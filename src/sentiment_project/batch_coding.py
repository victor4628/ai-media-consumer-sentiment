"""Small JSON batches with exact ID pairing, raw responses and cumulative budget."""
import json
import os
from concurrent.futures import ThreadPoolExecutor

from .ai_validation import call_deepseek, normalize_response_label, usage_cost_upper_estimate, validate_items
from .common import ROOT, digest, load_local_env, now_utc, read_json, write_json, write_jsonl


def core_cost(root=ROOT):
    folder = root / "labels/runs/core_v1/cache"
    return sum(read_json(p).get("cost_upper_usd", 0) for p in folder.glob("*.json")) if folder.exists() else 0.0


def decode_batch(response, items, allow_invalid=False):
    choice = response["choices"][0]
    if choice.get("finish_reason") != "stop":
        raise ValueError("Truncated batch")
    body = json.loads(choice["message"]["content"])
    labels = body.get("labels")
    if not isinstance(labels, list):
        raise ValueError("Batch response has no labels array")
    ids = [label.get("id") for label in labels]
    expected = {item["id"] for item in items}
    if len(ids) != len(set(ids)) or set(ids) != expected:
        raise ValueError("Batch ID sets differ; responses must not disappear")
    mapping = {item["id"]: item for item in items}
    result = []
    for label in labels:
        item = mapping[label["id"]]
        try:
            normalized, adjustments = normalize_response_label(label, item)
            status, error = "valid", None
        except (ValueError, TypeError, KeyError) as exc:
            if not allow_invalid:
                raise
            normalized, adjustments, status, error = None, [], "invalid_model_response", str(exc)
        result.append({"id": item["id"], "label": normalized, "input_sha256": digest(item), "format_adjustments": adjustments,
                       "label_status": status, "validation_error": error,
                       "source": item.get("source"), "platform": item.get("platform")})
    return result


def repair_batch(saved, batch, payload, cache, error, cfg, key, limit, root, fetch):
    path = cache.with_name(cache.stem + "_repair.json")
    model = payload["model"]
    repair_payload = {**payload, "messages": payload["messages"] + [
        {"role": "assistant", "content": saved["response"]["choices"][0]["message"]["content"]},
        {"role": "user", "content": "Validation failed: " + error + ". Return complete corrected JSON with labels array and every original ID. Use exactly one short verbatim quote per item, copied with original case and punctuation, even for irrelevant text. No paraphrases or ellipses. Keep all required fields."}]}
    reserve = ((len(json.dumps(repair_payload, ensure_ascii=False).encode("utf-8")) + 1024) * cfg["input_usd_per_million"][model] + 6000 * cfg["output_usd_per_million"][model]) / 1e6
    if path.exists():
        repaired = read_json(path)
        if repaired.get("state") not in ["received", "complete"]:
            raise RuntimeError("Uncertain paid repair; inspect cache")
    else:
        if core_cost(root) + reserve > limit:
            raise ValueError("Budget reached before one permitted batch repair")
        write_json(path, {"state": "pending", "kind": "schema_repair", "reserve_usd": reserve})
        response = fetch(repair_payload, key, cfg["base_url"])
        repaired = {"state": "received", "kind": "schema_repair", "role": saved["role"], "validation_error": error,
                    "response": response, "created_at": now_utc(), "prompt_sha256": digest(repair_payload),
                    "model_requested": model, "model_returned": response.get("model"),
                    "cost_upper_usd": usage_cost_upper_estimate(response, cfg, model, reserve)}
        write_json(path, repaired)
    # After the single repair, retain every ID and explicitly abstain on invalid items.
    labels = decode_batch(repaired["response"], batch, allow_invalid=True)
    repaired.update(state="complete", labels=labels)
    write_json(path, repaired)
    return [{**r, "format_adjustments": r["format_adjustments"] + ["one_batch_schema_repair_call"]} for r in labels], str(path)


def code_batches(items, role="A", budget=1.5, root=ROOT, fetch=call_deepseek, batch_size=6):
    validate_items(items)
    cfg = read_json(root / "configs/deepseek.json")
    study = read_json(root / "configs/core_study.json")
    prompt = (root / "prompts/economic_coding_v2.txt").read_text(encoding="utf-8")
    frozen = root / "labels/runs/core_v1/prompt_frozen.json"
    freeze_record = {"prompt_sha256": digest(prompt), "config_sha256": digest(cfg), "study_config_sha256": digest(study)}
    if frozen.exists() and read_json(frozen) != freeze_record:
        raise ValueError("Core prompt or configuration changed after freeze")
    write_json(frozen, freeze_record)
    load_local_env()
    key = os.getenv("DEEPSEEK_API_KEY")
    if not key:
        raise ValueError("DeepSeek key missing")
    model = cfg["roles"][role]
    suffix = {"A": "Apply the codebook directly.", "B": "Independently verify ambiguity and each evidence excerpt.", "C": "Independently review each field without another coder's answer."}[role]
    system = prompt + "\n" + suffix + "\nBATCH MODE: input is a JSON object with items. Return one JSON object {\"labels\":[label_for_each_item]}. Include every ID exactly once. Apply the complete schema independently to every item. Keep rationale under 180 characters and use one short literal evidence quote per item."
    results, jobs = [], []
    for start in range(0, len(items), batch_size):
        batch = items[start:start + batch_size]
        content = [{"id": i["id"], "text": i["text"], "published_at": i["published_at"], "official_evidence": i.get("official_evidence", [])} for i in batch]
        payload = {"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": json.dumps({"items": content}, ensure_ascii=False)}],
                   "response_format": {"type": "json_object"}, "thinking": {"type": "disabled"}, "temperature": 0, "max_tokens": 6000, "stream": False}
        cache = root / "labels/runs/core_v1/cache" / (digest({"role": role, "payload": payload}) + ".json")
        reserve = ((len(json.dumps(payload, ensure_ascii=False).encode("utf-8")) + 1024) * cfg["input_usd_per_million"][model] + 6000 * cfg["output_usd_per_million"][model]) / 1e6
        jobs.append((batch, payload, cache, reserve))
    # Two independent batches at a time; reserve both against one shared cumulative ledger.
    for start in range(0, len(jobs), 2):
        group = jobs[start:start + 2]
        new = [job for job in group if not job[2].exists()]
        for job in group:
            if job[2].exists() and read_json(job[2]).get("state") not in ["received", "complete", "schema_invalid"]:
                raise RuntimeError("Pending paid batch needs inspection before retry")
        if core_cost(root) + sum(job[3] for job in new) > min(budget, study["deepseek_new_budget_usd"]):
            raise ValueError("Cumulative core DeepSeek budget reached")
        with ThreadPoolExecutor(max_workers=2) as pool:
            pending = []
            for batch, payload, cache, reserve in new:
                write_json(cache, {"state": "pending", "role": role, "reserve_usd": reserve, "input_sha256": digest(batch)})
                pending.append((batch, payload, cache, reserve, pool.submit(fetch, payload, key, cfg["base_url"])))
            for batch, payload, cache, reserve, future in pending:
                response = future.result()
                saved = {"state": "received", "role": role, "model_requested": model, "model_returned": response.get("model"), "created_at": now_utc(),
                         "response": response, "input_sha256": digest(batch), "prompt_sha256": digest(system), "cost_upper_usd": usage_cost_upper_estimate(response, cfg, model, reserve)}
                write_json(cache, saved)
        for batch, payload, cache, reserve in group:
            saved = read_json(cache)
            try:
                if saved.get("state") == "complete":
                    labels = saved["labels"]
                else:
                    labels = decode_batch(saved["response"], batch)
                saved.update(state="complete", labels=labels)
                write_json(cache, saved)
            except (ValueError, TypeError, KeyError) as exc:
                saved.update(state="schema_invalid", validation_error=str(exc))
                write_json(cache, saved)
                labels, repair_path = repair_batch(saved, batch, payload, cache, str(exc), cfg, key, min(budget, study["deepseek_new_budget_usd"]), root, fetch)
                saved.update(state="complete", labels=labels, repair_cache=repair_path)
                write_json(cache, saved)
            results.extend({**r, "role": role, "model": saved["model_returned"]} for r in labels)
        if len(results) % 60 == 0 or start + 2 >= len(jobs):
            print(json.dumps({"role": role, "completed_items": len(results), "total": len(items), "core_cost_upper_usd": core_cost(root)}), flush=True)
    target = root / "labels/runs/core_v1" / (digest(items)[:12] + "_" + role + ".jsonl")
    write_jsonl(target, results)
    return {"items": len(results), "output": str(target), "core_cost_upper_usd": core_cost(root)}

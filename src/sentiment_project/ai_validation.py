from __future__ import annotations

import json
import html
import re
import math
import os
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .common import ROOT, digest, load_local_env, now_utc, read_json, read_jsonl, write_json, write_jsonl

ENUMS = {
    "tone": ["negative", "neutral", "positive", "mixed", "uncertain"],
    "language_style": ["factual", "emotional", "mixed", "uncertain"],
    "price_frame": ["levels", "changes", "both", "neither", "uncertain"],
    "scope_frame": ["household", "national", "both", "neither", "uncertain"],
    "time_frame": ["current", "future", "both", "neither", "uncertain"],
    "factual_calibration": ["matches", "conflicts", "not_checkable", "no_numeric_claim"],
    "political_attribution": ["credit", "blame", "both", "none", "uncertain"],
    "us_relevance": ["yes", "no", "uncertain"],
}
TOPICS = {"prices", "employment", "wages", "growth", "housing", "household_finances", "other"}


def usage_cost_upper_estimate(response, cfg, model, fallback):
    """Price reported tokens at peak cache-miss rates; discounts only lower cost."""
    usage = response.get("usage", {})
    prompt, completion = usage.get("prompt_tokens"), usage.get("completion_tokens")
    if not isinstance(prompt, int) or not isinstance(completion, int) or prompt < 0 or completion < 0:
        return fallback
    return (prompt * cfg["input_usd_per_million"][model] + completion * cfg["output_usd_per_million"][model]) / 1_000_000


def validate_label(label, item):
    if not isinstance(label, dict) or label.get("id") != item["id"]:
        raise ValueError("Label ID does not match input")
    for name, choices in ENUMS.items():
        if label.get(name) not in choices:
            raise ValueError(f"Invalid label: {name}")
    topics = label.get("topics")
    if not isinstance(topics, list) or any(not isinstance(t, str) or t not in TOPICS for t in topics) or len(topics) != len(set(topics)):
        raise ValueError("Invalid topics")
    evidence = label.get("evidence")
    if not isinstance(evidence, list) or not 1 <= len(evidence) <= 3:
        raise ValueError("Missing/excessive evidence excerpts")
    if any(not isinstance(s, str) or not s or len(s) > 160 or html.unescape(s) not in html.unescape(item["text"]) for s in evidence):
        raise ValueError("Evidence is not a bounded literal substring of the input")
    if not isinstance(label.get("rationale"), str) or len(label["rationale"]) > 400:
        raise ValueError("Invalid rationale")
    if label["factual_calibration"] in ["matches", "conflicts"] and not item.get("official_evidence"):
        raise ValueError("Factual verdict lacks official evidence")
    return label


def normalize_response_label(label, item):
    """Bound display-only text without changing any categorical judgments.

    Full unmodified provider content remains in the response cache. Never repair
    an invented quote: only shorten excerpts already present after HTML decoding.
    """
    label = dict(label)
    changes = []
    if isinstance(label.get("rationale"), str) and len(label["rationale"]) > 400:
        label["rationale"] = label["rationale"][:399] + "…"
        changes.append("rationale_display_truncated")
    excerpts = label.get("evidence")
    if isinstance(excerpts, list):
        bounded = []
        for excerpt in excerpts:
            if isinstance(excerpt, str) and html.unescape(excerpt) not in html.unescape(item["text"]):
                # Restore letter case from one unique source span; no paraphrase matching.
                matches = list(re.finditer(re.escape(html.unescape(excerpt)), html.unescape(item["text"]), re.IGNORECASE))
                if len(matches) == 1:
                    excerpt = matches[0].group(0)
                    changes.append("literal_excerpt_case_restored_from_source")
            if isinstance(excerpt, str) and len(excerpt) > 160 and html.unescape(excerpt) in html.unescape(item["text"]):
                bounded.append(html.unescape(excerpt)[:160])
                changes.append("literal_excerpt_display_truncated")
            else:
                bounded.append(excerpt)
        label["evidence"] = bounded
    return validate_label(label, item), changes


def validate_items(items):
    ids = set()
    for item in items:
        if not isinstance(item.get("id"), str) or not item["id"] or item["id"] in ids:
            raise ValueError("Missing/duplicate corpus ID")
        ids.add(item["id"])
        if not isinstance(item.get("text"), str) or not item["text"].strip():
            raise ValueError("Empty corpus text")
        pub = datetime.fromisoformat(item["published_at"].replace("Z", "+00:00"))
        if pub.tzinfo is None:
            raise ValueError("published_at requires a timezone")
        for fact in item.get("official_evidence", []):
            for field in ["source_url", "release_date", "vintage_date", "measure", "period", "unit", "value"]:
                if field not in fact:
                    raise ValueError(f"Official evidence missing {field}")
            if not str(fact["source_url"]).startswith("https://"):
                raise ValueError("Official evidence needs an HTTPS citation")
            for field in ["release_date", "vintage_date"]:
                # Date-only evidence must predate publication day to avoid intraday leakage.
                if datetime.fromisoformat(fact[field]).date() >= pub.date():
                    raise ValueError("Evidence is not demonstrably available before publication")
    return items


def call_deepseek(payload, key, base_url):
    req = Request(base_url + "/chat/completions", data=json.dumps(payload).encode("utf-8"),
                  headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=55) as r:
            return json.loads(r.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"DeepSeek HTTP {exc.code}; response body withheld; no automatic paid retry") from None
    except (URLError, TimeoutError):
        raise RuntimeError("DeepSeek network error; billing may be uncertain; inspect pending cache before retry") from None


def decode_or_repair(saved, item, payload, role, cfg, key, remaining, root, fetch):
    """At most one schema repair, cached separately; never retry a network failure."""
    choice = saved["response"]["choices"][0]
    if choice.get("finish_reason") != "stop":
        raise ValueError("Model response incomplete; saved and excluded from labels")
    try:
        label, changes = normalize_response_label(json.loads(choice["message"]["content"]), item)
        return label, changes, 0.0, 0.0, None
    except (ValueError, TypeError) as exc:
        error = str(exc)
    repair_payload = {**payload, "messages": payload["messages"] + [
        {"role": "assistant", "content": choice["message"]["content"]},
        {"role": "user", "content": "Your JSON failed validation: " + error + ". Return the complete corrected JSON. Include 1-3 literal excerpts even if the text is not about economics. Do not invent evidence. No other coder's answer is available."}]}
    model = payload["model"]
    reserve = ((len(json.dumps(repair_payload, ensure_ascii=False).encode("utf-8")) + 1024) * cfg["input_usd_per_million"][model] + cfg["max_tokens"] * cfg["output_usd_per_million"][model]) / 1_000_000
    path = root / "labels/runs/cache" / (digest({"repair_payload": repair_payload, "role": role}) + ".json")
    cost, reserved = 0.0, 0.0
    if path.exists():
        repair = read_json(path)
        if repair.get("state") not in ["received", "complete"]:
            raise RuntimeError("Pending schema repair needs inspection before paid retry")
    else:
        if reserve > remaining:
            raise ValueError("Budget reserve exceeded before schema repair")
        write_json(path, {"state": "pending", "role": role, "kind": "schema_repair", "reserved_usd": reserve})
        response = fetch(repair_payload, key, cfg["base_url"])
        cost, reserved = usage_cost_upper_estimate(response, cfg, model, reserve), reserve
        repair = {"state": "received", "kind": "schema_repair", "role": role, "model_requested": model,
                  "model_returned": response.get("model"), "created_at": now_utc(), "input_sha256": digest(item),
                  "prompt_sha256": digest(repair_payload), "estimated_cost_upper_usd": cost,
                  "estimated_reserved_usd": reserve, "validation_error": error, "response": response}
        write_json(path, repair)
    response_choice = repair["response"]["choices"][0]
    if response_choice.get("finish_reason") != "stop":
        raise ValueError("Schema repair response incomplete")
    label, changes = normalize_response_label(json.loads(response_choice["message"]["content"]), item)
    repair.update(state="complete", label=label, format_adjustments=changes)
    write_json(path, repair)
    return label, changes + ["one_schema_repair_call"], cost, reserved, str(path)


def classify(items, role, live=False, max_cost_usd=None, root=ROOT, fetch=call_deepseek, prompt_version="v1"):
    validate_items(items)
    cfg = read_json(root / "configs/deepseek.json")
    model = cfg["roles"][role]
    if prompt_version not in ["v1", "v2"]:
        raise ValueError("Unknown prompt version")
    system = (root / f"prompts/economic_coding_{prompt_version}.txt").read_text(encoding="utf-8")
    # Independent reviewer prompt; no A labels or explanations are supplied to B/C.
    suffix = {"A": "Apply the coding scheme directly.",
              "B": "Independently check each dimension, especially ambiguity and absent evidence.",
              "C": "Make an independent adjudication; retain uncertainty where the evidence is insufficient."}[role]
    tasks, total_reserve = [], 0.0
    for item in items:
        if len(item["text"]) > cfg["max_text_chars"]:
            raise ValueError("Text exceeds configured limit; do not silently truncate")
        content = {k: item[k] for k in ["id", "text", "published_at"]}
        content["official_evidence"] = item.get("official_evidence", [])
        payload = {"model": model, "messages": [{"role": "system", "content": system + "\n" + suffix},
                    {"role": "user", "content": json.dumps(content, ensure_ascii=False)}],
                   "response_format": {"type": "json_object"}, "thinking": {"type": cfg["thinking"]},
                   "temperature": cfg["temperature"], "max_tokens": cfg["max_tokens"], "stream": False}
        # UTF-8 bytes + overhead is deliberately conservative; provider tokenization/prices may change.
        input_bound = len(json.dumps(payload, ensure_ascii=False).encode("utf-8")) + 1024
        reserve = (input_bound * cfg["input_usd_per_million"][model] + cfg["max_tokens"] * cfg["output_usd_per_million"][model]) / 1_000_000
        tasks.append((item, payload, reserve))
        total_reserve += reserve
    if not live:
        return {"mode": "dry_run", "role": role, "model": model, "items": len(items),
                "conservative_estimated_usd": total_reserve, "network_calls": 0, "validation_scope": cfg["validation_scope"]}
    if max_cost_usd is None or not math.isfinite(max_cost_usd) or max_cost_usd <= 0:
        raise ValueError("Live labeling requires --max-cost-usd")
    load_local_env()
    key = os.getenv(cfg["api_key_env"])
    if not key:
        raise ValueError("DEEPSEEK_API_KEY is not configured")
    results, spent, reserved_sum = [], 0.0, 0.0
    for item, payload, reserve in tasks:
        cache = root / "labels/runs/cache" / (digest({"payload": payload, "role": role}) + ".json")
        if cache.exists():
            saved = read_json(cache)
            if saved.get("state") == "received":
                saved["label"], saved["format_adjustments"], cost, reserved, repair_path = decode_or_repair(saved, item, payload, role, cfg, key, max_cost_usd - spent, root, fetch)
                spent += cost
                reserved_sum += reserved
                saved["repair_cache"] = repair_path
                saved["state"] = "complete"
                saved["local_revalidated_at"] = now_utc()
                write_json(cache, saved)
            if saved.get("state") != "complete":
                raise RuntimeError("Pending/invalid model call needs inspection before paid retry")
        else:
            if spent + reserve > max_cost_usd:
                raise ValueError("Budget reserve exceeded; completed responses are cached for resume")
            write_json(cache, {"state": "pending", "role": role, "input_sha256": digest(item), "reserved_usd": reserve})
            response = fetch(payload, key, cfg["base_url"])
            saved = {"state": "received", "role": role, "model_requested": model,
                     "model_returned": response.get("model"), "created_at": now_utc(),
                     "input_sha256": digest(item), "prompt_sha256": digest(system + suffix),
                     "estimated_reserved_usd": reserve, "response": response}
            saved["estimated_cost_upper_usd"] = usage_cost_upper_estimate(response, cfg, model, reserve)
            write_json(cache, saved)
            spent += saved["estimated_cost_upper_usd"]
            reserved_sum += reserve
            label, saved["format_adjustments"], cost, reserved, repair_path = decode_or_repair(saved, item, payload, role, cfg, key, max_cost_usd - spent, root, fetch)
            spent += cost
            reserved_sum += reserved
            saved["repair_cache"] = repair_path
            saved["label"], saved["state"] = label, "complete"
            write_json(cache, saved)
        validate_label(saved["label"], item)
        results.append({"id": item["id"], "label": saved["label"], "role": role,
                        "model": saved["model_returned"], "input_sha256": digest(item),
                        "cached_call_input_sha256": saved["input_sha256"],
                        "format_adjustments": saved.get("format_adjustments", []),
                        "source": item.get("source", "unknown"), "platform": item.get("platform", "unknown")})
    # Input content fingerprint avoids overwriting outputs for a different corpus.
    run_id = digest(items)[:12] if prompt_version == "v1" else digest({"items": items, "prompt": system})[:12]
    target = root / "labels/runs" / f"{run_id}_{role}.jsonl"
    write_jsonl(target, results)
    return {"items": len(results), "prompt_version": prompt_version, "output": str(target), "estimated_new_reserved_usd": reserved_sum,
            "estimated_new_cost_upper_usd": spent,
            "validation_scope": cfg["validation_scope"]}


def categorical_agreement(left, right):
    if len(left) != len(right) or not left:
        raise ValueError("Agreement needs equal, nonempty paired samples")
    n = len(left)
    observed = sum(a == b for a, b in zip(left, right)) / n
    a, b = Counter(left), Counter(right)
    expected = sum(a[k] * b[k] for k in set(a) | set(b)) / (n * n)
    kappa = (observed - expected) / (1 - expected) if expected < 1 else None
    return {"n": n, "agreement": observed, "kappa": kappa,
            "cross_table": [{"A": x, "B": y, "count": v} for (x, y), v in sorted(Counter(zip(left, right)).items())]}


def compare_labels(left, right):
    a, b = {r["id"]: r for r in left}, {r["id"]: r for r in right}
    if len(a) != len(left) or len(b) != len(right):
        raise ValueError("Duplicate label IDs")
    if not a or a.keys() != b.keys():
        raise ValueError("Paired ID sets differ; missing responses must not silently disappear")
    ids = sorted(a)
    for i in ids:
        if a[i]["input_sha256"] != b[i]["input_sha256"]:
            raise ValueError("Labels refer to different source content")
    dims = dict(ENUMS)
    report = {"scope": "AI agreement, not truth accuracy", "paired_items": len(ids), "dimensions": {}, "disagreements": []}
    for name in dims:
        report["dimensions"][name] = categorical_agreement([a[i]["label"][name] for i in ids], [b[i]["label"][name] for i in ids])
    report["dimensions"]["topics_exact_set"] = categorical_agreement(["|".join(sorted(a[i]["label"]["topics"])) for i in ids], ["|".join(sorted(b[i]["label"]["topics"])) for i in ids])
    for i in ids:
        diff = [k for k in dims if a[i]["label"][k] != b[i]["label"][k]]
        if set(a[i]["label"]["topics"]) != set(b[i]["label"]["topics"]):
            diff.append("topics")
        if diff:
            report["disagreements"].append({"id": i, "dimensions": diff})
    report["by_source"] = {}
    for source in sorted({a[i].get("source", "unknown") for i in ids}):
        group = [i for i in ids if a[i].get("source", "unknown") == source]
        report["by_source"][source] = categorical_agreement([a[i]["label"]["tone"] for i in group], [b[i]["label"]["tone"] for i in group])
    return report

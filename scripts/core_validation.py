"""Audit coverage and coder agreement, explicitly retaining failed-response counts."""
import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sentiment_project.ai_validation import compare_labels, ENUMS
from sentiment_project.common import digest, read_json, read_jsonl, write_json, write_jsonl


def compare_group(items, a, b):
    ids = {i["id"] for i in items}
    if not ids.issubset(a) or not ids.issubset(b):
        raise ValueError("Missing attempted audit IDs")
    paired = [i for i in items if a[i["id"]]["label"] is not None and b[i["id"]]["label"] is not None]
    result = compare_labels([a[i["id"]] for i in paired], [b[i["id"]] for i in paired]) if paired else None
    return {"attempted": len(items), "valid_A": sum(a[i]["label"] is not None for i in ids), "valid_B": sum(b[i]["label"] is not None for i in ids), "valid_pairs": len(paired), "agreement": result}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-review", action="store_true")
    args = parser.parse_args()
    folder = ROOT / "data/private/core_v1"
    corpus = read_jsonl(folder / "corpus.jsonl")
    attempted = read_jsonl(folder / "audit_all_300.jsonl")
    a = {i["id"]: i for i in read_jsonl(ROOT / f"labels/runs/core_v1/{digest(corpus)[:12]}_A.jsonl")}
    b = {i["id"]: i for i in read_jsonl(ROOT / f"labels/runs/core_v1/{digest(attempted)[:12]}_B.jsonl")}
    for i in attempted:
        if a[i["id"]]["input_sha256"] != digest(i) or b[i["id"]]["input_sha256"] != digest(i):
            raise ValueError("Audit content identity mismatch")
    report = {"scope": "AI-only, shared DeepSeek family; agreement is not accuracy", "prompt_sha256": read_json(folder / "corpus_manifest.json")["prompt_sha256"],
              "all_300": compare_group(attempted, a, b), "held_out_200": compare_group(read_jsonl(folder / "audit_200.jsonl"), a, b),
              "development_100": compare_group(read_jsonl(folder / "development_100.jsonl"), a, b),
              "by_platform": {p: compare_group([i for i in attempted if i["platform"] == p], a, b) for p in ["news", "twitter"]}}
    write_json(ROOT / "reports/core_ai_validation.json", report)
    if args.prepare_review:
        disputed, agreeing = [], []
        for item in attempted:
            av, bv = a[item["id"]]["label"], b[item["id"]]["label"]
            diff = av is None or bv is None or any(av[k] != bv[k] for k in ENUMS) or set(av["topics"]) != set(bv["topics"])
            (disputed if diff else agreeing).append(item)
        rng = random.Random(20261017)
        selected = disputed + rng.sample(agreeing, min(len(agreeing), max(1, (len(agreeing) + 9) // 10)))
        selected.sort(key=lambda i: i["id"])
        target = folder / "review_C.jsonl"
        if target.exists() and digest(read_jsonl(target)) != digest(selected):
            raise ValueError("Frozen review queue changed")
        write_jsonl(target, selected)
        write_json(folder / "review_C.manifest.json", {"items": len(selected), "disputed": len(disputed), "agreement_checks": len(selected) - len(disputed), "sha256": digest(selected)})
    c_path = folder / "review_C.jsonl"
    if c_path.exists():
        c_items = read_jsonl(c_path)
        labels_path = ROOT / f"labels/runs/core_v1/{digest(c_items)[:12]}_C.jsonl"
        if labels_path.exists():
            labels = read_jsonl(labels_path)
            c = {r["id"]: r for r in labels}
            adjudicated, resolved, unresolved, challenges = [], 0, 0, 0
            for item in attempted:
                all_labels = {role: row["label"] for role, row in [("A", a[item["id"]]), ("B", b[item["id"]]), ("C", c.get(item["id"], {"label": None}))]}
                final, missing = {}, []
                for field in [*ENUMS, "topics"]:
                    values = [label[field] if field != "topics" else tuple(sorted(label[field])) for label in all_labels.values() if label is not None]
                    votes = Counter(values)
                    value, count = votes.most_common(1)[0] if votes else (None, 0)
                    if count >= 2:
                        final[field] = list(value) if field == "topics" else value
                        resolved += 1
                    else:
                        final[field] = None
                        missing.append(field)
                        unresolved += 1
                    if all(all_labels[r] is not None for r in ["A", "B", "C"]):
                        av, bv, cv = [all_labels[r][field] for r in ["A", "B", "C"]]
                        if field == "topics":
                            av, bv, cv = set(av), set(bv), set(cv)
                        if av == bv != cv:
                            challenges += 1
                adjudicated.append({"id": item["id"], "input_sha256": digest(item), "consensus_dimensions": final, "unresolved_dimensions": missing,
                                    "evidence_by_role": {role: label["evidence"] for role, label in all_labels.items() if label is not None},
                                    "rule": "At least two matching valid votes; unresolved fields remain null; not a truth label"})
            write_jsonl(folder / "adjudicated_audit.jsonl", adjudicated)
            report["C_review"] = {"attempted": len(labels), "valid": sum(r["label"] is not None for r in labels), "consensus_dimensions": resolved,
                                  "unresolved_dimensions": unresolved, "C_challenges_to_AB_agreement": challenges,
                                  "scope": "Independent calls without A/B answers; same Pro family as B; two-vote audit consensus is not a gold standard or causal verification"}
            write_json(ROOT / "reports/core_ai_validation.json", report)
    print(json.dumps({"attempted": 300, "held_out_attempted": 200, "held_out_valid_pairs": report["held_out_200"]["valid_pairs"], "C_review": report.get("C_review"), "output": "reports/core_ai_validation.json"}, indent=2))


if __name__ == "__main__":
    main()

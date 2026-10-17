"""ID-blinding stability probe on 20 held-out texts; never a truth benchmark."""
import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sentiment_project.ai_validation import ENUMS, categorical_agreement
from sentiment_project.common import digest, read_json, read_jsonl, write_json, write_jsonl


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    folder = ROOT / "data/private/core_v1"
    target = folder / "perturb_id_blind.jsonl"
    mapping_path = folder / "perturb_id_blind.manifest.json"
    if args.prepare:
        rng = random.Random(20261018)
        audit = read_jsonl(folder / "audit_200.jsonl")
        selected = []
        for platform in ["news", "twitter"]:
            group = sorted([i for i in audit if i["platform"] == platform], key=lambda i: i["id"])
            selected.extend(rng.sample(group, 10))
        altered, mapping = [], []
        for item in selected:
            masked = {**item, "id": "masked:" + digest(item["id"])[:20]}
            altered.append(masked)
            mapping.append({"original_id": item["id"], "masked_id": masked["id"], "original_sha256": digest(item), "masked_sha256": digest(masked)})
        if target.exists() and digest(read_jsonl(target)) != digest(altered):
            raise ValueError("Frozen perturbation set changed")
        write_jsonl(target, altered)
        write_json(mapping_path, {"scope": "ID-blinding only; content/publication unchanged; no truth benchmark", "items": mapping})
        print(json.dumps({"items": len(altered), "output": str(target)}))
        return
    corpus = read_jsonl(folder / "corpus.jsonl")
    original = {i["id"]: i for i in read_jsonl(ROOT / f"labels/runs/core_v1/{digest(corpus)[:12]}_A.jsonl")}
    changed = read_jsonl(target)
    altered = {i["id"]: i for i in read_jsonl(ROOT / f"labels/runs/core_v1/{digest(changed)[:12]}_A.jsonl")}
    mapping = read_json(mapping_path)["items"]
    paired = [(original[m["original_id"]], altered[m["masked_id"]]) for m in mapping]
    valid = [(a, b) for a, b in paired if a["label"] is not None and b["label"] is not None]
    report = {"scope": "ID-blinding stability, not accuracy; 10 news and 10 tweets from held-out audit; batch context may also vary", "attempted": len(paired), "valid_pairs": len(valid), "dimensions": {k: categorical_agreement([a["label"][k] for a, _ in valid], [b["label"][k] for _, b in valid]) for k in ENUMS}}
    write_json(ROOT / "reports/core_perturbation.json", report)
    print(json.dumps({"attempted": len(paired), "valid_pairs": len(valid), "tone_stability": report["dimensions"]["tone"]["agreement"]}, indent=2))


if __name__ == "__main__":
    main()

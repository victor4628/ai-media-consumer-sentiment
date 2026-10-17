"""Freeze a small development pilot, explicitly separate from the formal audit."""
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sentiment_project.common import digest, read_json, read_jsonl, write_json, write_jsonl
from sentiment_project.corpus import group_id


def main():
    inputs = {name: read_jsonl(ROOT / f"data/private/{name}_pilot.jsonl") for name in ["news", "twitter"]}
    fingerprint = digest(inputs)
    output = ROOT / "data/private/validation_pilot_v1.jsonl"
    manifest = output.with_suffix(".manifest.json")
    if manifest.exists():
        saved = read_json(manifest)
        if saved["input_sha256"] != fingerprint or digest(read_jsonl(output)) != saved["sample_sha256"]:
            raise ValueError("Frozen pilot changed; create a new version explicitly")
        print(json.dumps(saved, indent=2))
        return
    rng = random.Random(20261016)
    buckets = defaultdict(list)
    for item in inputs["twitter"]:
        buckets[item["published_at"][:4]].append(item)
    selected = sorted(inputs["news"], key=lambda r: r["id"])
    groups = {group_id(i) for i in selected}
    for year, rows in sorted(buckets.items()):
        rows.sort(key=lambda r: r["id"])
        rng.shuffle(rows)
        n = 0
        for row in rows:
            group = group_id(row)
            if group not in groups:
                groups.add(group)
                selected.append(row)
                n += 1
            if n == 12:
                break
    rng.shuffle(selected)
    summary = {"scope": "development pilot only; not the frozen 300-item formal audit",
               "seed": 20261016, "items": len(selected), "input_sha256": fingerprint,
               "sample_sha256": digest(selected),
               "by_platform": dict(Counter(r["platform"] for r in selected)),
               "by_source": dict(Counter(r["source"] for r in selected)),
               "by_year": dict(Counter(r["published_at"][:4] for r in selected))}
    write_jsonl(output, selected)
    write_json(manifest, summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

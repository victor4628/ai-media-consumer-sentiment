"""Combine separately cached platform A runs, enforcing exact content identity."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sentiment_project.common import digest, read_jsonl, write_jsonl

corpus = read_jsonl(ROOT / "data/private/core_v1/corpus.jsonl")
labels = {}
for path in (ROOT / "labels/runs/core_v1").glob("*_A.jsonl"):
    for row in read_jsonl(path):
        if row["id"] in labels and labels[row["id"]]["label"] != row["label"]:
            raise ValueError("Conflicting A labels")
        labels[row["id"]] = row
result = []
for item in corpus:
    if item["id"] not in labels or labels[item["id"]]["input_sha256"] != digest(item):
        raise ValueError("Missing/mismatched A label: " + item["id"])
    result.append(labels[item["id"]])
target = ROOT / f"labels/runs/core_v1/{digest(corpus)[:12]}_A.jsonl"
write_jsonl(target, result)
print(json.dumps({"items": len(result), "output": str(target)}))

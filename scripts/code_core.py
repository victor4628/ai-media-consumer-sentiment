import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sentiment_project.batch_coding import code_batches
from sentiment_project.common import read_jsonl

parser = argparse.ArgumentParser()
parser.add_argument("--input", type=Path, required=True)
parser.add_argument("--role", choices=["A", "B", "C"], required=True)
parser.add_argument("--budget", type=float, default=1.5)
args = parser.parse_args()
print(json.dumps(code_batches(read_jsonl(args.input), args.role, args.budget), indent=2))

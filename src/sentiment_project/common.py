from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_local_env():
    """Read only known API settings; do not evaluate shell expressions."""
    path = ROOT / ".env.local"
    if not path.exists():
        return
    allowed = {"TWITTERAPI_IO_KEY", "DEEPSEEK_API_KEY", "FRED_API_KEY"}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if sep and key.strip() in allowed:
            value = value.strip().strip('"').strip("'")
            if value:
                os.environ.setdefault(key.strip(), value)


def now_utc():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def digest(value):
    if not isinstance(value, bytes):
        value = json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def read_jsonl(path):
    # JSON strings may contain U+2028/U+0085; splitlines() would corrupt those records.
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8-sig").split("\n") if line.strip()]


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n" for row in rows), encoding="utf-8")


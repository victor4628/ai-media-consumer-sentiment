"""Download bounded public FRED snapshots. These are NOT historical vintages."""
import csv
import hashlib
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SERIES = ["UNRATE", "PCEPI", "PCEPILFE", "A191RL1Q225SBEA", "UMCSENT", "DSPIC96"]


def main():
    config = json.loads((ROOT / "configs/project.json").read_text(encoding="utf-8"))
    stamp = datetime.now(timezone.utc).isoformat()
    out = ROOT / "data/raw/fred_snapshot"
    out.mkdir(parents=True, exist_ok=True)
    manifest = {"retrieved_at": stamp, "analysis_cutoff": config["as_of"], "type": "current_snapshot_not_realtime_vintages", "series": []}
    for sid in SERIES:
        url = "https://fred.stlouisfed.org/graph/fredgraph.csv?" + urlencode({"id": sid, "cosd": "2009-01-01", "coed": config["as_of"]})
        try:
            with urlopen(Request(url, headers={"User-Agent": "ConsumerSentimentResearch/0.1"}), timeout=30) as response:
                data = response.read(5_000_000)
            reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
            if sid not in (reader.fieldnames or []):
                raise ValueError("Response does not contain requested series column")
            rows = list(reader)
            if not rows:
                raise ValueError("Empty series")
            (out / f"{sid}.csv").write_bytes(data)
            manifest["series"].append({"id": sid, "status": "downloaded", "rows": len(rows), "url": url, "sha256": hashlib.sha256(data).hexdigest()})
            print(sid, len(rows), "downloaded", flush=True)
        except (HTTPError, URLError, ValueError, TimeoutError) as exc:
            manifest["series"].append({"id": sid, "status": "failed", "error_type": type(exc).__name__, "url": url})
            print(sid, type(exc).__name__, flush=True)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return 0 if all(r["status"] == "downloaded" for r in manifest["series"]) else 1


if __name__ == "__main__":
    sys.exit(main())

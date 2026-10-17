"""Bounded cached downloads of five public series at month-end forecast origins."""
import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sentiment_project.common import digest, now_utc, read_json, write_json
from sentiment_project.vintages import parse_snapshot

SERIES = ["UNRATE", "PCEPI", "GDPC1", "UMCSENT", "DSPIC96"]


def fetch(task):
    series, vintage = task
    path = ROOT / "data/raw/alfred_vintages" / vintage / (series + ".csv")
    meta = path.with_suffix(".meta.json")
    if path.exists() and meta.exists():
        data = path.read_bytes()
        saved = read_json(meta)
        if digest(data) != saved["sha256"]:
            raise ValueError("Cached ALFRED file hash changed")
        parse_snapshot(data, series, vintage)
        return {**saved, "cache_hit": True}
    url = "https://alfred.stlouisfed.org/graph/alfredgraph.csv?" + urlencode({"id": series, "vintage_date": vintage, "cosd": "2008-01-01", "coed": vintage})
    with urlopen(Request(url, headers={"User-Agent": "ConsumerSentimentResearch/0.1"}), timeout=35) as response:
        data = response.read(2_000_001)
    if len(data) > 2_000_000:
        raise ValueError("ALFRED response too large")
    values = parse_snapshot(data, series, vintage)
    record = {"series": series, "vintage": vintage, "source_url": url, "retrieved_at": now_utc(),
              "sha256": digest(data), "bytes": len(data), "observations": len(values), "latest_period": max(values)}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    write_json(meta, record)
    time.sleep(0.2)
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2010-01")
    parser.add_argument("--end", default="2026-08")
    parser.add_argument("--max-downloads", type=int, default=1010)
    parser.add_argument("--series", nargs="+", choices=SERIES)
    args = parser.parse_args()
    start, end = date.fromisoformat(args.start + "-01"), date.fromisoformat(args.end + "-01")
    if start > end or end > date(2026, 10, 1):
        raise ValueError("Invalid forecast period bounds")
    origins = []
    current = start
    while current <= end:
        origins.append((current - timedelta(days=1)).isoformat())
        current = date(current.year + (current.month == 12), current.month % 12 + 1, 1)
    origins.append("2026-10-16")  # Evaluation snapshot, never used as an earlier forecast input.
    tasks = [(sid, vintage) for vintage in origins for sid in (args.series or SERIES)]
    if len(tasks) > args.max_downloads:
        raise ValueError("Request cap would be exceeded")
    name = "manifest_" + "_".join(args.series) + ".json" if args.series else "manifest.json"
    output = ROOT / "data/raw/alfred_vintages" / name
    records, errors = [], []
    # Modest parallel downloads; each series/vintage has its own immutable cache.
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [(task, pool.submit(fetch, task)) for task in tasks]
        for task, future in futures:
            try:
                records.append(future.result())
            except Exception as exc:
                errors.append({"series": task[0], "vintage": task[1], "error": str(exc)})
            if (len(records) + len(errors)) % 25 == 0:
                print(json.dumps({"completed": len(records), "failed": len(errors), "total": len(tasks)}), flush=True)
                write_json(output, {"records": records, "errors": errors, "scope": "vintage snapshots; not exact release-date history"})
    write_json(output, {"records": records, "errors": errors, "scope": "vintage snapshots; not exact release-date history"})
    print(json.dumps({"completed": len(records), "failed": len(errors), "total": len(tasks)}))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

"""16 fixed GDELT archive slots; free, bounded and cached, not monthly sampling."""
import json
import sys
import zipfile
from collections import Counter
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sentiment_project.common import digest, now_utc, write_json, write_jsonl
from sentiment_project.news_archive import parse_gkg


def main():
    folder = ROOT / "data/raw/news_archive_probe"
    folder.mkdir(parents=True, exist_ok=True)
    rows, records, errors = {}, [], []
    for day in ["20200615", "20220615", "20240614", "20260615"]:
        for hour in ["04", "10", "16", "22"]:
            slot = day + hour + "0000"
            url = f"https://data.gdeltproject.org/gdeltv2/{slot}.gkg.csv.zip"
            path = folder / (slot + ".zip")
            existing = ROOT / "data/raw/history_probe" / ("gdelt_" + slot + ".zip")
            try:
                if not path.exists():
                    if existing.exists():
                        data = existing.read_bytes()
                    else:
                        with urlopen(Request(url, headers={"User-Agent": "ConsumerSentimentResearch/0.1"}), timeout=35) as response:
                            data = response.read(20_000_001)
                        if len(data) > 20_000_000:
                            raise ValueError("Archive exceeds 20 MB limit")
                    path.write_bytes(data)
                raw = path.read_bytes()
                with zipfile.ZipFile(path) as z:
                    entries = z.infolist()
                    if len(entries) != 1 or entries[0].file_size > 100_000_000:
                        raise ValueError("Unexpected ZIP shape/expanded size")
                    candidates, counts = parse_gkg(z.read(entries[0]), url, digest(raw), now_utc())
                for candidate in candidates:
                    rows.setdefault(candidate["id"], candidate)
                records.append({"url": url, "sha256": digest(raw), "bytes": len(raw), "counts": counts})
                print(json.dumps({"slot": slot, "candidates": len(candidates)}), flush=True)
            except Exception as exc:
                errors.append({"url": url, "error": str(exc)})
    candidates = list(rows.values())
    eligible = [r for r in candidates if r["publication_timestamp_status"] == "timestamp_candidate_valid"]
    write_jsonl(ROOT / "data/private/news_archive_candidates.jsonl", candidates)
    write_jsonl(ROOT / "data/private/news_archive_timestamp_eligible.jsonl", eligible)
    report = {"scope": "archive access probe; four dates, four slots each; not representative monthly data",
              "files": len(records), "errors": errors, "candidates": len(candidates), "timestamp_eligible": len(eligible),
              "by_outlet": dict(Counter(r["source"] for r in candidates)), "by_year": dict(Counter(r["discovered_at"][:4] for r in candidates)),
              "date_quality": dict(Counter(r["publication_timestamp_status"] for r in candidates)),
              "limitations": ["headlines only", "publication timestamps are extracted metadata", "same story syndication and outlet balance require review", "PAGE_TITLE unavailable before September 2019", "US outlet does not imply US subject matter"],
              "source_docs": ["https://blog.gdeltproject.org/gkg-2-0-now-includes-page-titles/", "https://blog.gdeltproject.org/new-gkg-2-0-article-metadata-fields/"], "records": records}
    write_json(ROOT / "reports/news_archive_probe.json", report)
    print(json.dumps({k: v for k, v in report.items() if k != "records"}, indent=2))


if __name__ == "__main__":
    main()

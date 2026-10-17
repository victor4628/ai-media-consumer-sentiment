"""Fixed monthly media sampling with private raw caches and bounded spending."""
import argparse
import calendar
import json
import os
import random
import sys
import time
import zipfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sentiment_project.common import digest, load_local_env, now_utc, read_json, write_json, write_jsonl
from sentiment_project.news_archive import parse_gkg
from sentiment_project.twitter import make_query, normalize_tweet, request_page


def schedule(cfg):
    rng = random.Random(cfg["seed"])
    start, end = [datetime.strptime(cfg[k], "%Y-%m").replace(tzinfo=timezone.utc) for k in ["media_start", "media_end"]]
    dates = []
    month = start
    while month <= end:
        days = sorted(rng.sample(range(2, calendar.monthrange(month.year, month.month)[1]), 2))
        # Four daytime UTC news slots on each of two presampled days; two Twitter 1-hour windows.
        for n, day in enumerate(days):
            for hour in [13, 16, 19, 22]:
                dates.append({"platform": "news", "month": month.strftime("%Y-%m"), "at": month.replace(day=day, hour=hour).isoformat()})
            hour = rng.choice([13, 16, 19, 22])
            dates.append({"platform": "twitter", "month": month.strftime("%Y-%m"), "at": month.replace(day=day, hour=hour).isoformat()})
        month = month.replace(year=month.year + (month.month == 12), month=month.month % 12 + 1)
    return dates


def news_slot(task):
    cfg, row = task
    dt = datetime.fromisoformat(row["at"])
    slot = dt.strftime("%Y%m%d%H%M%S")
    url = f"https://data.gdeltproject.org/gdeltv2/{slot}.gkg.csv.zip"
    folder = ROOT / "data/raw/core_v1/news"
    path = folder / (slot + ".zip")
    meta = path.with_suffix(".meta.json")
    if path.exists() and meta.exists():
        saved = read_json(meta)
        if digest(path.read_bytes()) != saved["sha256"]:
            raise ValueError("News cache hash mismatch")
        return saved, read_json(meta.with_suffix(".items.json"))
    with urlopen(Request(url, headers={"User-Agent": "ConsumerSentimentResearch/0.2"}), timeout=35) as response:
        raw = response.read(cfg["news_file_cap_bytes"] + 1)
    if len(raw) > cfg["news_file_cap_bytes"]:
        raise ValueError("News archive per-file cap exceeded")
    import io
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        entries = z.infolist()
        if len(entries) != 1 or entries[0].file_size > 100_000_000:
            raise ValueError("Unexpected ZIP contents/size")
        retrieved = now_utc()
        items, counts = parse_gkg(z.read(entries[0]), url, digest(raw), retrieved)
    record = {**row, "url": url, "sha256": digest(raw), "bytes": len(raw), "retrieved_at": retrieved, "counts": counts}
    folder.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    write_json(meta, record)
    write_json(meta.with_suffix(".items.json"), items)
    return record, items


def collect_news(cfg, rows):
    tasks = [r for r in rows if r["platform"] == "news"]
    # Worst-case bound before initiating downloads, independent of observed yield.
    if len(tasks) * cfg["news_file_cap_bytes"] > cfg["news_compressed_download_cap_bytes"] * 2:
        raise ValueError("News schedule exceeds maximum download plan")
    results, errors, corpus = [], [], {}
    downloaded = 0
    with ThreadPoolExecutor(max_workers=3) as pool:
        pending = {}
        iterator = iter(tasks)
        for _ in range(3):
            task = next(iterator, None)
            if task:
                pending[pool.submit(news_slot, (cfg, task))] = task
        while pending:
            future = next(as_completed(pending))
            task = pending.pop(future)
            try:
                record, items = future.result()
                results.append(record)
                downloaded += record["bytes"]
                for item in items:
                    old = corpus.get(item["id"])
                    if old is None or item["discovered_at"] < old["discovered_at"]:
                        corpus[item["id"]] = item
            except Exception as exc:
                errors.append({**task, "error": str(exc)})
            next_task = next(iterator, None)
            if next_task and downloaded + (len(pending) + 1) * cfg["news_file_cap_bytes"] <= cfg["news_compressed_download_cap_bytes"]:
                pending[pool.submit(news_slot, (cfg, next_task))] = next_task
            if (len(results) + len(errors)) % 25 == 0:
                print(json.dumps({"news_files": len(results), "errors": len(errors), "candidates": len(corpus), "MB": round(downloaded / 1e6)}), flush=True)
                write_json(ROOT / "data/raw/core_v1/news_manifest.json", {"records": results, "errors": errors})
    candidates = list(corpus.values())
    eligible = [r for r in candidates if r["publication_timestamp_status"] == "timestamp_candidate_valid" and cfg["media_start"] <= r["published_at"][:7] <= cfg["media_end"]]
    write_jsonl(ROOT / "data/private/core_v1/news_candidates.jsonl", candidates)
    write_jsonl(ROOT / "data/private/core_v1/news.jsonl", eligible)
    report = {"records": sorted(results, key=lambda r: r["at"]), "errors": errors, "candidates": len(candidates), "eligible": len(eligible), "bytes": downloaded,
              "by_month": dict(Counter(r["published_at"][:7] for r in eligible)), "by_level": dict(Counter(r["source_level"] for r in eligible)), "scope": cfg["sampling_scope"]}
    write_json(ROOT / "data/raw/core_v1/news_manifest.json", report)
    write_json(ROOT / "reports/core_news_coverage.json", {k: v for k, v in report.items() if k != "records"})
    print(json.dumps({k: v for k, v in report.items() if k not in ["records", "by_month"]}, indent=2))


def collect_twitter(cfg, rows):
    load_local_env()
    key = os.getenv("TWITTERAPI_IO_KEY")
    if not key:
        raise ValueError("Twitter key missing")
    tasks = [r for r in rows if r["platform"] == "twitter"]
    folder = ROOT / "data/raw/core_v1/twitter"
    folder.mkdir(parents=True, exist_ok=True)
    records, corpus, errors, spent = [], {}, [], 0.0
    for task in tasks:
        start = datetime.fromisoformat(task["at"])
        end = start + timedelta(hours=1)
        window = {"since": start.isoformat(), "until": end.isoformat()}
        params = {"query": make_query({"query": cfg["twitter_query"]}, window), "queryType": "Latest", "cursor": ""}
        path = folder / (digest(params) + ".json")
        if path.exists():
            saved = read_json(path)
            if saved["state"] != "complete":
                raise RuntimeError("Uncertain paid request; inspect cache, never auto-repeat")
        else:
            if spent + 0.015 > cfg["twitter_new_budget_usd"]:
                break
            write_json(path, {"state": "pending", "params": params, "task": task})
            body = request_page("https://api.twitterapi.io/twitter/tweet/advanced_search", params, key)
            if not isinstance(body.get("tweets"), list):
                write_json(path, {"state": "invalid_response", "params": params, "response": body})
                raise ValueError("Invalid Twitter response")
            saved = {"state": "complete", "params": params, "task": task, "response": body,
                     "retrieved_at": now_utc(), "estimated_usd": max(0.00015, len(body["tweets"]) * 0.00015)}
            write_json(path, saved)
            time.sleep(5.5)
        spent += saved["estimated_usd"]
        valid = 0
        for tweet in saved["response"]["tweets"]:
            try:
                item = normalize_tweet(tweet, window, saved["retrieved_at"])
                item["sample_scope"] = cfg["sampling_scope"]
                item["sampling_window"] = task["at"]
                corpus.setdefault(item["id"], item)
                valid += 1
            except (ValueError, TypeError) as exc:
                errors.append({"id": str(tweet.get("id")), "window": task["at"], "error": str(exc)})
        records.append({**task, "returned": len(saved["response"]["tweets"]), "valid": valid})
        if saved["response"]["tweets"] and not valid:
            raise ValueError("Whole Twitter page invalid; stop before more paid requests")
        if len(records) % 10 == 0:
            print(json.dumps({"twitter_windows": len(records), "valid_unique": len(corpus), "estimated_usd": spent}), flush=True)
            write_jsonl(ROOT / "data/private/core_v1/twitter.jsonl", list(corpus.values()))
    write_jsonl(ROOT / "data/private/core_v1/twitter.jsonl", list(corpus.values()))
    summary = {"windows": len(records), "posts": len(corpus), "estimated_usd": spent, "errors": errors,
               "by_month": dict(Counter(r["published_at"][:7] for r in corpus.values())), "records": records, "scope": cfg["sampling_scope"]}
    write_json(ROOT / "reports/core_twitter_coverage.json", summary)
    print(json.dumps({k: v for k, v in summary.items() if k not in ["records", "by_month", "errors"]}, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=["news", "twitter"], required=True)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    cfg = read_json(ROOT / "configs/core_study.json")
    rows = schedule(cfg)
    target = ROOT / "data/private/core_v1/sampling_manifest.json"
    frozen = {"config_sha256": digest(cfg), "schedule_sha256": digest(rows), "schedule": rows}
    if target.exists() and read_json(target) != frozen:
        raise ValueError("Frozen sampling design changed")
    write_json(target, frozen)
    if not args.live:
        print(json.dumps({"schedule": dict(Counter(r["platform"] for r in rows)), "config": cfg}, indent=2))
        return
    (collect_news if args.platform == "news" else collect_twitter)(cfg, rows)


if __name__ == "__main__":
    main()

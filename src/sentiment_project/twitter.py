from __future__ import annotations

import os
import math
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .common import ROOT, digest, load_local_env, now_utc, read_json, write_json, write_jsonl


def make_query(config, window):
    start, end = datetime.fromisoformat(window["since"]), datetime.fromisoformat(window["until"])
    if start >= end:
        raise ValueError("until must be strictly later than since")
    start_epoch = int(start.replace(tzinfo=timezone.utc).timestamp())
    end_epoch = int(end.replace(tzinfo=timezone.utc).timestamp())
    return f"{config['query']} since_time:{start_epoch} until_time:{end_epoch}"


def request_page(endpoint, params, api_key):
    import json
    req = Request(endpoint + "?" + urlencode(params), headers={"X-API-Key": api_key, "User-Agent": "ConsumerSentimentResearch/0.1"})
    try:
        with urlopen(req, timeout=45) as r:
            return json.loads(r.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"Twitter HTTP {exc.code}; no automatic paid retry") from None
    except (URLError, TimeoutError):
        raise RuntimeError("Twitter network error; request may have been charged; inspect pending cache before retry") from None


def normalize_tweet(tweet, window, retrieved_at):
    tid, text = str(tweet.get("id", "")), tweet.get("text", "")
    created = tweet.get("createdAt", "")
    if not tid or not isinstance(text, str) or not text or not created:
        raise ValueError("Missing tweet id/text/createdAt")
    try:
        date = datetime.fromisoformat(created.replace("Z", "+00:00"))
    except ValueError:
        date = parsedate_to_datetime(created)
    if date.tzinfo is None:
        raise ValueError("Tweet timestamp has no timezone")
    date = date.astimezone(timezone.utc)
    start = datetime.fromisoformat(window["since"]).replace(tzinfo=timezone.utc)
    end = datetime.fromisoformat(window["until"]).replace(tzinfo=timezone.utc)
    if not start <= date < end:
        raise ValueError("Tweet outside requested UTC window")
    return {"id": "twitter:" + tid, "platform": "twitter", "source": "twitter_search", "text": text,
            "published_at": date.isoformat(), "retrieved_at": retrieved_at,
            "content_hash": digest(text), "story_group": digest(text.lower().split()),
            "url": f"https://x.com/i/web/status/{tid}", "us_relevance": "unknown",
            "is_reply": tweet.get("isReply"), "is_retweet": tweet.get("isRetweet"),
            "engagement_snapshot": {k: tweet.get(k) for k in ["likeCount", "retweetCount", "replyCount", "viewCount"]},
            "sample_scope": "pilot_not_monthly_representative"}


def collect_pilot(live=False, max_cost_usd=None, root=ROOT, fetch=request_page):
    cfg = read_json(root / "configs/twitter_pilot.json")
    queries = [make_query(cfg, w) for w in cfg["windows"]]
    if not live:
        return {"mode": "dry_run", "queries": queries, "request_cap": cfg["max_requests"],
                "estimated_usd_at_20_results_per_page": cfg["max_requests"] * 20 * cfg["usd_per_tweet"],
                "network_calls": 0, "scope": cfg["scope"]}
    if max_cost_usd is None or not math.isfinite(max_cost_usd) or max_cost_usd <= 0:
        raise ValueError("Live collection requires a positive --max-cost-usd")
    load_local_env()
    key = os.getenv("TWITTERAPI_IO_KEY")
    if not key:
        raise ValueError("TWITTERAPI_IO_KEY is not configured")
    cache = root / "data/raw/twitter_pilot" / digest(cfg)[:12]
    cache.mkdir(parents=True, exist_ok=True)
    corpus, invalid, windows = {}, [], []
    spent, calls = 0.0, 0
    for window, query in zip(cfg["windows"], queries):
        cursor, seen = "", set()
        status = "page_cap"
        for page in range(cfg["max_pages_per_window"]):
            params = {"query": query, "queryType": cfg["query_type"], "cursor": cursor}
            path = cache / (digest(params) + ".json")
            if path.exists():
                saved = read_json(path)
                if saved.get("state") != "complete":
                    raise RuntimeError("Previous request has uncertain billing; resolve the pending cache entry before resume")
            else:
                # Reserve 100 returned posts, well above the documented typical ~20/page.
                # This is a conservative local stopping rule, not a provider hard billing cap.
                reserve = max(cfg["min_usd_per_call"], 100 * cfg["usd_per_tweet"])
                if spent + reserve > max_cost_usd or calls >= cfg["max_requests"]:
                    status = "budget_or_request_cap"
                    break
                write_json(path, {"state": "pending", "params": params, "reserved_usd": reserve})
                body = fetch(cfg["endpoint"], params, key)
                tweets = body.get("tweets")
                if not isinstance(tweets, list) or not isinstance(body.get("has_next_page"), bool):
                    write_json(path, {"state": "invalid_response", "params": params, "response": body})
                    raise ValueError("Unexpected Twitter response schema; saved, no automatic retry")
                saved = {"state": "complete", "params": params, "retrieved_at": now_utc(), "response": body,
                         "estimated_usd": max(cfg["min_usd_per_call"], len(tweets) * cfg["usd_per_tweet"])}
                write_json(path, saved)
                calls += 1
                time.sleep(cfg["request_delay_seconds"])
            spent += saved["estimated_usd"]
            body = saved["response"]
            page_valid = 0
            for tweet in body["tweets"]:
                try:
                    row = normalize_tweet(tweet, window, saved["retrieved_at"])
                    corpus.setdefault(row["id"], row)
                    page_valid += 1
                except (ValueError, TypeError) as exc:
                    invalid.append({"id": str(tweet.get("id", "")), "reason": str(exc)})
            if body["tweets"] and page_valid == 0:
                status = "invalid_page_stopped_before_more_paid_requests"
                break
            if not body["has_next_page"]:
                status = "provider_pagination_exhausted_not_proof_of_full_coverage"
                break
            next_cursor = body.get("next_cursor")
            if not next_cursor or next_cursor in seen or next_cursor == cursor:
                raise ValueError("Missing or repeated pagination cursor")
            seen.add(next_cursor)
            cursor = next_cursor
        windows.append({**window, "status": status})
    write_jsonl(root / "data/private/twitter_pilot.jsonl", list(corpus.values()))
    summary = {"unique_valid_posts": len(corpus), "invalid_posts": invalid,
               "estimated_total_cached_and_new_usd": spent, "new_requests": calls, "windows": windows,
               "scope": cfg["scope"], "cost_control": "local conservative reserve; not a provider-enforced hard cap"}
    write_json(root / "reports/twitter_pilot_status.json", summary)
    return summary


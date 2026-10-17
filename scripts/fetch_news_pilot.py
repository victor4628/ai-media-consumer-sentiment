"""Bounded RSS discovery and headline-only pilot. No archive or balance claims."""
import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sentiment_project.common import digest, now_utc, read_json, write_json, write_jsonl


class FeedLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "link" and a.get("type") in ["application/rss+xml", "application/atom+xml"] and a.get("href"):
            self.urls.append(a["href"])


def download(url):
    if urlparse(url).scheme != "https":
        raise ValueError("Only HTTPS feeds allowed")
    with urlopen(Request(url, headers={"User-Agent": "ConsumerSentimentResearch/0.1"}), timeout=25) as r:
        return r.read(5_000_000)


def plain(value):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", value or ""))).strip()


def main():
    cfg = read_json(ROOT / "configs/news_sources.json")
    as_of = read_json(ROOT / "configs/project.json")["as_of"]
    # Exclude the current incomplete local day. This also avoids collecting later-today posts.
    cutoff = datetime.fromisoformat(as_of).replace(tzinfo=ZoneInfo("America/New_York"))
    raw = ROOT / "data/raw/news_pilot" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    raw.mkdir(parents=True, exist_ok=True)
    rows, manifest = {}, []
    for source in cfg["sources"]:
        status = {"source": source["id"], "source_page": source["page"], "retrieved_at": now_utc()}
        try:
            feed = source.get("feed")
            if not feed:
                parser = FeedLinks()
                parser.feed(download(source["page"]).decode("utf-8", errors="replace"))
                if not parser.urls:
                    status["status"] = "no_feed_link_discovered"
                    manifest.append(status)
                    print(source["id"], status["status"], flush=True)
                    continue
                feed = urljoin(source["page"], parser.urls[0])
            data = download(feed)
            (raw / f"{source['id']}.xml").write_bytes(data)
            tree = ET.fromstring(data)
            entries = tree.findall(".//item")
            status.update({"feed": feed, "sha256": digest(data), "rss_items": len(entries), "accepted": 0, "missing_or_invalid_date": 0, "after_cutoff": 0})
            if not entries:
                status["status"] = "no_rss_items_or_atom_not_yet_supported"
            else:
                status["status"] = "downloaded"
            for entry in entries[:200]:
                title = plain(entry.findtext("title"))
                link = entry.findtext("link") or ""
                date = entry.findtext("pubDate") or ""
                try:
                    published = parsedate_to_datetime(date)
                    if published.tzinfo is None:
                        raise ValueError("Missing timezone")
                except (TypeError, ValueError):
                    status["missing_or_invalid_date"] += 1
                    continue
                if published >= cutoff:
                    status["after_cutoff"] += 1
                    continue
                if not title or not link or not any(k in title.lower() for k in cfg["keywords"]):
                    continue
                record = {"id": "news:" + digest(link)[:24], "platform": "news", "source": source.get("outlet", source["id"]),
                          "source_level": source["level"], "published_at": published.astimezone(timezone.utc).isoformat(),
                          "retrieved_at": status["retrieved_at"], "text": title, "text_type": "headline",
                          "url": link, "content_hash": digest(title), "story_group": digest(title.lower().split()),
                          "us_relevance": "unknown", "sample_scope": "current_rss_keyword_pilot_not_historical_or_balanced"}
                rows[record["id"]] = record
                status["accepted"] += 1
        except Exception as exc:
            status.update({"status": "failed", "error_type": type(exc).__name__})
        manifest.append(status)
        print(source["id"], status["status"], status.get("accepted", 0), flush=True)
    write_jsonl(ROOT / "data/private/news_pilot.jsonl", list(rows.values()))
    write_json(ROOT / "reports/news_pilot_status.json", {"scope": cfg["scope"], "cutoff_exclusive": cutoff.isoformat(), "unique_headlines": len(rows), "sources": manifest})
    print("Total unique economic headline candidates:", len(rows))


if __name__ == "__main__":
    main()

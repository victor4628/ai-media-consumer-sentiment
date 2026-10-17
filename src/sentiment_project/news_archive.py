"""GDELT headline candidates; discovery timestamps never masquerade as publication."""
import html
import re
from collections import Counter
from datetime import datetime, timezone, timedelta
from urllib.parse import urlsplit, urlunsplit

from .common import digest

NATIONAL = {"npr.org", "pbs.org", "apnews.com", "reuters.com", "cnn.com", "cnbc.com", "abcnews.go.com", "cbsnews.com", "nbcnews.com", "foxnews.com", "nytimes.com", "washingtonpost.com", "usatoday.com", "wsj.com", "bloomberg.com", "politico.com", "thehill.com", "marketplace.org"}
LOCAL = {"wunc.org", "wbur.org", "kuow.org", "wamu.org", "kqed.org", "wbez.org", "whyy.org", "wpr.org", "mprnews.org", "houstonpublicmedia.org", "texastribune.org", "latimes.com", "chicagotribune.com", "seattletimes.com", "bostonglobe.com", "inquirer.com", "sfchronicle.com", "denverpost.com", "dallasnews.com", "miamiherald.com", "ajc.com", "startribune.com", "oregonlive.com", "cleveland.com", "detroitnews.com", "freep.com", "azcentral.com", "tampabay.com", "post-gazette.com", "ocregister.com", "thehour.com", "middletownpress.com", "aspentimes.com"}
KEYWORDS = re.compile(r"\b(econom(?:y|ic)|inflation|prices?|wages?|hiring|layoffs?|recession|rents?|mortgages?|housing|unemployment|jobless|consumers?|afford(?:able|ability)?|tariffs?|cost.of.living|jobs)\b", re.I)


def tag(extras, name):
    match = re.search(r"<" + name + r">(.*?)</" + name + r">", extras, re.S)
    return html.unescape(match[1]).strip() if match else None


def parse_gkg(data, archive_url, archive_sha, retrieved_at):
    rows, counts = [], Counter()
    for line in data.decode("utf-8", errors="replace").splitlines():
        counts["all_rows"] += 1
        fields = line.split("\t")
        if len(fields) != 27:
            counts["bad_column_count"] += 1
            continue
        url = fields[4]
        parts = urlsplit(url)
        domain = (parts.hostname or "").lower().removeprefix("www.")
        source = next((d for d in NATIONAL | LOCAL if domain == d or domain.endswith("." + d)), None)
        if not source:
            continue
        counts["selected_outlet_rows"] += 1
        title = tag(fields[26], "PAGE_TITLE")
        if not title or "\ufffd" in title or not KEYWORDS.search(title):
            continue
        counts["economic_title_candidates"] += 1
        seen = datetime.strptime(fields[1], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        raw_publication = tag(fields[26], "PAGE_PRECISEPUBTIMESTAMP")
        published, status = None, "missing_publication_timestamp"
        if raw_publication:
            try:
                pub = datetime.strptime(raw_publication, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
                published = pub.isoformat()
                status = "publication_after_discovery" if pub > seen else "older_than_31_days" if seen - pub > timedelta(days=31) else "timestamp_candidate_valid"
            except ValueError:
                status = "invalid_publication_timestamp"
        counts[status] += 1
        canonical = urlunsplit((parts.scheme, parts.netloc.lower(), parts.path, parts.query, ""))
        rows.append({"id": "gdelt:" + digest(canonical)[:24], "platform": "news", "source": source,
                     "source_level": "national" if source in NATIONAL else "local_or_regional", "text": title,
                     "text_scope": "headline_only", "url": url, "published_at": published,
                     "publication_timestamp_status": status, "publication_timestamp_source": "GDELT extracted metadata, not independently verified",
                     "discovered_at": seen.isoformat(), "retrieved_at": retrieved_at,
                     "story_group": digest(" ".join(title.lower().split())), "content_hash": digest(title),
                     "archive_url": archive_url, "archive_sha256": archive_sha,
                     "us_relevance": "unknown", "scope": "Selected US outlets do not guarantee US subject matter; keyword candidates only"})
    return rows, dict(counts)

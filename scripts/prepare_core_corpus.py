"""Freeze monthly coding corpus and a balanced, story-separated 300-item audit."""
import json
import argparse
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sentiment_project.common import digest, read_json, read_jsonl, write_json, write_jsonl
from sentiment_project.corpus import group_id
from sentiment_project.ai_validation import validate_items


def round_robin(items, n, rng, seen, month_balanced=False):
    buckets = defaultdict(list)
    for item in items:
        buckets[(item["published_at"][:7], item["source"])].append(item)
    for bucket in buckets.values():
        bucket.sort(key=lambda i: i["id"])
        rng.shuffle(bucket)
    selected = []
    key_order = sorted(buckets)
    if month_balanced:
        months = defaultdict(list)
        for key in key_order:
            months[key[0]].append(key)
        month_order = sorted(months)
        rng.shuffle(month_order)
        for keys in months.values():
            rng.shuffle(keys)
        key_order = [months[m][round_n] for round_n in range(max(map(len, months.values()))) for m in month_order if round_n < len(months[m])]
    while buckets and len(selected) < n:
        for key in key_order:
            if key not in buckets:
                continue
            while buckets[key]:
                row = buckets[key].pop()
                if group_id(row) not in seen:
                    seen.add(group_id(row))
                    selected.append(row)
                    break
            if not buckets[key]:
                del buckets[key]
            if len(selected) >= n:
                break
    return selected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--news-only", action="store_true")
    parser.add_argument("--twitter-prefix", action="store_true")
    args = parser.parse_args()
    folder = ROOT / "data/private/core_v1"
    frozen = folder / "corpus_manifest.json"
    if frozen.exists():
        manifest = read_json(frozen)
        if digest(read_jsonl(folder / "corpus.jsonl")) != manifest["corpus_sha256"]:
            raise ValueError("Frozen corpus changed")
        print(json.dumps(manifest, indent=2))
        return
    cfg = read_json(ROOT / "configs/core_study.json")
    old = read_jsonl(ROOT / "data/private/validation_pilot_v1.jsonl")
    seen = {group_id(i) for i in old}
    rng = random.Random(cfg["seed"])
    inputs = [i for platform in (["news"] if args.news_only else ["news", "twitter"]) for i in read_jsonl(folder / f"{platform}.jsonl")]
    validate_items(inputs)
    buckets = defaultdict(list)
    for item in inputs:
        buckets[(item["platform"], item["published_at"][:7])].append(item)
    corpus = []
    # Equal maximum coding allowance per platform/month, no popularity selection.
    for key in sorted(buckets):
        corpus.extend(round_robin(buckets[key], 12, rng, seen))
    if args.news_only:
        corpus.sort(key=lambda i: (i["published_at"], i["id"]))
        write_jsonl(folder / "news_coding.jsonl", corpus)
        write_json(folder / "news_coding.manifest.json", {"input_sha256": digest(inputs), "items": len(corpus), "sha256": digest(corpus)})
        news_audit = round_robin(corpus, 150, random.Random(cfg["seed"] + 100), set())
        news_audit.sort(key=lambda i: i["id"])
        write_jsonl(folder / "news_audit_150.jsonl", news_audit)
        write_json(folder / "news_audit_150.manifest.json", {"sample_sha256": digest(news_audit), "seed": cfg["seed"] + 100, "rule": "Label-independent month/source round robin; reserved 150 news audit records"})
        balanced = round_robin(corpus, 150, random.Random(cfg["seed"] + 100), set(), month_balanced=True)
        balanced.sort(key=lambda i: i["id"])
        write_jsonl(folder / "news_audit_balanced_150.jsonl", balanced)
        write_json(folder / "news_audit_balanced_150.manifest.json", {"sample_sha256": digest(balanced), "rule": "First cover every available month, then additional sources; replaces early-biased preliminary news audit; no labels used"})
        print(json.dumps({"items": len(corpus), "output": str(folder / "news_coding.jsonl")}))
        return
    if args.twitter_prefix:
        twitter = sorted([i for i in corpus if i["platform"] == "twitter"], key=lambda i: (i["published_at"], i["id"]))
        twitter = twitter[:len(twitter) // 6 * 6]
        write_jsonl(folder / "twitter_coding_prefix.jsonl", twitter)
        print(json.dumps({"items": len(twitter), "output": str(folder / "twitter_coding_prefix.jsonl")}))
        return
    audit_seen, audit_selected = set(), []
    for offset, platform in enumerate(["news", "twitter"]):
        group = round_robin([i for i in corpus if i["platform"] == platform], 150, random.Random(cfg["seed"] + 100 + offset), audit_seen, month_balanced=True)
        if len(group) != 150:
            raise ValueError("Not enough independent items for 150/platform formal audit")
        audit_selected.extend(group)
    # Within each platform, 50 development and 100 held-out; no label-driven allocation.
    development, audit = [], []
    for offset, platform in enumerate(["news", "twitter"]):
        group = [i for i in audit_selected if i["platform"] == platform]
        random.Random(cfg["seed"] + 200 + offset).shuffle(group)
        development.extend(group[:50])
        audit.extend(group[50:])
    for group in [corpus, audit_selected, development, audit]:
        group.sort(key=lambda i: i["id"])
    corpus.sort(key=lambda i: (i["published_at"], i["id"]))
    files = {"corpus": corpus, "audit_all_300": audit_selected, "development_100": development, "audit_200": audit}
    manifest = {"study_id": cfg["study_id"], "items": len(corpus), "corpus_sha256": digest(corpus),
                "input_sha256": digest(inputs), "prompt_sha256": digest((ROOT / "prompts/economic_coding_v2.txt").read_text(encoding="utf-8")),
                "by_platform": dict(Counter(i["platform"] for i in corpus)), "by_month": dict(Counter(i["published_at"][:7] for i in corpus)),
                "audit": {"total": 300, "development": 100, "held_out": 200, "platform_quota": 150},
                "old_development_story_groups_excluded": True, "seed": cfg["seed"], "scope": cfg["sampling_scope"],
                "grouping_limit": "Normalized headline/text exact groups; semantic syndication clustering still a limitation",
                "files": {name: {"items": len(items), "sha256": digest(items)} for name, items in files.items()}}
    for name, items in files.items():
        write_jsonl(folder / f"{name}.jsonl", items)
    write_jsonl(folder / "twitter_coding.jsonl", [i for i in corpus if i["platform"] == "twitter"])
    write_json(frozen, manifest)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()

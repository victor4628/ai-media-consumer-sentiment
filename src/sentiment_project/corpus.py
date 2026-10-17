"""Frozen, reproducible audit sampling; never fabricate missing media items."""
import random
import re
from collections import defaultdict
from pathlib import Path

from .ai_validation import validate_items
from .common import digest, write_json, write_jsonl


def group_id(item):
    # Respect supplied syndicated-story grouping; otherwise detect exact normalized duplicates.
    # Semantic/near-duplicate story grouping still needs a later corpus-specific pass.
    return item.get("story_group") or digest(re.sub(r"\s+", " ", item["text"].lower()).strip())


def prepare_audit(items, output_dir, size=300, seed=20261016):
    if size < 300:
        raise ValueError("Formal audit needs at least 300 real texts; use label dry-run for a smaller pilot")
    validate_items(items)
    output_dir = Path(output_dir)
    if (output_dir / "manifest.json").exists():
        raise ValueError("Frozen audit already exists; use a new output directory for a new version")
    buckets = defaultdict(list)
    for item in items:
        key = (item.get("platform", "unknown"), item.get("source", "unknown"), item["published_at"][:7])
        buckets[key].append(item)
    rng = random.Random(seed)
    for key in sorted(buckets):
        buckets[key].sort(key=lambda x: x["id"])
        rng.shuffle(buckets[key])
    selected, groups = [], set()
    keys = sorted(buckets)
    # Round robin prevents one prolific source/month from consuming the entire audit.
    while keys and len(selected) < size:
        for key in list(keys):
            while buckets[key]:
                item = buckets[key].pop()
                gid = group_id(item)
                if gid not in groups:
                    selected.append(item)
                    groups.add(gid)
                    break
            if not buckets[key]:
                keys.remove(key)
            if len(selected) >= size:
                break
    if len(selected) < size:
        raise ValueError(f"Only {len(selected)} independent groups available; need {size}")
    platforms = {i.get("platform") for i in selected}
    if not {"news", "twitter"}.issubset(platforms):
        raise ValueError("Formal audit must include both news and Twitter")
    rng.shuffle(selected)
    development_n = size // 3
    development, audit = selected[:development_n], selected[development_n:]
    manifest = {"size": size, "seed": seed, "development": len(development), "frozen_audit": len(audit),
                "input_sha256": digest(sorted(items, key=lambda x: x["id"])),
                "sample_sha256": digest(selected),
                "sampling": "round-robin source/platform/month strata; equal story-group cap; not population weights",
                "grouping_limit": "exact normalized text or supplied story_group; semantic duplicates still require review",
                "items": [{"id": i["id"], "sha256": digest(i), "group": group_id(i), "split": "development" if n < development_n else "audit"} for n, i in enumerate(selected)]}
    write_jsonl(output_dir / "development.jsonl", development)
    write_jsonl(output_dir / "audit.jsonl", audit)
    write_json(output_dir / "manifest.json", manifest)
    return {"size": size, "development": development_n, "audit": size - development_n, "output_dir": str(output_dir)}


def review_queue(items, comparison, output, seed=20261016):
    validate_items(items)
    mapping = {i["id"]: i for i in items}
    disagreements = {r["id"] for r in comparison["disagreements"]}
    if not disagreements.issubset(mapping):
        raise ValueError("Comparison refers to missing corpus items")
    if len(mapping) != comparison["paired_items"]:
        raise ValueError("Review input must be the same paired corpus")
    agreeing = sorted(set(mapping) - disagreements)
    rng = random.Random(seed)
    sampled = set(rng.sample(agreeing, min(len(agreeing), max(1, (len(agreeing) + 9) // 10))))
    # Labels and disagreement flags are deliberately NOT passed to the independent C call.
    selected = [mapping[i] for i in sorted(disagreements | sampled)]
    write_jsonl(output, selected)
    write_json(str(output) + ".manifest.json", {"seed": seed, "disagreement_ids": sorted(disagreements), "agreement_check_ids": sorted(sampled), "corpus_sha256": digest(items)})
    return {"items": len(selected), "disagreement_items": len(disagreements), "agreement_checks": len(sampled), "output": str(output)}


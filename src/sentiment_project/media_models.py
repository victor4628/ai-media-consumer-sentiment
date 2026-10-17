"""Preceding-month media features and expanding forecast comparisons."""
from collections import defaultdict
from datetime import datetime, timezone

import numpy as np
import pandas as pd

TONE = {"negative": -1.0, "neutral": 0.0, "positive": 1.0, "mixed": 0.0}


def monthly_media(items, labels, start, end):
    mapping = {r["id"]: r for r in labels}
    if len(mapping) != len(labels) or set(mapping) != {i["id"] for i in items}:
        raise ValueError("Every corpus item requires exactly one paired label")
    grouped = defaultdict(list)
    for item in items:
        if mapping[item["id"]]["input_sha256"]:
            from .common import digest
            if mapping[item["id"]]["input_sha256"] != digest(item):
                raise ValueError("Media label input hash mismatch")
        label = mapping[item["id"]]["label"]
        published = pd.Timestamp(item["published_at"])
        month = published.strftime("%Y-%m")
        if not start <= month <= end:
            continue
        cutoff = (pd.Timestamp(month + "-01", tz="UTC") + pd.offsets.MonthBegin(1))
        discovered = pd.Timestamp(item.get("discovered_at", item["published_at"]))
        available = max(published, discovered)
        eligible = label is not None and label["us_relevance"] == "yes" and bool(label["topics"]) and available < cutoff
        grouped[(month, item["platform"])].append((item, label, eligible))
    rows = []
    for month in pd.period_range(start, end, freq="M"):
        row = {"media_month": str(month), "target_month": (month + 1).start_time.strftime("%Y-%m-%d")}
        for platform in ["news", "twitter"]:
            candidates = grouped[(str(month), platform)]
            usable = [(item, label) for item, label, eligible in candidates if eligible]
            scored = [(item, label) for item, label in usable if label["tone"] in TONE]
            row[platform + "_candidate_n"] = len(candidates)
            row[platform + "_invalid_label_n"] = sum(label is None for _, label, _ in candidates)
            row[platform + "_eligible_n"] = len(usable)
            row[platform + "_scored_n"] = len(scored)
            row[platform + "_uncertain_share"] = sum(label["tone"] == "uncertain" for _, label in usable) / len(usable) if usable else np.nan
            if platform == "news":
                sources = defaultdict(list)
                for item, label in scored:
                    sources[item["source"]].append(TONE[label["tone"]])
                row["news_outlet_n"] = len(sources)
                row["news_local_n"] = sum(item.get("source_level") == "local_or_regional" for item, _ in usable)
                # Equal weight each observed outlet; no one prolific source dominates.
                row["news_tone"] = float(np.mean([np.mean(scores) for scores in sources.values()])) if sources else np.nan
                row["news_negative_share"] = float(np.mean([np.mean(np.asarray(scores) < 0) for scores in sources.values()])) if sources else np.nan
            else:
                row["twitter_tone"] = float(np.mean([TONE[label["tone"]] for _, label in scored])) if scored else np.nan
                row["twitter_negative_share"] = float(np.mean([label["tone"] == "negative" for _, label in scored])) if scored else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def ridge_prediction(train, current, features, penalty=1.0):
    x = train[features].to_numpy(float)
    mu, scale = x.mean(axis=0), x.std(axis=0)
    scale[scale < 1e-12] = 1
    design = np.column_stack([np.ones(len(x)), (x - mu) / scale])
    regularizer = np.eye(design.shape[1]) * penalty
    regularizer[0, 0] = 0
    beta = np.linalg.solve(design.T @ design + regularizer, design.T @ train.label.to_numpy(float))
    prediction = float(np.r_[1, (current[features].to_numpy(float) - mu) / scale] @ beta)
    return prediction, {name: float(beta[n + 1]) for n, name in enumerate(features)}


def rolling_comparison(panel, labels_at_origin, evaluation, min_train=24, evaluation_start="2023-01-01", min_news=1, min_twitter=3, include_memory=True, models_override=None):
    base = ["unemployment", "pce_yoy", "gdp_growth"] + (["sentiment_available"] if include_memory else [])
    models = {
        "M1_economic": base,
        "M2_add_media": base + ["news_tone", "twitter_tone"],
        "M3_add_household": base + ["news_tone", "twitter_tone", "income_yoy"],
    }
    if models_override is not None:
        models = models_override
    full = list(dict.fromkeys(f for features in models.values() for f in features))
    valid = panel[(panel.news_scored_n >= min_news) & (panel.twitter_scored_n >= min_twitter)].dropna(subset=full).copy()
    predictions, coefficients = [], []
    for _, current in valid.sort_values("target_month").iterrows():
        target, vintage = current.target_month, current.information_cutoff
        if target < evaluation_start or target not in evaluation:
            continue
        history = valid[valid.target_month < target].copy()
        history["label"] = history.target_month.map(labels_at_origin(vintage))
        history = history.dropna(subset=["label"])
        if len(history) < min_train:
            continue
        row = {"target_month": target, "information_cutoff": vintage, "training_n": len(history), "latest_training_target": max(history.target_month),
               "actual": evaluation[target], "persistence": current.sentiment_available,
               "news_n": current.news_scored_n, "twitter_n": current.twitter_scored_n}
        for name, features in models.items():
            row[name], beta = ridge_prediction(history, current, features)
            coefficients.append({"target_month": target, "model": name, **beta})
            # Calibrate only on older OOS predictions whose targets are now released.
            available = labels_at_origin(vintage)
            residuals = [abs(available[p["target_month"]] - p[name]) for p in predictions if p["target_month"] in available]
            width = float(np.quantile(residuals, .95)) if len(residuals) >= 12 else np.nan
            row[name + "_empirical_low"] = row[name] - width
            row[name + "_empirical_high"] = row[name] + width
            row[name + "_calibration_n"] = len(residuals)
        predictions.append(row)
    return pd.DataFrame(predictions), pd.DataFrame(coefficients), valid


def paired_block_interval(predictions, left, right, seed=20261017, repetitions=2000, block=3):
    """Paired moving-block bootstrap of MAE difference; negative favors left."""
    delta = (predictions[left] - predictions.actual).abs().to_numpy() - (predictions[right] - predictions.actual).abs().to_numpy()
    if len(delta) < 12:
        return {"n": len(delta), "difference": float(delta.mean()) if len(delta) else None, "interval": None}
    # Preserve each observed contiguous run's size; never drop isolated months or cross gaps.
    periods = pd.PeriodIndex(pd.to_datetime(predictions.target_month), freq="M").asi8
    segments = np.split(delta, np.where(np.diff(periods) != 1)[0] + 1)
    if max(map(len, segments)) < 2:
        return {"n": len(delta), "difference": float(delta.mean()), "interval": None, "reason": "No contiguous blocks"}
    rng = np.random.default_rng(seed)
    means = []
    for _ in range(repetitions):
        draws = []
        for segment in segments:
            length = len(segment)
            width = min(block, max(1, length // 2))
            starts = rng.integers(0, length, size=int(np.ceil(length / width)))
            indices = np.concatenate([(start + np.arange(width)) % length for start in starts])[:length]
            draws.append(segment[indices])
        means.append(np.concatenate(draws).mean())
    return {"n": len(delta), "difference": float(delta.mean()), "interval": np.quantile(means, [0.025, 0.975]).tolist(), "block_months": block,
            "segments": list(map(len, segments)),
            "scope": "Segment-preserving circular block bootstrap; exploratory conditional on observed sparse months, not causal inference"}

"""Join real coded media to vintage macro data and compare identical OOS months."""
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sentiment_project.common import digest, read_json, read_jsonl, write_json
from sentiment_project.media_models import monthly_media, paired_block_interval, rolling_comparison
from sentiment_project.vintages import parse_snapshot


def snapshot(series, vintage):
    return parse_snapshot((ROOT / f"data/raw/alfred_vintages/{vintage}/{series}.csv").read_bytes(), series, vintage)


def main():
    cfg = read_json(ROOT / "configs/core_study.json")
    folder = ROOT / "data/private/core_v1"
    corpus = read_jsonl(folder / "corpus.jsonl")
    labels = read_jsonl(ROOT / f"labels/runs/core_v1/{digest(corpus)[:12]}_A.jsonl")
    media = monthly_media(corpus, labels, cfg["media_start"], cfg["media_end"])
    media.to_csv(ROOT / "data/processed/core_monthly_media.csv", index=False)
    macro = pd.read_csv(ROOT / "data/processed/vintage_feature_panel.csv")
    panel = macro.merge(media, on="target_month", how="inner", validate="one_to_one")
    panel.to_csv(ROOT / "data/processed/core_model_panel.csv", index=False)
    evaluation = snapshot("UMCSENT", "2026-10-16")
    label_map = {row["id"]: row["label"] for row in labels}
    descriptive = {}
    for platform in ["news", "twitter"]:
        selected = []
        for item in corpus:
            label = label_map[item["id"]]
            publication = pd.Timestamp(item["published_at"])
            available = max(publication, pd.Timestamp(item.get("discovered_at", item["published_at"])))
            cutoff = pd.Timestamp(publication.strftime("%Y-%m") + "-01", tz="UTC") + pd.offsets.MonthBegin(1)
            if item["platform"] == platform and label is not None and label["us_relevance"] == "yes" and label["topics"] and available < cutoff:
                selected.append(label)
        descriptive[platform] = {"n": len(selected), "dimensions": {field: dict(Counter(label[field] for label in selected)) for field in ["tone", "language_style", "price_frame", "scope_frame", "time_frame", "political_attribution", "factual_calibration"]},
                                 "topics_multilabel": dict(Counter(topic for label in selected for topic in label["topics"])), "scope": "Pooled sampled eligible texts; not population reporting shares or accuracy", "external_numeric_fact_check_coverage": 0}
    write_json(ROOT / "reports/core_media_descriptive.json", descriptive)
    get_labels = lambda vintage: snapshot("UMCSENT", vintage)
    forecasts, coefficients, eligible = rolling_comparison(panel, get_labels, evaluation, cfg["minimum_training_months"], cfg["model_evaluation_start"])
    if forecasts.empty:
        write_json(ROOT / "reports/core_analysis.json", {"status": "insufficient_overlap", "media_months": len(media), "eligible_months": len(eligible), "scope": cfg["sampling_scope"]})
        raise ValueError("Insufficient common months; cannot fabricate a three-model result")
    forecasts.to_csv(ROOT / "data/processed/core_predictions.csv", index=False)
    coefficients.to_csv(ROOT / "data/processed/core_rolling_coefficients.csv", index=False)
    metrics = {}
    for name in ["persistence", "M1_economic", "M2_add_media", "M3_add_household"]:
        errors = forecasts[name] - forecasts.actual
        metrics[name] = {"n": len(errors), "MAE": float(errors.abs().mean()), "RMSE": float(np.sqrt((errors ** 2).mean())), "mean_error": float(errors.mean())}
        if name != "persistence":
            band = forecasts.dropna(subset=[name + "_empirical_low", name + "_empirical_high"])
            metrics[name]["empirical_band_n"] = len(band)
            metrics[name]["empirical_95_band_coverage"] = float(((band.actual >= band[name + "_empirical_low"]) & (band.actual <= band[name + "_empirical_high"])).mean()) if len(band) else None
    sensitivity = {}
    for name, news_n, twitter_n in [("minimum_2_news_5_tweets", 2, 5), ("minimum_3_news_5_tweets", 3, 5)]:
        alternate, _, valid = rolling_comparison(panel, get_labels, evaluation, cfg["minimum_training_months"], cfg["model_evaluation_start"], news_n, twitter_n)
        sensitivity[name] = {"eligible_months": len(valid), "test_months": len(alternate)}
        if not alternate.empty:
            sensitivity[name]["MAE"] = {m: float((alternate[m] - alternate.actual).abs().mean()) for m in metrics}
    alternate_panel = panel.copy()
    alternate_panel["news_tone"] = -alternate_panel.news_negative_share
    alternate_panel["twitter_tone"] = -alternate_panel.twitter_negative_share
    alternate, _, valid = rolling_comparison(alternate_panel, get_labels, evaluation, cfg["minimum_training_months"], cfg["model_evaluation_start"])
    sensitivity["negative_share_instead_of_mean_tone"] = {"eligible_months": len(valid), "test_months": len(alternate), "MAE": {m: float((alternate[m] - alternate.actual).abs().mean()) for m in metrics} if not alternate.empty else {}}
    alternate, _, valid = rolling_comparison(panel, get_labels, evaluation, cfg["minimum_training_months"], cfg["model_evaluation_start"], include_memory=False)
    sensitivity["economic_only_without_sentiment_memory_posthoc"] = {"eligible_months": len(valid), "test_months": len(alternate), "MAE": {m: float((alternate[m] - alternate.actual).abs().mean()) for m in metrics} if not alternate.empty else {}, "scope": "Post-hoc supplemental specification matching the pure economic baseline; primary specification unchanged"}
    report = {"status": "preliminary_measured_media_analysis", "data_scope": cfg["sampling_scope"], "corpus_items": len(corpus), "media_months": len(media),
              "months_with_both_media": int(((media.news_scored_n >= 1) & (media.twitter_scored_n >= 3)).sum()), "common_eligible_months": len(eligible),
              "common_test_months": len(forecasts), "test_start": forecasts.target_month.min(), "test_end": forecasts.target_month.max(), "metrics": metrics,
              "M2_minus_M1_MAE": paired_block_interval(forecasts, "M2_add_media", "M1_economic"),
              "M3_minus_M2_MAE": paired_block_interval(forecasts, "M3_add_household", "M2_add_media"),
              "coverage_sensitivity": sensitivity, "estimator": "Expanding standardized ridge, fixed penalty 1; standardization fit only on training data; unpenalized intercept",
              "primary_media": "Previous calendar-month US-relevant economic content; negative -1 neutral/mixed 0 positive +1; uncertain excluded and reported; news equal observed-outlet weight",
              "label_availability": "Past-origin macro features; training targets drawn from forecast-origin ALFRED vintage; evaluation vintage 2026-10-16 only for scoring",
              "household_proxy": "DSPIC96 real disposable personal income YoY, national aggregate proxy, not household microdata",
              "validation": "Formal AI audit is reported separately; no human gold standard; no causal interpretation",
              "limitations": ["Sparse time-window and keyword selection", "News headlines, not full articles", "News metadata timestamps not independently checked publication timestamps", "Potential semantic story duplication", "Shared-family AI errors", "US-relevance filtering and missing coverage select the analyzed population", "Small noncontinuous evaluation sample", "Historical texts were classified retrospectively with 2026 models; original online implementability not demonstrated", "M3 contains one aggregate household proxy; debt/wealth and sentiment subindices not included"]}
    write_json(ROOT / "reports/core_analysis.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

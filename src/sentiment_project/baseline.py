"""Exploratory rolling baseline on current snapshots, never labeled real-time."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .common import ROOT, read_json, write_json

FEATURES = ["unemployment", "pce_yoy", "gdp_growth"]


def diagnostic_panel(observations, start, as_of):
    data = observations.copy()
    data["period_end"] = pd.to_datetime(data.period_end)
    if data.duplicated(["series_id", "period_end"]).any():
        raise ValueError("Duplicate series/period")
    cutoff = pd.Timestamp(as_of)
    last_complete = cutoff.to_period("M") - 1
    monthly = {sid: group.set_index("period_end").value for sid, group in data.groupby("series_id")}
    gdp = data[data.series_id == "gdp_growth"].copy()
    # Illustrative assumption only: available at the end of the following month.
    gdp["assumed_available"] = gdp.period_end + pd.offsets.MonthEnd(1)
    records = []
    for p in pd.period_range(start, last_complete, freq="M"):
        target, origin = p.end_time.normalize(), p.start_time - pd.Timedelta(days=1)
        macro_period = (p - 2).end_time.normalize()
        row = {"period_end": target, "forecast_cutoff": origin,
               "sentiment": monthly["sentiment"].get(target, np.nan),
               "persistence": monthly["sentiment"].get((p - 1).end_time.normalize(), np.nan),
               "unemployment": monthly["unemployment"].get(macro_period, np.nan),
               "pce_yoy": monthly["pce_yoy"].get(macro_period, np.nan),
               "monthly_macro_period": macro_period,
               "gdp_growth": np.nan, "gdp_period": pd.NaT}
        available = gdp[gdp.assumed_available <= origin].sort_values("period_end")
        if not available.empty:
            latest = available.iloc[-1]
            # Do not silently carry an obsolete GDP observation indefinitely.
            if origin - latest.period_end <= pd.Timedelta(days=160):
                row["gdp_growth"], row["gdp_period"] = latest.value, latest.period_end
        records.append(row)
    return pd.DataFrame(records)


def rolling_baseline(panel, evaluation_start, min_training=60):
    panel = panel.sort_values("period_end").copy()
    records, previous_errors = [], []
    for row in panel.itertuples(index=False):
        if row.period_end < pd.Timestamp(evaluation_start):
            continue
        train = panel[panel.period_end < row.period_end].dropna(subset=FEATURES + ["sentiment"])
        x = np.array([getattr(row, c) for c in FEATURES], dtype=float)
        if len(train) < min_training or not np.isfinite(x).all() or not np.isfinite(row.sentiment) or not np.isfinite(row.persistence):
            continue
        X = np.column_stack([np.ones(len(train)), train[FEATURES].to_numpy(dtype=float)])
        beta, _, rank, _ = np.linalg.lstsq(X, train.sentiment.to_numpy(dtype=float), rcond=None)
        if rank != X.shape[1]:
            raise ValueError("Rank-deficient baseline design")
        predicted = float(np.r_[1.0, x] @ beta)
        error = float(row.sentiment - predicted)
        # Empirical diagnostic band from PREVIOUS held-out errors only.
        radius = float(np.quantile(np.abs(previous_errors), 0.95, method="higher")) if len(previous_errors) >= 24 else np.nan
        records.append({"period_end": row.period_end.date().isoformat(), "actual": row.sentiment,
                        "economic_prediction": predicted, "persistence_prediction": row.persistence,
                        "diagnostic_gap": error, "empirical_low": predicted - radius, "empirical_high": predicted + radius,
                        "training_months": len(train), "training_end": train.period_end.max().date().isoformat(),
                        "data_status": "current_revised_snapshot_assumed_release_lags"})
        previous_errors.append(error)
    if not records:
        raise ValueError("Not enough complete data for diagnostic baseline")
    return pd.DataFrame(records)


def run_baseline(root=ROOT):
    cfg = read_json(root / "configs/project.json")
    source = root / "data/processed/official_snapshot_observations.csv"
    if not source.exists():
        raise ValueError("Download and normalize official snapshots first; workbook is not silently substituted")
    data = pd.read_csv(source)
    panel = diagnostic_panel(data, cfg["analysis_start"], cfg["as_of"])
    predictions = rolling_baseline(panel, cfg["evaluation_start"], cfg["min_training_months"])
    panel.to_csv(root / "data/processed/diagnostic_panel.csv", index=False)
    predictions.to_csv(root / "data/processed/diagnostic_predictions.csv", index=False)
    models = []
    for model, col in [("economic_only", "economic_prediction"), ("persistence", "persistence_prediction")]:
        errors = predictions.actual - predictions[col]
        models.append({"model": model, "months": len(errors), "mae": float(errors.abs().mean()),
                       "rmse": float(np.sqrt(np.mean(errors ** 2)))})
    bands = predictions.dropna(subset=["empirical_low", "empirical_high"])
    metrics = {"status": "EXPLORATORY_NOT_REALTIME", "evaluation_first": predictions.period_end.min(),
               "evaluation_last": predictions.period_end.max(), "models": models,
               "band_months": len(bands),
               "empirical_band_coverage": float(((bands.actual >= bands.empirical_low) & (bands.actual <= bands.empirical_high)).mean()) if len(bands) else None,
               "limitations": ["Current revised snapshots, not historical vintages", "Publication lags assumed, not verified", "Empirical bands assume historical error scale is informative; no guaranteed coverage", "No media observations or media-effect estimates"]}
    write_json(root / "reports/baseline_metrics.json", metrics)
    lines = ["# 经济基线：探索性运行", "", "**当前修订值 + 假设发布滞后；不是真实实时回测，不作为媒体偏见的证据。**", "",
             f"测试区间：{metrics['evaluation_first']} 至 {metrics['evaluation_last']}，共 {len(predictions)} 个可比较月份。", "",
             "| 模型 | MAE（指数点） | RMSE（指数点） |", "|---|---:|---:|"]
    for m in models:
        lines.append(f"| {m['model']} | {m['mae']:.2f} | {m['rmse']:.2f} |")
    lines += ["", "## 方法", "",
              "- 从 2010 年开始训练，2018 年起逐月扩展窗口 OLS；训练标签时期严格早于测试时期。",
              "- 月初预测：失业率和 PCE 使用目标月前两个月的观测。GDP 假设在季度结束后的下月底可用，保留季度观测日期，不插值。",
              "- 这些日期仅是示范假设；所有数值仍可能包含事后修订，所以时间顺序切分并未解决历史版本泄漏。",
              "- 与上月信心持续性预测在相同测试月份比较。月份缺失不插值，也不按上一非空行冒充上一月。",
              "- 经验误差带使用此前至少 24 个样本外误差的绝对值 95% 分位数；不使用当前测试误差。它不是完成校准的正式预测区间。",
              "- sentiment gap 只命名为 diagnostic_gap；未建媒体模型，不能判断媒体是否改善预测。", "",
              "## 下一阶段", "", "补充真实发布日、历史版本、调查子指数和媒体语料，再运行正式 M1/M2/M3 对照。"]
    (root / "reports/baseline_diagnostic.zh-CN.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return metrics


"""Monthly forecast-origin features and training labels available at that origin."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sentiment_project.common import read_json, write_json
from sentiment_project.vintages import annual_change, latest_value, parse_snapshot, quarterly_annualized

SERIES = {"unemployment": "UNRATE", "pce_yoy": "PCEPI", "gdp_growth": "GDPC1", "sentiment_available": "UMCSENT", "income_yoy": "DSPIC96"}


def snapshot(series, vintage):
    path = ROOT / "data/raw/alfred_vintages" / vintage / (series + ".csv")
    return parse_snapshot(path.read_bytes(), series, vintage)


def main():
    manifest = read_json(ROOT / "data/raw/alfred_vintages/manifest.json")
    if manifest["errors"]:
        raise ValueError("Resolve failed downloads before baseline construction")
    origins = sorted({r["vintage"] for r in manifest["records"]} - {"2026-10-16"})
    rows = []
    for vintage in origins:
        target = (pd.Timestamp(vintage) + pd.offsets.MonthBegin(1)).strftime("%Y-%m-%d")
        row = {"target_month": target, "information_cutoff": vintage}
        for name, series in SERIES.items():
            values = snapshot(series, vintage)
            transform = annual_change if name in ["pce_yoy", "income_yoy"] else quarterly_annualized if name == "gdp_growth" else latest_value
            period, value = transform(values, target)
            row[name] = value
            row[name + "_period"] = period
            row[name + "_age_months"] = (pd.Timestamp(target).year - pd.Timestamp(period).year) * 12 + pd.Timestamp(target).month - pd.Timestamp(period).month
        rows.append(row)
    frame = pd.DataFrame(rows)
    output = ROOT / "data/processed"
    output.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output / "vintage_feature_panel.csv", index=False)
    evaluation = snapshot("UMCSENT", "2026-10-16")
    predictions = []
    models = {
        "economic_only": ["unemployment", "pce_yoy", "gdp_growth"],
        "economic_with_sentiment_memory": ["unemployment", "pce_yoy", "gdp_growth", "sentiment_available"],
        "economic_with_income_and_memory": ["unemployment", "pce_yoy", "gdp_growth", "sentiment_available", "income_yoy"],
    }
    for _, current in frame.iterrows():
        target, vintage = current["target_month"], current["information_cutoff"]
        if target < "2018-01-01" or target not in evaluation:
            continue
        # Training labels use this forecast's snapshot, never the evaluation snapshot.
        available_labels = snapshot("UMCSENT", vintage)
        train = frame[frame.target_month < target].copy()
        train["label"] = train.target_month.map(available_labels)
        train = train.dropna(subset=["label"])
        if len(train) < 60:
            continue
        record = {"target_month": target, "information_cutoff": vintage, "actual_evaluation_vintage": "2026-10-16", "actual": evaluation[target], "training_rows": len(train), "latest_training_target": max(train.target_month), "persistence_available": current.sentiment_available}
        for name, features in models.items():
            x = np.column_stack([np.ones(len(train)), train[features].to_numpy(dtype=float)])
            y = train.label.to_numpy(dtype=float)
            beta = np.linalg.lstsq(x, y, rcond=None)[0]
            record[name] = float(np.r_[1, current[features].to_numpy(dtype=float)] @ beta)
        predictions.append(record)
    forecast = pd.DataFrame(predictions)
    forecast.to_csv(output / "vintage_baseline_predictions.csv", index=False)
    metrics = {}
    for model in ["persistence_available", *models]:
        error = forecast[model] - forecast.actual
        metrics[model] = {"n": len(error), "MAE": float(error.abs().mean()), "RMSE": float(np.sqrt((error ** 2).mean()))}
    report = {"scope": "ALFRED month-end information-set backtest, macro only; no media effect or causal claim",
              "feature_months": len(frame), "evaluation_months": len(forecast), "metrics": metrics,
              "release_date_rule": "Snapshots establish availability by cutoff, not exact first release dates. Publication-day fact checking still needs release records.",
              "training_rule": "Past-origin features; labels from each forecast-origin UMCSENT vintage; only previously available targets",
              "evaluation_rule": "Observed UMCSENT from 2026-10-16 vintage, not unreleased months",
              "limitations": ["ALFRED availability may lag original provider releases", "No current-conditions/expectations subindices yet", "No media variables, final M1/M2/M3 comparison pending", "No tuned hyperparameters or causal identification"],
              "feature_age_months": {name: {"min": int(frame[name + "_age_months"].min()), "max": int(frame[name + "_age_months"].max())} for name in SERIES}}
    write_json(ROOT / "reports/vintage_baseline.json", report)
    lines = ["# 历史版本经济基线", "", f"已构建 {len(frame)} 个月的预测时点特征，完成 {len(forecast)} 个共同月份的样本外预测。", "",
             "每个目标月使用前一月末的 ALFRED 快照；训练特征保留各自历史时点版本，训练标签只取本次预测时已发布的消费者信心。总体 PCE 同比按同一快照中相隔恰好 12 个月的指数计算，GDP 不插值。", "",
             "| 模型 | 月份 | MAE | RMSE |", "|---|---:|---:|---:|"]
    for name, m in metrics.items():
        lines.append(f"| {name} | {m['n']} | {m['MAE']:.3f} | {m['RMSE']:.3f} |")
    lines += ["", "这是宏观基线比较，尚不是课程要求的经济/加媒体/加家庭因素三模型结果。模型预测目标值统一以 2026-10-16 快照评分，不会将该评分版本用于更早的训练。", "",
              "月末快照证明该数值在截止时点可获得，不等于知道首次发布日期。发表日事实核查仍须补齐官方发布记录；ALFRED 的更新时点也可能晚于原始提供者。信心分项、媒体变量、稳健性区间与最终解释仍待完成。", "",
              "来源：[ALFRED 历史版本说明](https://fred.stlouisfed.org/docs/api/fred/alfred.html)。下载 URL、时间和 SHA256 位于私有原始目录的 manifest。"]
    (ROOT / "reports/vintage_baseline.zh-CN.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

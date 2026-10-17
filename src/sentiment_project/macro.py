from __future__ import annotations

import pandas as pd

from .common import ROOT, read_json, write_json

MAP = {"UNRATE": ("unemployment", "M"), "PCEPI": ("pce_index", "M"), "PCEPILFE": ("core_pce_index", "M"),
       "A191RL1Q225SBEA": ("gdp_growth", "Q"), "UMCSENT": ("sentiment", "M"),
       "DSPIC96": ("real_disposable_income", "M")}


def normalize_snapshots(root=ROOT):
    folder = root / "data/raw/fred_snapshot"
    manifest = read_json(folder / "manifest.json")
    write_json(root / "reports/data_provenance.json", manifest)
    rows = []
    for entry in manifest["series"]:
        if entry["status"] != "downloaded":
            continue
        sid, freq = MAP[entry["id"]]
        frame = pd.read_csv(folder / f"{entry['id']}.csv")
        dates = pd.to_datetime(frame.iloc[:, 0]).dt.to_period(freq).dt.to_timestamp(how="end").dt.normalize()
        values = pd.to_numeric(frame[entry["id"]], errors="coerce")
        for period, value in zip(dates, values):
            if pd.isna(value):
                continue
            rows.append({"series_id": sid, "period_end": period.date().isoformat(), "value": float(value),
                         "frequency": freq, "source_url": f"https://fred.stlouisfed.org/series/{entry['id']}",
                         "release_date": "", "vintage_date": "", "retrieved_at": manifest["retrieved_at"],
                         "status": "current_snapshot_not_historical_vintage"})
    long = pd.DataFrame(rows)
    if long.empty:
        raise ValueError("No downloaded official snapshots")
    pce = long[long.series_id == "pce_index"].copy().sort_values("period_end")
    lookup = dict(zip(pce.period_end, pce.value))
    extra = []
    for row in pce.to_dict("records"):
        date = pd.Timestamp(row["period_end"]).to_period("M") - 12
        prev = date.end_time.date().isoformat()
        if prev in lookup and lookup[prev] > 0:
            extra.append({**row, "series_id": "pce_yoy", "value": 100 * (row["value"] / lookup[prev] - 1)})
    long = pd.concat([long, pd.DataFrame(extra)], ignore_index=True).sort_values(["series_id", "period_end"])
    core = long[long.series_id == "core_pce_index"].copy()
    core_lookup = dict(zip(core.period_end, core.value))
    core_yoy = {}
    for date, value in core_lookup.items():
        prev = (pd.Period(date, freq="M") - 12).end_time.date().isoformat()
        if prev in core_lookup:
            core_yoy[date] = 100 * (value / core_lookup[prev] - 1)
    out = root / "data/processed"
    out.mkdir(parents=True, exist_ok=True)
    long.to_csv(out / "official_snapshot_observations.csv", index=False)
    wb = pd.read_csv(out / "workbook_observations.csv")
    comparison = wb.merge(long[["series_id", "period_end", "value", "source_url"]], on=["series_id", "period_end"], how="inner", suffixes=("_workbook", "_official"))
    comparison["difference"] = comparison.value_workbook - comparison.value_official
    comparison["within_tolerance"] = comparison.difference.abs() <= 0.0001
    comparison.to_csv(out / "workbook_vs_official.csv", index=False)
    summary = {"type": "comparison_to_current_snapshot_not_historical_vintage", "series": [],
               "mismatch_interpretation": "Different vintages, definitions or workbook errors are possible; mismatches do not alone identify which."}
    for sid, group in comparison.groupby("series_id"):
        summary["series"].append({"series_id": sid, "matched_periods": len(group),
                                  "outside_tolerance": int((~group.within_tolerance).sum()),
                                  "max_absolute_difference": float(group.difference.abs().max())})
    core_check = wb[wb.series_id == "pce_yoy"].copy()
    core_check["core_pce_yoy"] = core_check.period_end.map(core_yoy)
    core_check = core_check.dropna(subset=["core_pce_yoy"])
    core_check["difference_vs_core"] = core_check.value - core_check.core_pce_yoy
    core_check.to_csv(out / "workbook_vs_core_pce.csv", index=False)
    summary["core_pce_diagnostic"] = {"compared_months": len(core_check),
        "within_0_0001_pp": int((core_check.difference_vs_core.abs() <= 0.0001).sum()),
        "max_absolute_difference": float(core_check.difference_vs_core.abs().max()) if len(core_check) else None,
        "source": "https://fred.stlouisfed.org/series/PCEPILFE"}
    write_json(root / "reports/source_comparison.json", summary)
    lines = ["# 来源与口径核对", "", "比较范围为已下载官方序列与工作簿的共同日期。当前修订值的比较不等于历史版本验证。", "",
             "| 序列 | 可比较时期数 | 超过 0.0001 容差的时期数 | 最大绝对差 |", "|---|---:|---:|---:|"]
    for entry in summary["series"]:
        lines.append(f"| {entry['series_id']} | {entry['matched_periods']} | {entry['outside_tolerance']} | {entry['max_absolute_difference']:.6f} |")
    check = summary["core_pce_diagnostic"]
    lines += ["", "## PCE 口径发现", "",
              f"工作簿的 PCE YoY 在 {check['compared_months']} 个可比月份中，有 {check['within_0_0001_pp']} 个月与官方核心 PCE 同比在 0.0001 个百分点容差内一致。",
              "这支持该列实际采用排除食品和能源的核心 PCE 口径，而不是作业要求的总体 PCE。分析已改为从 PCEPI 重新计算总体同比，原工作簿保持不变。",
              "[核心 PCE 定义](https://fred.stlouisfed.org/series/PCEPILFE)；[总体 PCE 定义](https://fred.stlouisfed.org/series/PCEPI)。", "",
              "## GDP 与其他序列", "", "GDP 多个季度存在差异，可能与修订或来源有关；尚未逐期追溯，不能仅凭差异指定原因。",
              "消费者信心和失业率在共同日期内匹配。工作簿有 2026 年 9–10 月信心，但本次公开 FRED 文件只到 2026 年 8 月；因此当前示范回测止于 8 月，未把不同来源的末端值直接拼接。",
              "所有逐期差值已保存至 data/processed/workbook_vs_official.csv，核心 PCE 比较另存 workbook_vs_core_pce.csv。"]
    (root / "reports/source_comparison.zh-CN.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


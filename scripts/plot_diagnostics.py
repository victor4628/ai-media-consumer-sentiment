"""Optional static research charts; run with an environment containing matplotlib."""
import csv
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
GREEN = "#254C45"


def read(name):
    with (ROOT / "data/processed" / name).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main():
    rows = read("diagnostic_predictions.csv")
    dates = [datetime.fromisoformat(r["period_end"]) for r in rows]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True, gridspec_kw={"height_ratios": [2, 1]}, layout="constrained")
    axes[0].plot(dates, [float(r["actual"]) for r in rows], label="Observed sentiment", color="#252525", lw=1.8)
    axes[0].plot(dates, [float(r["economic_prediction"]) for r in rows], label="Economic-only model", color=GREEN, lw=1.7)
    axes[0].plot(dates, [float(r["persistence_prediction"]) for r in rows], label="Previous-month benchmark", color="#8F9D99", lw=1, alpha=0.85)
    axes[0].set_ylabel("Michigan index points")
    axes[0].legend(loc="lower left", frameon=False, ncol=2)
    axes[0].set_title("Exploratory rolling predictions | Current revised data", loc="left", color=GREEN, weight="bold")
    axes[1].axhline(0, color="#777777", lw=0.7)
    axes[1].plot(dates, [float(r["diagnostic_gap"]) for r in rows], color=GREEN, lw=1.4)
    axes[1].set_ylabel("Observed minus model")
    axes[1].set_title("Diagnostic gap: not evidence of perceptual or media bias", loc="left", fontsize=10)
    for ax in axes:
        ax.grid(axis="y", color="#E6E8E7", lw=0.7)
        ax.set_axisbelow(True)
    fig.supxlabel("Assumed release lags; no historical-vintage backtest. No media data included.", fontsize=9, color="#555555")
    out = ROOT / "reports/figures"
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / "baseline_diagnostic.png", dpi=160)
    plt.close(fig)
    pce = [r for r in read("workbook_vs_official.csv") if r["series_id"] == "pce_yoy"]
    fig, ax = plt.subplots(figsize=(11, 4), layout="constrained")
    dates = [datetime.fromisoformat(r["period_end"]) for r in pce]
    ax.plot(dates, [float(r["value_official"]) for r in pce], label="Headline PCE, recomputed from PCEPI", color=GREEN, lw=1.8)
    ax.plot(dates, [float(r["value_workbook"]) for r in pce], label="Workbook PCE YoY (matches core PCE)", color="#A6763D", lw=1.5)
    ax.set_ylabel("Year-over-year change (%)")
    ax.set_title("Inflation definition check", loc="left", color=GREEN, weight="bold")
    ax.legend(frameon=False, loc="upper left")
    ax.grid(axis="y", color="#E6E8E7")
    fig.supxlabel("Source: supplied workbook and BEA series via FRED; study cutoff 2026-10-16.", fontsize=9, color="#555555")
    fig.savefig(out / "pce_definition_check.png", dpi=160)
    plt.close(fig)
    print("Saved two diagnostic PNG charts")


if __name__ == "__main__":
    main()

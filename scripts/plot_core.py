"""Export standalone figures using measured monthly features and forecasts."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 160, "font.size": 10, "axes.titleweight": "bold"})
folder = ROOT / "reports/figures"
folder.mkdir(exist_ok=True)
forecasts = pd.read_csv(ROOT / "data/processed/core_predictions.csv", parse_dates=["target_month"])
media = pd.read_csv(ROOT / "data/processed/core_monthly_media.csv", parse_dates=["media_month"])
fig, axes = plt.subplots(2, 1, figsize=(10, 7), constrained_layout=True)
timeline = forecasts.set_index("target_month").reindex(pd.date_range(forecasts.target_month.min(), forecasts.target_month.max(), freq="MS"))
for col, name, color in [("actual", "Observed sentiment", "#222222"), ("M1_economic", "M1: economy + memory", "#9caaa5"), ("M2_add_media", "M2: add media", "#254C45"), ("M3_add_household", "M3: add income", "#a37d46")]:
    axes[0].plot(timeline.index, timeline[col], marker=".", label=name, color=color, linewidth=1.4)
axes[0].set_title("Common out-of-sample months | vintage macro inputs", loc="left", color="#254C45")
axes[0].set_ylabel("Consumer sentiment index")
axes[0].legend(ncol=2, fontsize=8)
errors = [(forecasts[c] - forecasts.actual).abs().mean() for c in ["persistence", "M1_economic", "M2_add_media", "M3_add_household"]]
bars = axes[1].barh(["Persistence", "M1", "M2 + media", "M3 + income"], errors, color=["#b3bdb9", "#7c938c", "#254C45", "#a37d46"])
axes[1].bar_label(bars, fmt="%.2f", padding=4)
axes[1].set_xlabel("Mean absolute error (lower is better)")
axes[1].set_xlim(0, max(errors) * 1.2)
axes[1].set_title("Same months and training eligibility for all models", loc="left", color="#254C45")
fig.savefig(folder / "core_model_comparison.png")
plt.close(fig)
fig, axes = plt.subplots(2, 1, figsize=(10, 6), constrained_layout=True, sharex=True)
axes[0].plot(media.media_month, media.news_tone, label="News: equal observed-outlet weight", color="#254C45", marker=".")
axes[0].plot(media.media_month, media.twitter_tone, label="Twitter: sampled posts", color="#a37d46", marker=".")
axes[0].axhline(0, color="#aaaaaa", linewidth=.6)
axes[0].set_ylim(-1.1, 1.1)
axes[0].set_ylabel("Mean tone (-1 to +1)")
axes[0].set_title("Sparse sampled media | missing months remain missing", loc="left", color="#254C45")
axes[0].legend(fontsize=8)
axes[1].plot(media.media_month, media.news_scored_n, label="Scored headlines", color="#254C45")
axes[1].plot(media.media_month, media.twitter_scored_n, label="Scored tweets", color="#a37d46")
axes[1].set_ylabel("Eligible coded items")
axes[1].set_xlabel("Publication month (UTC)")
axes[1].legend(fontsize=8)
fig.savefig(folder / "core_media_coverage.png")
plt.close(fig)
print("Exported reports/figures/core_model_comparison.png and core_media_coverage.png")

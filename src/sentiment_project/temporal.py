"""Strict information-set helpers: missing release/vintage dates fail closed."""
from __future__ import annotations

import pandas as pd


def snapshot_as_of(observations, cutoff):
    required = {"series_id", "period_end", "value", "release_date", "vintage_date", "source_url"}
    missing = required.difference(observations.columns)
    if missing:
        raise ValueError(f"Missing required fields: {sorted(missing)}")
    frame = observations.copy()
    for col in ["period_end", "release_date", "vintage_date"]:
        frame[col] = pd.to_datetime(frame[col], errors="raise")
        if frame[col].isna().any():
            raise ValueError(f"Unknown {col}: cannot perform a strict real-time backtest")
    if frame.source_url.isna().any() or frame.source_url.eq("").any():
        raise ValueError("Missing source evidence")
    if frame.duplicated(["series_id", "period_end", "vintage_date"]).any():
        raise ValueError("Ambiguous duplicate vintage")
    cutoff = pd.Timestamp(cutoff)
    frame = frame[(frame.release_date <= cutoff) & (frame.vintage_date <= cutoff) & (frame.period_end <= cutoff)]
    return frame.sort_values("vintage_date").drop_duplicates(["series_id", "period_end"], keep="last")


def pce_yoy_as_of(observations, cutoff, period):
    frame = snapshot_as_of(observations, cutoff)
    frame = frame[frame.series_id == "pce_index"].set_index("period_end")
    current = pd.Period(period, freq="M").end_time.normalize()
    previous = (pd.Period(period, freq="M") - 12).end_time.normalize()
    if current not in frame.index or previous not in frame.index:
        return None
    base = float(frame.loc[previous, "value"])
    if base <= 0:
        raise ValueError("Invalid PCE denominator")
    return 100 * (float(frame.loc[current, "value"]) / base - 1)


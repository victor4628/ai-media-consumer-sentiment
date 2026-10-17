"""ALFRED snapshots: as-of availability, not invented release dates."""
import csv
import io
import math
from datetime import date


def parse_snapshot(data, series, vintage):
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    expected = series + "_" + vintage.replace("-", "")
    if reader.fieldnames != ["observation_date", expected]:
        raise ValueError(f"ALFRED vintage/header mismatch for {series} {vintage}")
    values = {}
    for row in reader:
        period = row["observation_date"]
        date.fromisoformat(period)
        if period > vintage:
            raise ValueError("Snapshot contains future observation period")
        if period in values:
            raise ValueError("Duplicate observation period")
        if row[expected] in ["", "."]:
            continue
        value = float(row[expected])
        if not math.isfinite(value):
            raise ValueError("Nonfinite observation")
        values[period] = value
    if not values:
        raise ValueError("Empty ALFRED snapshot")
    return values


def latest_value(values, cutoff):
    eligible = [p for p in values if p < cutoff]
    if not eligible:
        raise ValueError("No released observation before forecast target")
    period = max(eligible)
    return period, values[period]


def annual_change(values, cutoff):
    period, value = latest_value(values, cutoff)
    prior = str(int(period[:4]) - 1) + period[4:]
    if prior not in values or values[prior] == 0:
        raise ValueError("Exact calendar year comparison missing")
    return period, (value / values[prior] - 1) * 100


def quarterly_annualized(values, cutoff):
    period, value = latest_value(values, cutoff)
    year, month = int(period[:4]), int(period[5:7])
    if month not in [1, 4, 7, 10]:
        raise ValueError("GDP observation is not a quarter start")
    prior = f"{year - (month == 1):04d}-{(month - 4) % 12 + 1:02d}-01"
    if prior not in values or values[prior] <= 0 or value <= 0:
        raise ValueError("Previous-quarter GDP unavailable")
    return period, ((value / values[prior]) ** 4 - 1) * 100

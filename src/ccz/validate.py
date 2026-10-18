"""
Data checks for the hourly table.
Each check stops the run with a plain message if the data is wrong.
"""

import pandas as pd

from ccz import config


class DataCheckError(Exception):
    """Raised when the data fails a check. The message says what and where."""


def required_columns():
    """Every column the models need, without repeats."""
    cols = ["time_utc", config.NEIGHBOUR_COLUMN, "hour_london", "dayofweek_london"]
    cols += list(config.TARGET_COLUMNS.values()) + list(config.WEATHER_INPUTS)
    return list(dict.fromkeys(cols))


def check_hourly(df):
    """Run every check on the hourly table. Returns a list of the checks passed."""
    passed = []

    if df.empty:
        raise DataCheckError("The hourly table is empty.")
    passed.append(f"not empty ({len(df)} rows)")

    missing = [c for c in required_columns() if c not in df.columns]
    if missing:
        raise DataCheckError(f"Missing columns: {missing}")
    passed.append("all required columns present")

    times = pd.to_datetime(df["time_utc"], utc=True)
    if times.duplicated().any():
        raise DataCheckError(f"{times.duplicated().sum()} repeated hours in time_utc.")
    steps = times.diff().iloc[1:]
    breaks = steps[steps != pd.Timedelta(hours=1)]
    if len(breaks):
        raise DataCheckError(f"Hours are not one apart. First break at {times[breaks.index[0]]}.")
    start = pd.Timestamp(config.MASTER_START, tz="UTC")
    end = pd.Timestamp(config.MASTER_END, tz="UTC")
    if times.iloc[0] != start or times.iloc[-1] != end:
        raise DataCheckError(f"Table runs {times.iloc[0]} to {times.iloc[-1]}, expected {start} to {end}.")
    passed.append("one row per hour, full calendar")

    for target, col in config.TARGET_COLUMNS.items():
        share = df[col].isna().mean()
        if share > config.MAX_MISSING_SHARE:
            raise DataCheckError(f"{col} ({target}) is {share:.1%} missing, limit {config.MAX_MISSING_SHARE:.0%}.")
    passed.append("targets missing below limit")

    for col, (low, high) in config.VALID_RANGES.items():
        if col not in df.columns:
            continue
        bad = df[(df[col] < low) | (df[col] > high)]
        if len(bad):
            raise DataCheckError(
                f"{col}: {len(bad)} values outside {low} to {high}, "
                f"for example {bad[col].iloc[0]} at {bad['time_utc'].iloc[0]}."
            )
    passed.append("all values inside physical limits")

    return passed
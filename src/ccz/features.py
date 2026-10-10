# Builds the answer columns the models will learn to predict.
# For each target and each horizon h, the answer is the value h hours AFTER the row's own hour.
import pandas as pd
from ccz import config


def add_targets(hourly):
    gaps = hourly["time_utc"].diff().dropna()
    if not (gaps == pd.Timedelta(hours=1)).all():
        raise ValueError("The table is not one row per hour, so shifting by rows would be wrong")

    out = hourly.copy()
    for name, column in config.TARGET_COLUMNS.items():
        for h in config.HORIZONS:
            out[f"y_{name}_{h}h"] = out[column].shift(-h)
    return out
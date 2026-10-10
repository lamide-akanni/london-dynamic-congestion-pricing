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

def training_rows(table, name, h):
    train_end = pd.Timestamp(config.TRAIN_END, tz="UTC")
    answer_time = table["time_utc"] + pd.Timedelta(hours=h)
    keep = (table["time_utc"] <= train_end) & (answer_time <= train_end)
    rows = table.loc[keep]
    return rows[rows[f"y_{name}_{h}h"].notna()]
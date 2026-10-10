# Builds the answer columns the models will learn to predict.
# For each target and each horizon h, the answer is the value h hours AFTER the row's own hour.
import pandas as pd
import numpy as np  
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
def training_rows(table, name, h, train_end=None):
    train_end = pd.Timestamp(train_end or config.TRAIN_END, tz="UTC")
    answer_time = table["time_utc"] + pd.Timedelta(hours=h)
    keep = (table["time_utc"] <= train_end) & (answer_time <= train_end)
    rows = table.loc[keep]
    return rows[rows[f"y_{name}_{h}h"].notna()]

def month_rows(table, name, h, month):
    rows = table.loc[table["time_utc"].dt.strftime("%Y-%m") == month]
    return rows[rows[f"y_{name}_{h}h"].notna()]


def add_lags(table):
    out = table.copy()
    for column in config.TARGET_COLUMNS.values():
        for k in config.LAG_HOURS:
            out[f"{column}_lag{k}h"] = out[column].shift(k)
    return out


def add_clock(table):
    out = table.copy()
    local = out["time_utc"].dt.tz_convert(config.TIMEZONE)
    out["is_weekend"] = (out["dayofweek_london"] >= 5).astype(int)
    out["hour_sin"] = np.sin(2 * np.pi * out["hour_london"] / 24)
    out["hour_cos"] = np.cos(2 * np.pi * out["hour_london"] / 24)
    out["is_bank_holiday"] = local.dt.strftime("%Y-%m-%d").isin(config.BANK_HOLIDAYS).astype(int)
    return out


def build_inputs(table):
    return add_clock(add_lags(table))


def input_columns():
    now = list(config.TARGET_COLUMNS.values())
    lags = [f"{c}_lag{k}h" for c in now for k in config.LAG_HOURS]
    clock = ["hour_sin", "hour_cos", "is_weekend", "is_bank_holiday"]
    return now + lags + clock + config.WEATHER_INPUTS

def test_rows(table, name, h):
    test_start = pd.Timestamp(config.TEST_START, tz="UTC")
    rows = table.loc[table["time_utc"] >= test_start]
    return rows[rows[f"y_{name}_{h}h"].notna()]
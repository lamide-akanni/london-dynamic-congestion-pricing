# Fit, save, load and use the final models.
# One saved file per target and horizon. Each file holds the fitted model, the settings it was
# built with, the input columns it expects, and a small "rule table" cut from the training rows.
# The weekly profile is learned from the training rows, so it has to travel with the model.
import joblib
import numpy as np
import pandas as pd
from ccz import baselines, config, features, models


def models_dir():
    # <project>/models, next to the reports folder
    return config.TABLES_DIR.parents[1] / "models"


def file_name(name, h):
    return f"{name}_{h}h.joblib"


def fit_bundle(table, name, h, pick, train_end):
    y = f"y_{name}_{h}h"
    inputs = features.input_columns()
    train = features.training_rows(table, name, h, train_end=train_end)
    model = models.make_model(pick["kind"], pick["params"])
    if pick["mode"] == "correct":
        base_train = baselines.base_guess(train, train, name, h)
        fit = base_train.notna()
        model.fit(train.loc[fit, inputs], train.loc[fit, y] - base_train[fit])
    else:
        model.fit(train[inputs], train[y])
    return {
        "target": name,
        "hours_ahead": h,
        "kind": pick["kind"],
        "mode": pick["mode"],
        "params": pick["params"],
        "inputs": inputs,
        "trained_through": str(train_end),
        "rows": int(len(train)),
        "model": model,
        "rule_table": train[["dayofweek_london", "hour_london", y]].copy(),
    }


def save_bundle(bundle, directory=None):
    directory = models_dir() if directory is None else directory
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / file_name(bundle["target"], bundle["hours_ahead"])
    joblib.dump(bundle, path, compress=3)
    return path


def load_bundle(name, h, directory=None):
    directory = models_dir() if directory is None else directory
    path = directory / file_name(name, h)
    if not path.exists():
        raise FileNotFoundError(f"Missing model file {path}. Run scripts/25_train_final.py first.")
    return joblib.load(path)


def forecast(bundle, rows):
    # rows: the table made by features.build_inputs. Returns the forecast for h hours after each row,
    # clipped to the physical range (congestion 0 to 100, pollutants 0 or more).
    name, h = bundle["target"], bundle["hours_ahead"]
    needed = bundle["inputs"] + ["dayofweek_london", "hour_london"]
    missing = [column for column in needed if column not in rows.columns]
    if missing:
        raise ValueError(f"Missing input columns for {name} {h}h: {missing}")
    guess = np.asarray(bundle["model"].predict(rows[bundle["inputs"]]), dtype=float)
    if bundle["mode"] == "correct":
        guess = guess + baselines.base_guess(bundle["rule_table"], rows, name, h).to_numpy()
    low, high = (0.0, 100.0) if name == "congestion" else (0.0, np.inf)
    return pd.Series(np.clip(guess, low, high), index=rows.index)


def forecast_table(hourly, n_last=24, directory=None):
    # hourly: the cleaned hourly table, one row per hour, newest last.
    # Returns forecasts made at each of the last n_last hours, one row per target and horizon.
    table = features.build_inputs(hourly).tail(n_last)
    pieces = []
    for name in config.TARGET_COLUMNS:
        for h in config.HORIZONS:
            bundle = load_bundle(name, h, directory)
            part = table[["time_utc"]].rename(columns={"time_utc": "origin_utc"}).copy()
            part["target"] = name
            part["hours_ahead"] = h
            part["forecast_for_utc"] = part["origin_utc"] + pd.Timedelta(hours=h)
            part["forecast"] = forecast(bundle, table)
            pieces.append(part)
    return pd.concat(pieces, ignore_index=True)
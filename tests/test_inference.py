import numpy as np
import pandas as pd
import pytest
from ccz import config, features, inference

DIRECT = {"kind": "ridge", "mode": "direct", "params": {"alpha": 1.0}}
CORRECT = {"kind": "ridge", "mode": "correct", "params": {"alpha": 1.0}}


def small_table(n=600):
    rng = np.random.default_rng(0)
    times = pd.date_range("2025-01-01", periods=n, freq="h", tz="UTC")
    local = times.tz_convert(config.TIMEZONE)
    data = {
        "time_utc": times,
        "hour_london": local.hour.to_numpy(),
        "dayofweek_london": local.dayofweek.to_numpy(),
    }
    raw = set(config.TARGET_COLUMNS.values()) | set(config.WEATHER_INPUTS) | {config.NEIGHBOUR_COLUMN}
    for column in raw:
        data[column] = rng.uniform(10, 90, n)
    return features.build_inputs(features.add_targets(pd.DataFrame(data)))


def end_of(table):
    return table["time_utc"].max().strftime("%Y-%m-%d %H:%M")


def test_save_and_load_give_the_same_forecast(tmp_path):
    table = small_table()
    bundle = inference.fit_bundle(table, "congestion", 1, DIRECT, end_of(table))
    inference.save_bundle(bundle, tmp_path)
    loaded = inference.load_bundle("congestion", 1, tmp_path)
    rows = table.tail(20)
    assert inference.forecast(loaded, rows).to_numpy() == pytest.approx(inference.forecast(bundle, rows).to_numpy())


def test_rule_table_travels_with_the_model(tmp_path):
    table = small_table()
    bundle = inference.fit_bundle(table, "congestion", 3, CORRECT, end_of(table))
    inference.save_bundle(bundle, tmp_path)
    loaded = inference.load_bundle("congestion", 3, tmp_path)
    rows = table.tail(20)
    assert inference.forecast(loaded, rows).to_numpy() == pytest.approx(inference.forecast(bundle, rows).to_numpy())


def test_forecast_is_clipped_to_the_physical_range():
    class Fixed:
        def predict(self, X):
            return np.array([-50.0, 150.0, 30.0])[: len(X)]

    table = small_table()
    bundle = inference.fit_bundle(table, "congestion", 1, DIRECT, end_of(table))
    bundle["model"] = Fixed()
    out = inference.forecast(bundle, table.tail(3)).to_numpy()
    assert out[0] == 0.0
    assert out[1] == 100.0
    assert out[2] == 30.0


def test_missing_column_gives_a_clear_error():
    table = small_table()
    bundle = inference.fit_bundle(table, "congestion", 1, DIRECT, end_of(table))
    with pytest.raises(ValueError, match="hour_sin"):
        inference.forecast(bundle, table.tail(5).drop(columns=["hour_sin"]))


def test_missing_model_file_gives_a_clear_error(tmp_path):
    with pytest.raises(FileNotFoundError, match="25_train_final"):
        inference.load_bundle("congestion", 1, tmp_path)
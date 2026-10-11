# Tests for the answer columns and input columns built in src/ccz/features.py
import pandas as pd
import pytest
from ccz import config, features


def make_table(n=12):
    # A made-up table: one row per hour, and every value equals its row number.
    times = pd.date_range("2025-04-30 12:00", periods=n, freq="h", tz="UTC")
    table = pd.DataFrame({"time_utc": times})
    for column in config.TARGET_COLUMNS.values():
        table[column] = range(n)
    return table


def test_answer_is_the_value_h_hours_later():
    table = features.add_targets(make_table())
    for name in config.TARGET_COLUMNS:
        for h in config.HORIZONS:
            answer = table[f"y_{name}_{h}h"]
            assert answer.iloc[0] == h
            assert answer.iloc[-h:].isna().all()


def test_missing_hours_stop_the_code():
    table = make_table().drop(index=5)
    with pytest.raises(ValueError):
        features.add_targets(table)


def test_training_rows_never_use_an_answer_after_the_training_end():
    table = features.add_targets(make_table(24))
    train_end = pd.Timestamp(config.TRAIN_END, tz="UTC")
    for name in config.TARGET_COLUMNS:
        for h in config.HORIZONS:
            rows = features.training_rows(table, name, h)
            assert len(rows) > 0
            answer_time = rows["time_utc"] + pd.Timedelta(hours=h)
            assert (answer_time <= train_end).all()


def test_lag_columns_look_backwards():
    table = features.add_lags(make_table(30))
    for column in config.TARGET_COLUMNS.values():
        for k in config.LAG_HOURS:
            lagged = table[f"{column}_lag{k}h"]
            assert lagged.iloc[:k].isna().all()
            assert lagged.iloc[k] == 0
            assert lagged.iloc[-1] == (len(table) - 1) - k


def make_input_table(n=60):
    table = make_table(n)
    local = table["time_utc"].dt.tz_convert(config.TIMEZONE)
    table["hour_london"] = local.dt.hour
    table["dayofweek_london"] = local.dt.dayofweek
    for column in config.WEATHER_INPUTS:
        table[column] = range(n)
    table[config.NEIGHBOUR_COLUMN] = range(n)
    return table


def test_clock_columns_use_london_time():
    times = pd.date_range("2025-04-18 00:00", periods=24, freq="h", tz="UTC")
    table = pd.DataFrame({"time_utc": times})
    local = table["time_utc"].dt.tz_convert(config.TIMEZONE)
    table["hour_london"] = local.dt.hour
    table["dayofweek_london"] = local.dt.dayofweek
    out = features.add_clock(table)
    assert out["is_bank_holiday"].iloc[0] == 1
    assert out["is_bank_holiday"].iloc[-1] == 0
    assert out["is_weekend"].iloc[0] == 0
    assert out["is_weekend"].iloc[-1] == 1


def test_inputs_at_hour_t_do_not_depend_on_later_hours():
    groups = ("recent", "neighbour")
    table = make_input_table(60)
    cut = 40
    changed = table.copy()
    later = changed.index >= cut + 1
    source = list(config.TARGET_COLUMNS.values()) + config.WEATHER_INPUTS + [config.NEIGHBOUR_COLUMN]
    for column in source:
        changed.loc[later, column] = 999
    a = features.build_inputs(table)[features.input_columns(groups)]
    b = features.build_inputs(changed)[features.input_columns(groups)]
    pd.testing.assert_frame_equal(a.iloc[:cut + 1], b.iloc[:cut + 1])


def test_default_inputs_are_still_the_original_32():
    assert len(features.input_columns()) == 32


def test_test_rows_start_at_the_test_start_and_have_answers():
    table = features.add_targets(make_table(48))
    rows = features.test_rows(table, "no2", 3)
    assert rows["time_utc"].min() >= pd.Timestamp(config.TEST_START, tz="UTC")
    assert rows["y_no2_3h"].notna().all()
    assert len(rows) == 33


def test_training_rows_accept_an_earlier_training_end():
    table = features.add_targets(make_table(48))
    rows = features.training_rows(table, "no2", 3, train_end="2025-05-01 05:00")
    assert len(rows) > 0
    answer_time = rows["time_utc"] + pd.Timedelta(hours=3)
    assert answer_time.max() <= pd.Timestamp("2025-05-01 05:00", tz="UTC")
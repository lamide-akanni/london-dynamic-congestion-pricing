# Tests for the answer columns built in src/ccz/features.py
import pandas as pd
import pytest
from ccz import config, features
# Tests for the answer columns built in src/ccz/features.py
import pandas as pd
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
import pandas as pd
import pytest

from ccz import config
from ccz.validate import DataCheckError, check_hourly, required_columns


def good_table():
    """A small clean table with every needed column, no real data."""
    times = pd.date_range(config.MASTER_START, config.MASTER_END, freq="h", tz="UTC")
    df = pd.DataFrame({"time_utc": times})
    for col in required_columns()[1:]:
        df[col] = 1.0
    df["surface_pressure"] = 1000.0
    return df


def test_clean_table_passes():
    assert len(check_hourly(good_table())) == 5


def test_empty_table_fails():
    with pytest.raises(DataCheckError, match="empty"):
        check_hourly(good_table().iloc[0:0])


def test_missing_column_fails():
    with pytest.raises(DataCheckError, match="Missing columns"):
        check_hourly(good_table().drop(columns="wm6_no2"))


def test_gap_in_hours_fails():
    df = good_table().drop(index=100).reset_index(drop=True)
    with pytest.raises(DataCheckError, match="not one apart"):
        check_hourly(df)


def test_too_many_missing_fails():
    df = good_table()
    df.loc[:1000, "wm6_pm25"] = None
    with pytest.raises(DataCheckError, match="missing"):
        check_hourly(df)


def test_value_out_of_range_fails():
    df = good_table()
    df.loc[7, "cloud_cover"] = 150
    with pytest.raises(DataCheckError, match="cloud_cover"):
        check_hourly(df)
#TRAINING MONTHS ONLY (January to April).

import pandas as pd

from ccz import config


def section(title):
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")


hourly = pd.read_csv(config.HOURLY_FILE, parse_dates=["time_utc"])

# The line that decides what we are looking at.
train_end = pd.Timestamp(config.TRAIN_END, tz="UTC")
train = hourly[hourly["time_utc"] <= train_end].copy()

section("1. The slice")
print(f"Training rows: {len(train)} (expected 2880 = 120 days x 24 hours)")
print(f"From {train['time_utc'].min()} to {train['time_utc'].max()}")
if len(train) != 2880:
    raise SystemExit("CHECK FAILED: the training slice is not 2880 hours")

central = train["congestion_central"]

section("2. Westminster congestion by London hour of day (training months)")
by_hour = train.groupby("hour_london")["congestion_central"].agg(
    median="median",
    mean="mean",
    share_zero=lambda s: 100 * (s == 0).mean(),
    share_60_or_more=lambda s: 100 * (s >= 60).mean(),
)
print(by_hour.round(1).to_string())

section("3. Weekday against weekend, Westminster (training months)")
train["is_weekend"] = train["dayofweek_london"] >= 5
print(train.groupby("is_weekend")["congestion_central"].describe().round(1).to_string())

city = train["congestion_check"]

section("4. Share of hours at or above each level (training months)")
for level in [50, 60, 70]:
    print(f"Westminster >= {level}: {100 * (central >= level).mean():.1f}% of hours"
          f"   |   City of London >= {level}: {100 * (city >= level).mean():.1f}%")
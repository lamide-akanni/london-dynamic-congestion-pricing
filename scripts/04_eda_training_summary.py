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

    section("5. Does City of London follow Westminster? (training months)")
print(f"Correlation of the two hourly series: {central.corr(city):.2f}")

daily_shape = train.groupby("hour_london")[["congestion_central", "congestion_check"]].mean()
print(f"Correlation of their average daily shapes: "
      f"{daily_shape['congestion_central'].corr(daily_shape['congestion_check']):.2f}")

print(f"Hours above 100: Westminster {(central > 100).sum()}, City of London {(city > 100).sum()}")

section("6. Do the two main air sites agree with each other? (training months)")
print(f"NO2   WM6 vs CE2: {train['wm6_no2'].corr(train['ce2_no2']):.2f}")
print(f"PM2.5 WM6 vs CE2: {train['wm6_pm25'].corr(train['ce2_pm25']):.2f}")
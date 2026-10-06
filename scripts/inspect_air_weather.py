"""Brick 14: look at the raw air quality and weather files and print what is in them.

This script only reads. It changes nothing on disk.
"""

import pandas as pd

from ccz import config

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", None)

FULL_HOURS = pd.date_range(config.DATA_START, config.DATA_END + " 23:00", freq="h")

# ======================= AIR QUALITY =======================
air = pd.read_csv(config.LAQN_FILE)
air["time_utc"] = pd.to_datetime(air["time_utc"])

print("AIR QUALITY: ROWS AND COLUMNS")
print(air.shape)
print()
print("COLUMN TYPES")
print(air.dtypes)
print()
print("FIRST 5 ROWS")
print(air.head())
print()
print("DUPLICATE ROWS (same site, species and time)")
print(air.duplicated(subset=["site", "species", "time_utc"]).sum())
print()
print("TIME RANGE")
print(air["time_utc"].min(), "to", air["time_utc"].max())
print()

summary_rows = []
monthly = {}
for site in config.AIR_SITES:
    for species in config.AIR_SPECIES:
        part = air[(air["site"] == site) & (air["species"] == species)]
        # For this check only, keep the first reading if a time appears twice.
        series = part.drop_duplicates("time_utc").set_index("time_utc")["value"].reindex(FULL_HOURS)

        missing = series.isna()
        runs = (missing != missing.shift()).cumsum()
        longest_gap = int(missing.groupby(runs).sum().max())

        summary_rows.append(
            {
                "site": site,
                "species": species,
                "hours_with_reading": int(series.notna().sum()),
                "share_%": round(100 * series.notna().mean(), 1),
                "first_reading": series.first_valid_index(),
                "last_reading": series.last_valid_index(),
                "min": series.min(),
                "mean": round(series.mean(), 1),
                "max": series.max(),
                "negatives": int((series < 0).sum()),
                "longest_gap_hours": longest_gap,
            }
        )
        monthly[f"{site} {species}"] = (
            series.notna().groupby(series.index.to_period("M")).mean() * 100
        ).round(0)

print(f"SUMMARY PER SITE AND POLLUTANT (out of {len(FULL_HOURS)} hours)")
print(pd.DataFrame(summary_rows).to_string(index=False))
print()
print("SHARE OF HOURS WITH A READING, BY MONTH (%)")
print(pd.DataFrame(monthly).T)
print()

# ======================= WEATHER =======================
weather = pd.read_csv(config.WEATHER_FILE)
weather["time_utc"] = pd.to_datetime(weather["time_utc"])

print("WEATHER: ROWS AND COLUMNS")
print(weather.shape)
print()
print("COLUMN TYPES")
print(weather.dtypes)
print()
print("FIRST 5 ROWS")
print(weather.head())
print()
print("MISSING VALUES PER COLUMN")
print(weather.isna().sum())
print()
print("DUPLICATE TIMES")
print(weather["time_utc"].duplicated().sum())
print()
print("TIME RANGE")
print(weather["time_utc"].min(), "to", weather["time_utc"].max())
print()
steps = weather["time_utc"].diff().dropna()
print("STEPS THAT ARE NOT EXACTLY 1 HOUR")
print((steps != pd.Timedelta(hours=1)).sum())
print()
print("SUMMARY STATISTICS")
print(weather.drop(columns="time_utc").describe().T)
# How much of the kerbside pollution is traffic? Kerbside site WM6 against background site BL0.
# Uses the raw LAQN file. Training months only, because the share is a model setting.
# Negative readings are set to 0, as in the cleaning rules.
import json
from pathlib import Path

import pandas as pd
from ccz import config

raw_file = Path(config.HOURLY_FILE).parent.parent / "raw" / "laqn_2025H1.csv"
raw = pd.read_csv(raw_file)
raw["time"] = pd.to_datetime(raw["time_utc"], utc=True)
raw["species"] = raw["species"].str.upper().str.replace(".", "", regex=False)
print("Pollutants in file:", sorted(raw["species"].unique()), "| Sites:", sorted(raw["site"].unique()))

cut = pd.Timestamp(config.TRAIN_END, tz="UTC")
result, details = {}, {}

for pollutant, label in [("no2", "NO2"), ("pm25", "PM25")]:
    part = raw[(raw["species"] == label) & (raw["time"] <= cut)]
    wide = part.pivot_table(index="time", columns="site", values="value", aggfunc="mean").clip(lower=0)
    if "BL0" not in wide.columns or "WM6" not in wide.columns:
        print(f"\n{pollutant}: WM6 or BL0 is missing, no share can be measured.")
        result[pollutant] = None
        continue

    both = wide[["WM6", "BL0"]].dropna()
    kerb, back = both["WM6"], both["BL0"]
    share = 1 - back.mean() / kerb.mean()

    zeros = int((back == 0).sum())
    nonzero = both[both["BL0"] > 0]
    share_nonzero = 1 - nonzero["BL0"].mean() / nonzero["WM6"].mean()

    half = len(both) // 2
    first, second = both.iloc[:half], both.iloc[half:]
    share_first = 1 - first["BL0"].mean() / first["WM6"].mean()
    share_second = 1 - second["BL0"].mean() / second["WM6"].mean()

    print(f"\n{pollutant.upper()}")
    print(f"  Hours with both sites: {len(both)} ({both.index.min():%d %b} to {both.index.max():%d %b})")
    print(f"  Kerbside WM6 average {kerb.mean():.1f}, background BL0 average {back.mean():.1f}")
    print(f"  Traffic share: {share:.2f}")
    print(f"  BL0 zero readings: {zeros} hours. Share without them: {share_nonzero:.2f}")
    print(f"  Share in first half of the overlap {share_first:.2f}, second half {share_second:.2f}")

    result[pollutant] = None if share <= 0 else round(float(share), 3)
    if share <= 0:
        print("  Background is as high as the kerbside, so the traffic share is treated as 0.")
    details[pollutant] = {
        "hours": len(both), "share": round(float(share), 3),
        "share_without_zero_hours": round(float(share_nonzero), 3),
        "share_first_half": round(float(share_first), 3),
        "share_second_half": round(float(share_second), 3),
        "bl0_zero_hours": zeros,
    }

config.TABLES_DIR.mkdir(parents=True, exist_ok=True)
result["details"] = details
with open(config.TABLES_DIR / "traffic_shares.json", "w") as f:
    json.dump(result, f, indent=2)
print("\nSaved reports/tables/traffic_shares.json")
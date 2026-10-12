# Pricing simulation, part 1: the decision table.
# One row per weekday (May and June), per block, per hour that gets a price.
# It holds what really happened and what each forecaster said when the prices were published.
# Nothing is refitted here. The model forecasts come from the saved hold-out predictions.
import pandas as pd
from ccz import baselines, config, features

TARGET_COL = {"congestion": "congestion_central", "no2": "wm6_no2", "pm25": "wm6_pm25"}
LIMITS = {"congestion": (0, 100), "no2": (0, None), "pm25": (0, None)}
HOURS_AHEAD = [1, 2, 3, 4, 5, 6]

hourly = pd.read_csv(config.HOURLY_FILE, parse_dates=["time_utc"])
table = features.build_inputs(features.add_targets(hourly))
table = table.sort_values("time_utc").reset_index(drop=True)
assert pd.to_datetime(table["time_utc"], utc=True).diff().dropna().eq(pd.Timedelta(hours=1)).all()

# answers for every hour ahead, 1 to 6 (the table so far only has 1, 3 and 6)
for name, col in TARGET_COL.items():
    for k in HOURS_AHEAD:
        column = f"y_{name}_{k}h"
        if column not in table.columns:
            table[column] = table[col].shift(-k)

local = pd.to_datetime(table["time_utc"], utc=True).dt.tz_convert("Europe/London")
table["local_date"] = local.dt.strftime("%Y-%m-%d")
table["origin_hour"] = local.dt.hour
table["weekday"] = local.dt.dayofweek

# the moments when prices are decided: weekdays in the test months, no bank holidays
parts = []
for block, hours in config.PRICING_BLOCKS.items():
    pick = table[
        (table["origin_hour"] == hours[0] - 1)
        & (table["weekday"] < 5)
        & (table["local_date"] >= config.TEST_START[:10])
        & (~table["local_date"].isin(config.BANK_HOLIDAYS))
    ]
    parts.append(pick.assign(block=block))
origins = pd.concat(parts)

# model forecasts: saved hold-out predictions at 1, 3, 6 hours, straight-line fill for 2, 4, 5
pred = pd.read_csv(config.TABLES_DIR / "holdout_predictions.csv")
pred["time_utc"] = pd.to_datetime(pred["time_utc"], utc=True)
model_table = {}
for name in TARGET_COL:
    p = pred[pred["target"] == name].pivot(index="time_utc", columns="hours_ahead", values="model")
    full = pd.DataFrame(index=p.index)
    full[1], full[3], full[6] = p[1], p[3], p[6]
    full[2] = (p[1] + p[3]) / 2
    full[4] = p[3] + (p[6] - p[3]) / 3
    full[5] = p[3] + 2 * (p[6] - p[3]) / 3
    low, high = LIMITS[name]
    model_table[name] = full.clip(lower=low, upper=high)

frames = []
for k in HOURS_AHEAD:
    part = origins[["block", "local_date", "origin_hour", "time_utc"]].copy()
    part["k"] = k
    part["price_hour"] = part["origin_hour"] + k
    keep = [h in config.PRICING_BLOCKS[b] for h, b in zip(part["price_hour"], part["block"])]
    part = part[keep]
    rows = origins.loc[part.index]
    stamps = pd.DatetimeIndex(pd.to_datetime(part["time_utc"], utc=True))
    for name in TARGET_COL:
        train = features.training_rows(table, name, k)
        simple = baselines.baseline_guesses(train, rows, name, k)
        part[f"{name}_actual"] = rows[f"y_{name}_{k}h"]
        part[f"{name}_persistence"] = simple["persistence"]
        part[f"{name}_profile"] = simple["weekly_profile"]
        part[f"{name}_model"] = model_table[name].reindex(stamps)[k].to_numpy()
    frames.append(part)

decision = pd.concat(frames, ignore_index=True)

# keep only blocks where every hour and every forecast exists
need = [c for c in decision.columns if c.endswith(("_actual", "_persistence", "_profile", "_model"))]
decision["complete"] = decision[need].notna().all(axis=1)
block_ok = decision.groupby(["local_date", "block"])["complete"].transform("all")
kept = decision[block_ok].drop(columns="complete").sort_values(["local_date", "block", "k"])

total = decision.groupby(["local_date", "block"]).ngroups
good = kept.groupby(["local_date", "block"]).ngroups
print(f"Price blocks found: {total}. Kept (nothing missing): {good}. Dropped: {total - good}.")
print(kept.groupby("block")["local_date"].nunique().to_string())

print("\nAverage real congestion by the hour being priced (London time):")
print(kept.groupby("price_hour")["congestion_actual"].mean().round(1).to_string())

print("\nAverage miss on these decision hours (MAE):")
summary = []
for name in TARGET_COL:
    for k in HOURS_AHEAD:
        s = kept[kept["k"] == k]
        row = {"target": name, "hours_ahead": k, "rows": len(s)}
        for source in ["model", "profile", "persistence"]:
            row[source] = (s[f"{name}_{source}"] - s[f"{name}_actual"]).abs().mean()
        summary.append(row)
print(pd.DataFrame(summary).round(2).to_string(index=False))

config.TABLES_DIR.mkdir(parents=True, exist_ok=True)
kept.to_csv(config.TABLES_DIR / "pricing_inputs.csv", index=False)
print("\nSaved reports/tables/pricing_inputs.csv")
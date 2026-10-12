# Where does the model go wrong? Reads the saved May and June predictions only.
# Everything is grouped by the hour the answer refers to (forecast time + hours ahead), in London time.
import numpy as np
import pandas as pd
from ccz import config

pd.options.display.width = 220
pd.options.display.max_columns = 30

pred = pd.read_csv(config.TABLES_DIR / "holdout_predictions.csv")
hourly = pd.read_csv(config.HOURLY_FILE)
hourly["time"] = pd.to_datetime(hourly["time_utc"], utc=True)

pred["target_time"] = pd.to_datetime(pred["time_utc"], utc=True) + pd.to_timedelta(pred["hours_ahead"], unit="h")
local = pred["target_time"].dt.tz_convert("Europe/London")

pred["model_err"] = pred["model"] - pred["actual"]
pred["base_err"] = pred["best_baseline"] - pred["actual"]
pred["model_abs"] = pred["model_err"].abs()
pred["base_abs"] = pred["base_err"].abs()
pred["key"] = pred["target"].str[:4] + "_" + pred["hours_ahead"].astype(str) + "h"

# groupings
pred["hour_of_day"] = pd.cut(
    local.dt.hour, bins=[-1, 5, 9, 15, 19, 23],
    labels=["00-05 night", "06-09 morning", "10-15 midday", "16-19 evening", "20-23 late"],
)
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
pred["weekday"] = pd.Categorical(local.dt.day_name(), categories=days, ordered=True)
pred["month"] = local.dt.strftime("%Y-%m")
pred["bank_holiday"] = np.where(local.dt.strftime("%Y-%m-%d").isin(config.BANK_HOLIDAYS), "bank holiday", "normal day")
pred["real_level"] = pred.groupby(["target", "hours_ahead"])["actual"].transform(
    lambda s: pd.qcut(s, 4, labels=["1 lowest quarter", "2", "3", "4 highest quarter"])
).astype(str)

rain_cols = [c for c in hourly.columns if "rain" in c.lower() or "precip" in c.lower()]
if rain_cols:
    rain = hourly[["time", rain_cols[0]]].rename(columns={rain_cols[0]: "rain_value"})
    pred = pred.merge(rain, left_on="target_time", right_on="time", how="left")
    pred["rain"] = np.where(pred["rain_value"] > 0, "wet hour", "dry hour")
    pred.loc[pred["rain_value"].isna(), "rain"] = np.nan
    print("Rain column used:", rain_cols[0])
else:
    print("No rain column found, rain split skipped")

groupings = ["hour_of_day", "weekday", "real_level", "month", "bank_holiday"]
if rain_cols:
    groupings.append("rain")

all_rows = []
for col in groupings:
    res = pred.groupby(["key", col], observed=True).agg(
        hours=("model_abs", "size"),
        model_mae=("model_abs", "mean"),
        baseline_mae=("base_abs", "mean"),
        bias=("model_err", "mean"),
    ).reset_index().rename(columns={col: "group"})
    res.insert(0, "grouping", col)
    all_rows.append(res)
    res["ratio"] = res["model_mae"] / res["baseline_mae"]
    print(f"\n=== By {col}: model MAE ===")
    print(res.pivot(index="group", columns="key", values="model_mae").round(2).to_string())
    print(f"--- By {col}: model MAE divided by simple-rule MAE (below 1 means the model wins) ---")
    print(res.pivot(index="group", columns="key", values="ratio").round(2).to_string())
    print(f"--- By {col}: bias (guess minus real) ---")
    print(res.pivot(index="group", columns="key", values="bias").round(2).to_string())

# have the levels moved? average real value per month, Jan to Jun
print("\n=== Average real level per month (all hours) ===")
cols = ["congestion_central", "wm6_no2", "wm6_pm25"]
levels = hourly.assign(month=hourly["time"].dt.tz_convert("Europe/London").dt.strftime("%Y-%m"))
levels = levels.groupby("month")[cols].mean().round(1)
print(levels.to_string())

# worst days
pred["day"] = local.dt.strftime("%Y-%m-%d")
daily = pred.groupby(["target", "hours_ahead", "day"]).agg(
    hours=("model_abs", "size"), model_mae=("model_abs", "mean"),
    baseline_mae=("base_abs", "mean"), average_real=("actual", "mean"),
).reset_index()
daily = daily[daily["hours"] >= 18]
worst = daily.sort_values("model_mae", ascending=False).groupby(["target", "hours_ahead"]).head(3)
worst = worst.sort_values(["target", "hours_ahead", "model_mae"], ascending=[True, True, False]).round(2)
print("\n=== Three worst days for each target and horizon ===")
print(worst.to_string(index=False))

config.TABLES_DIR.mkdir(parents=True, exist_ok=True)
pd.concat(all_rows).round(3).to_csv(config.TABLES_DIR / "error_analysis.csv", index=False)
levels.to_csv(config.TABLES_DIR / "monthly_levels.csv")
worst.to_csv(config.TABLES_DIR / "worst_days.csv", index=False)
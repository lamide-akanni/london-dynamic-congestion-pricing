"""
Monitoring (build guide Step 15).
Part 1, drift: do the inputs in May and June look like the training months?
Part 2, replay: week by week through May and June, as if live, is the model
still better than the best simple rule, and is its bias inside the S4 limit?
Uses the April-trained models' saved forecasts, the same ones that were scored.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

from ccz import config
from ccz.validate import check_hourly


def psi(train, new, bins):
    """Population Stability Index. The bins come from the training values."""
    train, new = train.dropna(), new.dropna()
    edges = np.unique(np.quantile(train, np.linspace(0, 1, bins + 1)))
    edges[0], edges[-1] = -np.inf, np.inf
    p = np.histogram(train, edges)[0] / len(train)
    q = np.histogram(new, edges)[0] / len(new)
    p, q = np.clip(p, 1e-4, None), np.clip(q, 1e-4, None)
    return float(np.sum((q - p) * np.log(q / p)))


# ---------------- Part 1: drift ----------------
hourly = pd.read_csv(config.HOURLY_FILE)
check_hourly(hourly)
hourly["time_utc"] = pd.to_datetime(hourly["time_utc"], utc=True)
train = hourly[hourly["time_utc"] <= pd.Timestamp(config.TRAIN_END, tz="UTC")]
test = hourly[hourly["time_utc"] >= pd.Timestamp(config.TEST_START, tz="UTC")]
features = list(config.TARGET_COLUMNS.values()) + [config.NEIGHBOUR_COLUMN] + list(config.WEATHER_INPUTS)

rows = []
for month in test["time_utc"].dt.strftime("%Y-%m").unique():
    new = test[test["time_utc"].dt.strftime("%Y-%m") == month]
    for col in features:
        value = psi(train[col], new[col], config.PSI_BINS)
        rows.append({
            "month": month, "feature": col,
            "train_mean": round(train[col].mean(), 2), "month_mean": round(new[col].mean(), 2),
            "psi": round(value, 3),
            "ks_stat": round(ks_2samp(train[col].dropna(), new[col].dropna()).statistic, 3),
            "drift_flag": value > config.PSI_LIMIT,
        })
drift = pd.DataFrame(rows)
drift.to_csv(config.TABLES_DIR / "monitoring_drift.csv", index=False)

# ---------------- Part 2: weekly replay ----------------
pred = pd.read_csv(config.TABLES_DIR / "holdout_predictions.csv")
pred = pred.dropna(subset=["actual", "model", "best_baseline"])
pred["time_utc"] = pd.to_datetime(pred["time_utc"], utc=True)
day = pred["time_utc"].dt.normalize()
pred["week_start"] = (day - pd.to_timedelta(day.dt.dayofweek, unit="D")).dt.date
pred["err_model"] = (pred["model"] - pred["actual"]).abs()
pred["err_base"] = (pred["best_baseline"] - pred["actual"]).abs()
pred["bias"] = pred["model"] - pred["actual"]

weekly = pred.groupby(["target", "hours_ahead", "week_start"]).agg(
    rows=("actual", "size"), level=("actual", "mean"),
    model_mae=("err_model", "mean"), baseline_mae=("err_base", "mean"), bias=("bias", "mean"),
).reset_index()
weekly["bias_pct"] = 100 * weekly["bias"].abs() / weekly["level"]
weekly["model_not_better"] = weekly["model_mae"] >= weekly["baseline_mae"]
weekly["flag_not_better"] = False
for _, grp in weekly.groupby(["target", "hours_ahead"]):
    in_a_row = grp["model_not_better"].astype(int).rolling(config.RETRAIN_WEEKS).sum() >= config.RETRAIN_WEEKS
    weekly.loc[grp.index, "flag_not_better"] = in_a_row.values
weekly["flag_bias"] = weekly["bias_pct"] > config.BIAS_LIMIT_PCT
weekly["retrain_flag"] = weekly["flag_not_better"] | weekly["flag_bias"]
weekly = weekly.round({"level": 2, "model_mae": 2, "baseline_mae": 2, "bias": 2, "bias_pct": 1})
weekly.to_csv(config.TABLES_DIR / "monitoring_weekly.csv", index=False)

# ---------------- Chart: congestion, weekly error ----------------
fig, axes = plt.subplots(1, 3, figsize=(15, 4), sharey=True)
for ax, h in zip(axes, config.HORIZONS):
    part = weekly[(weekly["target"] == "congestion") & (weekly["hours_ahead"] == h)]
    ax.plot(part["week_start"], part["model_mae"], marker="o", label="model")
    ax.plot(part["week_start"], part["baseline_mae"], marker="o", label="best simple rule")
    ax.set_title(f"Congestion, {h}h ahead")
    ax.tick_params(axis="x", rotation=45)
axes[0].set_ylabel("MAE (weekly)")
axes[0].legend()
fig.tight_layout()
fig.savefig(config.FIGURES_DIR / "monitoring_congestion_weekly.png", dpi=150)

# ---------------- Summary ----------------
print("Drift (PSI above", config.PSI_LIMIT, "):")
print(drift[drift["drift_flag"]][["month", "feature", "train_mean", "month_mean", "psi"]].to_string(index=False))
print("\nRetraining flags, first week raised:")
for (t, h), grp in weekly.groupby(["target", "hours_ahead"]):
    flagged = grp[grp["retrain_flag"]]
    if len(flagged):
        first = flagged.iloc[0]
        why = "not better 2 weeks" if first["flag_not_better"] else f"bias {first['bias_pct']}%"
        print(f"  {t} {h}h: {first['week_start']} ({why}), {len(flagged)} of {len(grp)} weeks flagged")
    else:
        print(f"  {t} {h}h: no flag")
print("\nSaved monitoring_drift.csv, monitoring_weekly.csv, monitoring_congestion_weekly.png")
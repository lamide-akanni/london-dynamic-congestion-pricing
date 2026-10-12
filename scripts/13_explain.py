# Step 10: what does the model rely on, and what do forecasts look like on real days?
# Models are refitted with the frozen settings on training rows only. Nothing here changes any setting.
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from ccz import baselines, config, features, models

settings = json.load(open(config.TABLES_DIR / "tuned_settings.json"))
hourly = pd.read_csv(config.HOURLY_FILE, parse_dates=["time_utc"])
table = features.build_inputs(features.add_targets(hourly))
inputs = features.input_columns()
figures = config.TABLES_DIR.parent / "figures"
figures.mkdir(parents=True, exist_ok=True)

# ---------- 1. which inputs matter (mean absolute SHAP value) ----------
importance = {}
long_rows = []
for name in config.TARGET_COLUMNS:
    for h in config.HORIZONS:
        y = f"y_{name}_{h}h"
        pick = settings[f"{name}_{h}h"]
        train = features.training_rows(table, name, h)
        test = features.test_rows(table, name, h)
        model = models.make_model(pick["kind"], pick["params"])
        if pick["mode"] == "correct":
            base_train = baselines.base_guess(train, train, name, h)
            fit = base_train.notna()
            model.fit(train.loc[fit, inputs], train.loc[fit, y] - base_train[fit])
        else:
            model.fit(train[inputs], train[y])

        sample = test[inputs].sample(min(300, len(test)), random_state=config.RANDOM_SEED)
        if hasattr(model, "steps"):
            inner = model[-1]
            sample = pd.DataFrame(model[:-1].transform(sample), columns=inputs, index=sample.index)
        else:
            inner = model
        values = shap.TreeExplainer(inner).shap_values(sample)
        series = pd.Series(np.abs(values).mean(axis=0), index=inputs).sort_values(ascending=False)
        importance[(name, h)] = series
        for rank, (feature, value) in enumerate(series.items(), start=1):
            long_rows.append({"target": name, "hours_ahead": h, "rank": rank,
                              "feature": feature, "mean_abs_shap": round(float(value), 4)})
        top = ", ".join(f"{f} {v:.2f}" for f, v in series.head(6).items())
        print(f"{name} {h}h ({pick['kind']}, {pick['mode']}): {top}", flush=True)

pd.DataFrame(long_rows).to_csv(config.TABLES_DIR / "feature_importance.csv", index=False)

fig, axes = plt.subplots(1, 3, figsize=(15, 5))
for ax, h in zip(axes, config.HORIZONS):
    top = importance[("congestion", h)].head(10)[::-1]
    ax.barh(top.index, top.values, color="#3b6ea5")
    ax.set_title(f"Congestion, {h} hour(s) ahead")
    ax.set_xlabel("Average effect on the forecast (SHAP)")
fig.tight_layout()
fig.savefig(figures / "feature_importance_congestion.png", dpi=150)
plt.close(fig)

# ---------- 2. example days for congestion ----------
d = pd.read_csv(config.TABLES_DIR / "holdout_predictions.csv")
d = d[d["target"] == "congestion"].copy()
d["target_time"] = pd.to_datetime(d["time_utc"], utc=True) + pd.to_timedelta(d["hours_ahead"], unit="h")
d["local"] = d["target_time"].dt.tz_convert("Europe/London")
d["day"] = d["local"].dt.strftime("%Y-%m-%d")
d["hour"] = d["local"].dt.hour
d["err"] = (d["model"] - d["actual"]).abs()

horizons = [1, 6]
fig, axes = plt.subplots(len(horizons), 3, figsize=(16, 8), sharey=True)
for r, h in enumerate(horizons):
    g = d[d["hours_ahead"] == h]
    daily = g.groupby("day").agg(n=("err", "size"), mae=("err", "mean"))
    daily = daily[daily["n"] == 24]
    holiday = next(x for x in ["2025-05-26", "2025-05-05"] if x in daily.index)
    picks = [
        ("Typical day", (daily["mae"] - daily["mae"].median()).abs().idxmin()),
        ("Worst day", daily["mae"].idxmax()),
        ("Bank holiday", holiday),
    ]
    for c, (label, day) in enumerate(picks):
        ax = axes[r, c]
        part = g[g["day"] == day].sort_values("hour")
        ax.plot(part["hour"], part["actual"], color="black", label="Real")
        ax.plot(part["hour"], part["model"], color="#d1495b", label="Model")
        ax.plot(part["hour"], part["best_baseline"], color="grey", linestyle="--", label="Simple rule")
        ax.axhline(config.CONGESTION_ALARM_LEVEL, color="#edae49", linestyle=":", label="Alarm level")
        ax.set_title(f"{label}, {day}, {h}h ahead (model MAE {daily.loc[day, 'mae']:.1f})")
        ax.set_xlabel("Hour of the day (London)")
        if c == 0:
            ax.set_ylabel("Congestion (%)")
        if r == 0 and c == 0:
            ax.legend()
fig.tight_layout()
fig.savefig(figures / "example_days_congestion.png", dpi=150)
plt.close(fig)
print("\nSaved: feature_importance.csv, feature_importance_congestion.png, example_days_congestion.png")
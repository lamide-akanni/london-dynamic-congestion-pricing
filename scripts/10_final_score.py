# Final score. Settings are frozen from scripts/09_tune.py, so nothing here is tuned.
# 1) Four monthly checks: each month is scored by a model trained only on earlier months.
# 2) The May + June hold-out score: model trained through the end of April.
# The baseline for each row is the best of mean, median, persistence and weekly profile on the same rows.
import json

import pandas as pd
from ccz import baselines, config, features, models

BASELINES = ["mean", "median", "persistence", "weekly_profile"]

settings = json.load(open(config.TABLES_DIR / "tuned_settings.json"))
hourly = pd.read_csv(config.HOURLY_FILE, parse_dates=["time_utc"])
table = features.build_inputs(features.add_targets(hourly))
inputs = features.input_columns()


def run(name, h, train_end, test):
    y = f"y_{name}_{h}h"
    train = features.training_rows(table, name, h, train_end=train_end)
    guesses = baselines.baseline_guesses(train, test, name, h)
    use = guesses[BASELINES].notna().all(axis=1)
    pick = settings[f"{name}_{h}h"]
    model = models.make_model(pick["kind"], pick["params"])
    if pick["mode"] == "correct":
        base_train = baselines.base_guess(train, train, name, h)
        fit = base_train.notna()
        model.fit(train.loc[fit, inputs], train.loc[fit, y] - base_train[fit])
        guess = baselines.base_guess(train, test, name, h) + model.predict(test[inputs])
    else:
        model.fit(train[inputs], train[y])
        guess = pd.Series(model.predict(test[inputs]), index=test.index)
    actual = test.loc[use, y]
    base_errors = guesses.loc[use, BASELINES].sub(actual, axis=0).abs().mean()
    best = base_errors.idxmin()
    model_mae = float((guess[use] - actual).abs().mean())
    detail = pd.DataFrame({
        "time_utc": test.loc[use, "time_utc"],
        "target": name,
        "hours_ahead": h,
        "actual": actual,
        "model": guess[use],
        "best_baseline": guesses.loc[use, best],
    })
    return float(base_errors[best]), model_mae, len(actual), detail


monthly_rows, final_rows, details = [], [], []
for name in config.TARGET_COLUMNS:
    for h in config.HORIZONS:
        # hold-out first: trained through the training end, scored on May and June together
        base, mae, n, detail = run(name, h, None, features.test_rows(table, name, h))
        details.append(detail)
        holdout_mae = mae
        final_rows.append({
            "target": name, "hours_ahead": h, "rows": n,
            "baseline_mae": round(base, 2), "model_mae": round(mae, 2),
            "skill_pct": round(100 * (1 - mae / base), 1),
        })
        worst_ratio = 0.0
        for month in config.ROLLING_TEST_MONTHS:
            train_end = (pd.Timestamp(month + "-01") - pd.Timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")
            b, m, k, _ = run(name, h, train_end, features.month_rows(table, name, h, month))
            ratio = m / holdout_mae
            worst_ratio = max(worst_ratio, ratio)
            monthly_rows.append({
                "target": name, "hours_ahead": h, "month": month, "rows": k,
                "baseline_mae": round(b, 2), "model_mae": round(m, 2),
                "skill_pct": round(100 * (1 - m / b), 1),
                "ratio_to_holdout": round(ratio, 2),
            })
        final_rows[-1]["worst_month_ratio"] = round(worst_ratio, 2)
        final_rows[-1]["S1_pass"] = final_rows[-1]["skill_pct"] >= 10
        final_rows[-1]["S2_pass"] = worst_ratio <= 1.5

monthly = pd.DataFrame(monthly_rows)
final = pd.DataFrame(final_rows)
print("\nFour monthly checks")
print(monthly.to_string(index=False))
print("\nFinal May and June score")
print(final.to_string(index=False))

config.TABLES_DIR.mkdir(parents=True, exist_ok=True)
monthly.to_csv(config.TABLES_DIR / "rolling_monthly_mae.csv", index=False)
final.to_csv(config.TABLES_DIR / "final_holdout_score.csv", index=False)
pd.concat(details).to_csv(config.TABLES_DIR / "holdout_predictions.csv", index=False)

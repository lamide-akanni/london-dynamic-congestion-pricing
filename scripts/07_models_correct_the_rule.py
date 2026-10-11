# Same as script 06, but each model learns the MISS of a simple
# rule and adds it back, so the starting point is the rule itself.
import pandas as pd
from ccz import baselines, config, features, models

BASELINES = ["mean", "median", "persistence", "weekly_profile"]
MODEL_NAMES = ["ridge", "random_forest", "xgboost"]

hourly = pd.read_csv(config.HOURLY_FILE, parse_dates=["time_utc"])
table = features.build_inputs(features.add_targets(hourly))
inputs = features.input_columns()

results = []
for name in config.TARGET_COLUMNS:
    for h in config.HORIZONS:
        y = f"y_{name}_{h}h"
        errors = []
        for month, train_end in config.VALIDATION_FOLDS:
            train = features.training_rows(table, name, h, train_end=train_end)
            valid = features.month_rows(table, name, h, month)
            guesses = baselines.baseline_guesses(train, valid, name, h)

            base_train = baselines.base_guess(train, train, name, h)
            base_valid = baselines.base_guess(train, valid, name, h)
            fit = base_train.notna()
            miss = train.loc[fit, y] - base_train[fit]
            for label, model in models.make_models().items():
                model.fit(train.loc[fit, inputs], miss)
                guesses[label] = base_valid + model.predict(valid[inputs])

            usable = guesses[BASELINES].notna().all(axis=1)
            errors.append(guesses[usable].sub(valid.loc[usable, y], axis=0).abs())

        mae = pd.concat(errors).mean()
        best_base = mae[BASELINES].idxmin()
        best_model = mae[MODEL_NAMES].idxmin()
        results.append({
            "target": name,
            "hours_ahead": h,
            "rows": sum(len(e) for e in errors),
            "best_baseline": best_base,
            "baseline_mae": round(mae[best_base], 2),
            "ridge": round(mae["ridge"], 2),
            "random_forest": round(mae["random_forest"], 2),
            "xgboost": round(mae["xgboost"], 2),
            "skill_pct": round(100 * (1 - mae[best_model] / mae[best_base]), 1),
        })

out = pd.DataFrame(results)
print(out.to_string(index=False))
out.to_csv(config.TABLES_DIR / "validation_models_correct_rule_mae.csv", index=False)

# Tuning: random search, judged on the validation months only (March, April).
TUNING_TRIES = 8
SEARCH_SPACE = {
    "ridge": {"alpha": [0.1, 1.0, 10.0, 100.0, 1000.0]},
    "random_forest": {
        "n_estimators": [200, 400],
        "min_samples_leaf": [2, 5, 10, 20],
        "max_features": [0.3, 0.5, 1.0],
    },
    "xgboost": {
        "n_estimators": [100, 200, 400],
        "learning_rate": [0.02, 0.05, 0.1],
        "max_depth": [2, 3, 4, 6],
        "subsample": [0.7, 1.0],
        "colsample_bytree": [0.5, 0.8, 1.0],
    },
}
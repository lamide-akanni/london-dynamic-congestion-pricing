# First look at three models. Scored on March and April only, each month by a model
# trained on earlier months. The test months (May, June) are not touched.
# Settings below are untuned first guesses. Tuning comes later (Step 11).
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor
from ccz import baselines, config, features

BASELINES = ["mean", "median", "persistence", "weekly_profile"]
MODELS = ["ridge", "random_forest", "xgboost"]


def make_models():
    seed = config.RANDOM_SEED
    return {
        "ridge": make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(alpha=1.0)),
        "random_forest": make_pipeline(
            SimpleImputer(strategy="median"),
            RandomForestRegressor(n_estimators=200, min_samples_leaf=5, random_state=seed, n_jobs=-1),
        ),
        "xgboost": XGBRegressor(n_estimators=200, learning_rate=0.05, max_depth=4,
                                subsample=0.8, colsample_bytree=0.8, random_state=seed),
    }


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
            for label, model in make_models().items():
                model.fit(train[inputs], train[y])
                guesses[label] = model.predict(valid[inputs])
            usable = guesses[BASELINES].notna().all(axis=1)
            errors.append(guesses[usable].sub(valid.loc[usable, y], axis=0).abs())

        mae = pd.concat(errors).mean()
        best_base = mae[BASELINES].idxmin()
        best_model = mae[MODELS].idxmin()
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

config.TABLES_DIR.mkdir(parents=True, exist_ok=True)
out.to_csv(config.TABLES_DIR / "validation_models_mae.csv", index=False)
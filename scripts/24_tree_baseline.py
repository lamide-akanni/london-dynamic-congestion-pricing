# A shallow decision tree as one more baseline. Depth 4 is fixed in advance, not tuned.
# Scored on the same hold-out rows as the model and the best simple rule.
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.tree import DecisionTreeRegressor
from ccz import baselines, config, features

BASELINES = ["mean", "median", "persistence", "weekly_profile"]

hourly = pd.read_csv(config.HOURLY_FILE, parse_dates=["time_utc"])
table = features.build_inputs(features.add_targets(hourly))
inputs = features.input_columns()
saved = pd.read_csv(config.TABLES_DIR / "holdout_predictions.csv")

rows = []
for name in config.TARGET_COLUMNS:
    for h in config.HORIZONS:
        y = f"y_{name}_{h}h"
        train = features.training_rows(table, name, h, train_end=None)
        test = features.test_rows(table, name, h)
        guesses = baselines.baseline_guesses(train, test, name, h)
        use = guesses[BASELINES].notna().all(axis=1)

        tree = make_pipeline(
            SimpleImputer(strategy="median"),
            DecisionTreeRegressor(max_depth=4, min_samples_leaf=20, random_state=config.RANDOM_SEED),
        )
        tree.fit(train[inputs], train[y])
        guess = pd.Series(tree.predict(test[inputs]), index=test.index)
        tree_mae = float((guess[use] - test.loc[use, y]).abs().mean())

        g = saved[(saved["target"] == name) & (saved["hours_ahead"] == h)]
        model_mae = float((g["model"] - g["actual"]).abs().mean())
        base_mae = float((g["best_baseline"] - g["actual"]).abs().mean())
        rows.append({
            "target": name, "hours_ahead": h,
            "rows_tree": int(use.sum()), "rows_saved": len(g),
            "best_rule_mae": round(base_mae, 2), "tree_mae": round(tree_mae, 2),
            "model_mae": round(model_mae, 2),
            "tree_skill_pct": round(100 * (1 - tree_mae / base_mae), 1),
            "model_skill_pct": round(100 * (1 - model_mae / base_mae), 1),
        })

result = pd.DataFrame(rows)
result.to_csv(config.TABLES_DIR / "holdout_tree_baseline.csv", index=False)
print(result.to_string(index=False))
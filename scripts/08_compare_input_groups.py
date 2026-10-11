# Validation folds inside the training months. Each month is predicted by a model
# trained only on earlier months. May and June (the test months) are never used here.

import pandas as pd
from ccz import baselines, config, features, models

BASELINES = ["mean", "median", "persistence", "weekly_profile"]
MODEL_NAMES = ["ridge", "random_forest", "xgboost"]
INPUT_SETS = {
    "base": (),
    "recent": ("recent",),
    "neighbour": ("neighbour",),
    "both": ("recent", "neighbour"),
}


def score(table, inputs, name, h):
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
    return pd.concat(errors).mean()


hourly = pd.read_csv(config.HOURLY_FILE, parse_dates=["time_utc"])
table = features.build_inputs(features.add_targets(hourly))

rows = []
for name in config.TARGET_COLUMNS:
    for h in config.HORIZONS:
        row = {"target": name, "hours_ahead": h}
        for set_name, groups in INPUT_SETS.items():
            mae = score(table, features.input_columns(groups), name, h)
            base = mae[BASELINES].min()
            best = mae[MODEL_NAMES].min()
            row["baseline_mae"] = round(base, 2)
            row[f"skill_{set_name}"] = round(100 * (1 - best / base), 1)
        rows.append(row)

out = pd.DataFrame(rows)
print(out.to_string(index=False))
out.to_csv(config.TABLES_DIR / "validation_input_groups.csv", index=False)
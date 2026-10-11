# Tuning on the validation months only (March, April). The test months are never touched.
# For every target and horizon it tries: two ways of using the simple rule
# ("direct" = guess the answer, "correct" = learn the rule's miss), three model types,
# the default settings plus a few random ones. It keeps the best by validation MAE,
# and reports defaults and tuned side by side.
import json
from math import prod

import pandas as pd
from sklearn.model_selection import ParameterSampler
from ccz import baselines, config, features, models

BASELINES = ["mean", "median", "persistence", "weekly_profile"]
MODES = ["direct", "correct"]

hourly = pd.read_csv(config.HOURLY_FILE, parse_dates=["time_utc"])
table = features.build_inputs(features.add_targets(hourly))
inputs = features.input_columns()


def prepare(name, h):
    folds = []
    for month, train_end in config.VALIDATION_FOLDS:
        train = features.training_rows(table, name, h, train_end=train_end)
        valid = features.month_rows(table, name, h, month)
        guesses = baselines.baseline_guesses(train, valid, name, h)
        folds.append({
            "train": train,
            "valid": valid,
            "guesses": guesses,
            "usable": guesses[BASELINES].notna().all(axis=1),
            "base_train": baselines.base_guess(train, train, name, h),
            "base_valid": baselines.base_guess(train, valid, name, h),
        })
    return folds


def baseline_mae(folds, y):
    errors = []
    for f in folds:
        use = f["usable"]
        errors.append(f["guesses"].loc[use, BASELINES].sub(f["valid"].loc[use, y], axis=0).abs())
    return pd.concat(errors).mean().min()


def model_mae(folds, y, kind, mode, params):
    errors = []
    for f in folds:
        train, valid, use = f["train"], f["valid"], f["usable"]
        model = models.make_model(kind, params)
        if mode == "correct":
            fit = f["base_train"].notna()
            model.fit(train.loc[fit, inputs], train.loc[fit, y] - f["base_train"][fit])
            guess = f["base_valid"] + model.predict(valid[inputs])
        else:
            model.fit(train[inputs], train[y])
            guess = pd.Series(model.predict(valid[inputs]), index=valid.index)
        errors.append((guess[use] - valid.loc[use, y]).abs())
    return pd.concat(errors).mean()


def random_settings(space):
    size = prod(len(v) for v in space.values())
    sampler = ParameterSampler(space, n_iter=min(config.TUNING_TRIES, size),
                               random_state=config.RANDOM_SEED)
    return list(sampler)


rows, chosen = [], {}
for name in config.TARGET_COLUMNS:
    for h in config.HORIZONS:
        y = f"y_{name}_{h}h"
        folds = prepare(name, h)
        base = baseline_mae(folds, y)
        best_default = None
        best_tuned = None
        for mode in MODES:
            for kind, space in config.SEARCH_SPACE.items():
                tries = [models.DEFAULTS[kind]] + random_settings(space)
                for i, params in enumerate(tries):
                    mae = model_mae(folds, y, kind, mode, params)
                    entry = (mae, kind, mode, params)
                    if i == 0 and (best_default is None or mae < best_default[0]):
                        best_default = entry
                    if best_tuned is None or mae < best_tuned[0]:
                        best_tuned = entry
        chosen[f"{name}_{h}h"] = {
            "kind": best_tuned[1], "mode": best_tuned[2], "params": best_tuned[3],
        }
        rows.append({
            "target": name,
            "hours_ahead": h,
            "baseline_mae": round(base, 2),
            "default_mae": round(best_default[0], 2),
            "tuned_mae": round(best_tuned[0], 2),
            "skill_default": round(100 * (1 - best_default[0] / base), 1),
            "skill_tuned": round(100 * (1 - best_tuned[0] / base), 1),
            "chosen": f"{best_tuned[1]} / {best_tuned[2]}",
        })
        print(rows[-1], flush=True)

out = pd.DataFrame(rows)
print()
print(out.to_string(index=False))

config.TABLES_DIR.mkdir(parents=True, exist_ok=True)
out.to_csv(config.TABLES_DIR / "tuning_validation.csv", index=False)
with open(config.TABLES_DIR / "tuned_settings.json", "w") as f:
    json.dump(chosen, f, indent=2)
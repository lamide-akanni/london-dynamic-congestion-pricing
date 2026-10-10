# Scores four simple rules on the test months (May and June).
# Every rule is fitted on training rows only. MAE = average miss in the target's own units.
import numpy as np
import pandas as pd
from ccz import config, features

hourly = pd.read_csv(config.HOURLY_FILE, parse_dates=["time_utc"])
table = features.build_inputs(features.add_targets(hourly))

results = []
for name, column in config.TARGET_COLUMNS.items():
    for h in config.HORIZONS:
        y = f"y_{name}_{h}h"
        train = features.training_rows(table, name, h)
        test = features.test_rows(table, name, h)

        profile = train.groupby(["dayofweek_london", "hour_london"])[y].mean()
        keys = zip(test["dayofweek_london"], test["hour_london"])

        guesses = pd.DataFrame({
            "mean": train[y].mean(),
            "median": train[y].median(),
            "persistence": test[column],
            "weekly_profile": [profile.get(k, np.nan) for k in keys],
        }, index=test.index)

        usable = guesses.notna().all(axis=1)
        errors = guesses[usable].sub(test.loc[usable, y], axis=0).abs()
        row = {"target": name, "hours_ahead": h, "test_rows": int(usable.sum())}
        row.update(errors.mean().round(2).to_dict())
        results.append(row)

out = pd.DataFrame(results)
print(out.to_string(index=False))

config.TABLES_DIR.mkdir(parents=True, exist_ok=True)
out.to_csv(config.TABLES_DIR / "baselines_mae.csv", index=False)
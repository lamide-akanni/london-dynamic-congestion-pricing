# The four simple rules every model has to beat. Fitted on the training rows only.
import numpy as np
import pandas as pd
from ccz import config


def baseline_guesses(train, test, name, h):
    column = config.TARGET_COLUMNS[name]
    y = f"y_{name}_{h}h"
    profile = train.groupby(["dayofweek_london", "hour_london"])[y].mean()
    keys = zip(test["dayofweek_london"], test["hour_london"])
    return pd.DataFrame({
        "mean": train[y].mean(),
        "median": train[y].median(),
        "persistence": test[column],
        "weekly_profile": [profile.get(k, np.nan) for k in keys],
    }, index=test.index)
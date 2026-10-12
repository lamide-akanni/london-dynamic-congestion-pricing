# Fuller hold-out metrics from the saved predictions (nothing is refitted here).
# S4: absolute average bias below 10% of the average level.
# S3: congestion alarm at 60 or more; recall >= 0.80 and precision >= 0.85 at 6 hours.
import numpy as np
import pandas as pd
from ccz import config

d = pd.read_csv(config.TABLES_DIR / "holdout_predictions.csv")


def stats(p, a, level):
    e = p - a
    floor = 0.1 * level
    return {
        "mae": e.abs().mean(),
        "rmse": np.sqrt((e ** 2).mean()),
        "r2": 1 - (e ** 2).sum() / ((a - level) ** 2).sum(),
        "bias": e.mean(),
        "bias_pct_of_level": 100 * abs(e.mean()) / level,
        "wape_pct": 100 * e.abs().sum() / a.abs().sum(),
        "mape_pct": 100 * (e.abs() / np.maximum(a.abs(), floor)).mean(),
    }


metric_rows, alarm_rows = [], []
for (name, h), g in d.groupby(["target", "hours_ahead"], sort=False):
    a, level = g["actual"], g["actual"].mean()
    for who in ["model", "best_baseline"]:
        row = {"target": name, "hours_ahead": h, "forecaster": who, "average_level": level}
        row.update(stats(g[who], a, level))
        row["S4_pass"] = row["bias_pct_of_level"] < 10
        metric_rows.append(row)
    if name == "congestion":
        real = a >= config.CONGESTION_ALARM_LEVEL
        for who in ["model", "best_baseline"]:
            said = g[who] >= config.CONGESTION_ALARM_LEVEL
            tp = int((real & said).sum())
            fp = int((~real & said).sum())
            fn = int((real & ~said).sum())
            precision = tp / (tp + fp) if tp + fp else 0.0
            recall = tp / (tp + fn) if tp + fn else 0.0
            f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
            alarm_rows.append({
                "hours_ahead": h, "forecaster": who, "real_alarm_hours": int(real.sum()),
                "precision": precision, "recall": recall, "f1": f1,
                "S3_pass": bool(precision >= 0.85 and recall >= 0.80),
            })

metrics = pd.DataFrame(metric_rows).round(2)
alarm = pd.DataFrame(alarm_rows).round(2)
print(metrics.to_string(index=False))
print()
print(alarm.to_string(index=False))

metrics.to_csv(config.TABLES_DIR / "holdout_metrics.csv", index=False)
alarm.to_csv(config.TABLES_DIR / "holdout_alarm.csv", index=False)
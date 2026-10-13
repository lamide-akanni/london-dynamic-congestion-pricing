# Read-only check on the saved hold-out predictions (nothing is refitted or tuned).
# 1) Clip forecasts to the physical range: congestion 0 to 100, pollutants 0 or more.
# 2) Threshold-free quality of the congestion alarm: ROC-AUC and PR-AUC.
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score
from ccz import config

d = pd.read_csv(config.TABLES_DIR / "holdout_predictions.csv")
d["model_clipped"] = np.where(d["target"] == "congestion", d["model"].clip(0, 100), d["model"].clip(lower=0))

clip_rows = []
for (name, h), g in d.groupby(["target", "hours_ahead"], sort=False):
    clip_rows.append({
        "target": name, "hours_ahead": h,
        "hours_changed": int((g["model"] != g["model_clipped"]).sum()),
        "mae_before": (g["model"] - g["actual"]).abs().mean(),
        "mae_after": (g["model_clipped"] - g["actual"]).abs().mean(),
    })
clipping = pd.DataFrame(clip_rows).round(3)
clipping.to_csv(config.TABLES_DIR / "holdout_clipping.csv", index=False)
print("Effect of clipping to the physical range:")
print(clipping.to_string(index=False))

auc_rows = []
cong = d[d["target"] == "congestion"]
for h, g in cong.groupby("hours_ahead"):
    real = g["actual"] >= config.CONGESTION_ALARM_LEVEL
    for who in ["model", "best_baseline"]:
        auc_rows.append({
            "hours_ahead": h, "forecaster": who,
            "alarm_share": real.mean(),
            "roc_auc": roc_auc_score(real, g[who]),
            "pr_auc": average_precision_score(real, g[who]),
        })
auc = pd.DataFrame(auc_rows).round(3)
auc.to_csv(config.TABLES_DIR / "holdout_alarm_auc.csv", index=False)
print("\nCongestion alarm (level 60), threshold-free quality:")
print(auc.to_string(index=False))
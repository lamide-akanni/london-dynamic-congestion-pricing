# Train the final models on all available hours with the frozen settings, and save them.
# The accuracy in the report comes from the April-trained models scored on May and June (script 10).
# These all-data models have no unseen months left to be scored on. The docs say so.
import json
import platform
from datetime import datetime, timezone

import pandas as pd
import sklearn
import xgboost
from ccz import config, features, inference

settings = json.load(open(config.TABLES_DIR / "tuned_settings.json"))
hourly = pd.read_csv(config.HOURLY_FILE, parse_dates=["time_utc"])
table = features.build_inputs(features.add_targets(hourly))
train_end = hourly["time_utc"].max().strftime("%Y-%m-%d %H:%M")
print(f"Training on all hours up to {train_end} UTC. Models go to {inference.models_dir()}")

manifest = {
    "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
    "trained_through_utc": train_end,
    "note": "Trained on all available hours. Reported accuracy comes from the April-trained models scored on May and June.",
    "libraries": {
        "python": platform.python_version(),
        "pandas": pd.__version__,
        "scikit-learn": sklearn.__version__,
        "xgboost": xgboost.__version__,
    },
    "models": {},
}

for name in config.TARGET_COLUMNS:
    for h in config.HORIZONS:
        pick = settings[f"{name}_{h}h"]
        bundle = inference.fit_bundle(table, name, h, pick, train_end)
        path = inference.save_bundle(bundle)
        manifest["models"][f"{name}_{h}h"] = {
            "kind": pick["kind"], "mode": pick["mode"], "rows": bundle["rows"], "file": path.name,
        }
        print(f"  {name} {h}h: {pick['kind']} ({pick['mode']}), {bundle['rows']} rows -> {path.name}")

with open(inference.models_dir() / "manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)
print("Manifest saved.")
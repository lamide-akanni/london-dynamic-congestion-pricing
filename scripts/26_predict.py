# Batch forecast from the saved final models. Nothing is retrained.
import numpy as np
import pandas as pd
from ccz import config, inference

hourly = pd.read_csv(config.HOURLY_FILE, parse_dates=["time_utc"])

result = inference.forecast_table(hourly, n_last=24)
result.to_csv(config.TABLES_DIR / "latest_forecasts.csv", index=False)
latest = result[result["origin_utc"] == result["origin_utc"].max()]
print("Forecasts made at the newest hour in the data:")
print(latest.assign(forecast=latest["forecast"].round(1)).to_string(index=False))

# Sanity check only: these models were trained on these hours, so this is NOT an accuracy claim.
check = inference.forecast_table(hourly, n_last=200)
actual = hourly.set_index("time_utc")[config.TARGET_COLUMNS["congestion"]]
sub = check[(check["target"] == "congestion") & (check["hours_ahead"] == 1)]
real = actual.reindex(sub["forecast_for_utc"]).to_numpy()
mae = np.nanmean(np.abs(sub["forecast"].to_numpy() - real))
print(f"\nSanity check (in-sample, congestion 1h, last 200 hours): MAE {mae:.2f}")
# Robustness checks for the pricing result.
# 1) Forecast error scaled from 0 to 4 times the measured error of our model (S7).
# 2) Softer road curve (exponent 2).
# 3) PM2.5 traffic share halved.
# Each plan is made on the (changed) forecast and scored on what really happened.
import numpy as np
import pandas as pd
from ccz import config, optimiser, pricing

COLUMNS = ["congestion", "no2", "pm25"]
ERROR_MULTIPLIERS = [0, 0.5, 1, 1.5, 2, 3, 4]
TARGET = float(config.BASE_PRICE)
BOOTSTRAPS = 300

table = pd.read_csv(config.TABLES_DIR / "pricing_inputs.csv")
table = table.sort_values(["local_date", "block", "price_hour"]).reset_index(drop=True)
base_shares = pricing.load_shares()

blocks = []
for (day, block), g in table.groupby(["local_date", "block"], sort=True):
    blocks.append((day, g.index.to_numpy()))
unique_days = sorted(set(b[0] for b in blocks))
rows_of_day = {d: np.concatenate([b[1] for b in blocks if b[0] == d]) for d in unique_days}
all_rows = np.arange(len(table))

real = {col: table[f"{col}_actual"].to_numpy(float) for col in COLUMNS}
model = {col: table[f"{col}_model"].to_numpy(float) for col in COLUMNS}
rng = np.random.default_rng(config.RANDOM_SEED)


def forecast_with_error(multiplier):
    # multiplier 1 = our model, 0 = perfect, 2 = twice the measured error (same pattern, bigger)
    out = {}
    for col in COLUMNS:
        values = real[col] + multiplier * (model[col] - real[col])
        out[col] = np.clip(values, 1.0, 100.0) if col == "congestion" else np.clip(values, 0.1, None)
    return out


def harm(price, elasticity, rows, shares):
    out = pricing.outcomes(price, elasticity, real["congestion"][rows], real["no2"][rows],
                           real["pm25"][rows], shares)
    h = (out["congestion"].mean() / real["congestion"][rows].mean()
         + out["no2"].mean() / real["no2"][rows].mean()
         + out["pm25"].mean() / real["pm25"][rows].mean()) / 3
    return h, out


def evaluate(forecast, elasticity, shares):
    price = np.zeros(len(table))
    misses = 0
    for day, index in blocks:
        c, n, p = (forecast[col][index] for col in COLUMNS)
        x = optimiser.solve_matched(elasticity, c, n, p, shares, TARGET)
        x = np.clip(x, config.PRICE_FLOOR, config.PRICE_CEILING)
        planned = pricing.evaluate_many(x, elasticity, c, n, p, shares)["average_price_paid"][0]
        misses += abs(planned - TARGET) > 0.05
        price[index] = x

    h, out = harm(price, elasticity, all_rows, shares)
    paid = out["average_price_paid"]
    matched = harm(np.full(len(table), paid), elasticity, all_rows, shares)[0]

    gains = []
    for _ in range(BOOTSTRAPS):
        picked = rng.choice(unique_days, size=len(unique_days), replace=True)
        rows = np.concatenate([rows_of_day[d] for d in picked])
        hd, od = harm(price[rows], elasticity, rows, shares)
        gains.append(harm(np.full(len(rows), od["average_price_paid"]), elasticity, rows, shares)[0] - hd)
    low, high = np.percentile(gains, [2.5, 97.5])
    return {
        "average_price_paid": paid,
        "congestion_pct": 100 * (out["congestion"].mean() / real["congestion"].mean() - 1),
        "no2_pct": 100 * (out["no2"].mean() / real["no2"].mean() - 1),
        "pm25_pct": 100 * (out["pm25"].mean() / real["pm25"].mean() - 1),
        "harm": h, "gain": matched - h, "gain_low": low, "gain_high": high,
        "plan_misses": int(misses),
    }


results = []
for elasticity in config.ELASTICITIES:
    for m in ERROR_MULTIPLIERS:
        row = evaluate(forecast_with_error(m), elasticity, base_shares)
        results.append({"elasticity": elasticity, "case": f"forecast error x{m}", **row})
        print(f"elasticity {elasticity}: forecast error x{m} done")

    # softer road curve: planning and scoring both use exponent 2
    original_exponent = config.BPR_EXPONENT
    config.BPR_EXPONENT = 2
    row = evaluate(forecast_with_error(1), elasticity, base_shares)
    config.BPR_EXPONENT = original_exponent
    results.append({"elasticity": elasticity, "case": "road curve exponent 2", **row})
    print(f"elasticity {elasticity}: road curve exponent 2 done")

    # PM2.5 traffic share halved
    halved = dict(base_shares)
    halved["pm25"] = base_shares["pm25"] / 2
    row = evaluate(forecast_with_error(1), elasticity, halved)
    results.append({"elasticity": elasticity, "case": "PM2.5 share halved", **row})
    print(f"elasticity {elasticity}: PM2.5 share halved done")

result = pd.DataFrame(results)
result.to_csv(config.TABLES_DIR / "robustness.csv", index=False)

print("\nGain = matched flat harm minus dynamic harm (positive = dynamic wins). Range is a 95% range over days.")
show = result.copy()
for column in ["average_price_paid", "congestion_pct", "no2_pct", "pm25_pct"]:
    show[column] = show[column].round(2)
for column in ["harm", "gain", "gain_low", "gain_high"]:
    show[column] = show[column].round(4)
print(show.to_string(index=False))

print("\nBreak-even forecast error (first multiplier where the 95% range reaches zero):")
for elasticity in config.ELASTICITIES:
    part = result[(result["elasticity"] == elasticity) & result["case"].str.startswith("forecast error")]
    failed = part[part["gain_low"] <= 0]
    where = failed["case"].iloc[0] if len(failed) else "not reached up to x4"
    print(f"  elasticity {elasticity}: {where}")
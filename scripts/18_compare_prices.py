# Full pricing comparison. Plan each block on a forecast, score the plan on what really happened.
# Dynamic schedules are planned to an average price paid of 15 (the solver), then compared with
# a flat price that has the same realised average price paid.
import numpy as np
import pandas as pd
from ccz import config, optimiser, pricing

SOURCES = ["actual", "model", "profile", "persistence"]
SOURCE_NAMES = {"actual": "perfect", "model": "our model", "profile": "weekly profile", "persistence": "persistence"}
TARGET = float(config.BASE_PRICE)
BOOTSTRAPS = 1000

table = pd.read_csv(config.TABLES_DIR / "pricing_inputs.csv")
table = table.sort_values(["local_date", "block", "price_hour"]).reset_index(drop=True)
shares = pricing.load_shares()

blocks = []
for (day, block), g in table.groupby(["local_date", "block"], sort=True):
    blocks.append((day, block, g.index.to_numpy()))
print(f"{len(blocks)} blocks, {len(table)} priced hours")

real_c = table["congestion_actual"].to_numpy(float)
real_n = table["no2_actual"].to_numpy(float)
real_p = table["pm25_actual"].to_numpy(float)
days = np.array([b[0] for b in blocks])
unique_days = sorted(set(days))
rows_of_day = {d: np.concatenate([b[2] for b in blocks if b[0] == d]) for d in unique_days}


def forecast(column, source, index):
    values = table.loc[index, f"{column}_{source}"].to_numpy(float)
    if column == "congestion":
        return np.clip(values, 1.0, 100.0)
    return np.clip(values, 0.1, None)


def harm(price, elasticity, rows):
    # Realised, pooled over the hours in rows. 1.00 = as observed.
    out = pricing.outcomes(price, elasticity, real_c[rows], real_n[rows], real_p[rows], shares)
    h = (out["congestion"].mean() / real_c[rows].mean()
         + out["no2"].mean() / real_n[rows].mean()
         + out["pm25"].mean() / real_p[rows].mean()) / 3
    return h, out


def flat_matched_harm(price_paid, elasticity, rows):
    # A flat price pays exactly that average price, so the matched flat price is the dynamic average.
    return harm(np.full(len(rows), price_paid), elasticity, rows)[0]


all_rows = np.arange(len(table))
results = []
rng = np.random.default_rng(config.RANDOM_SEED)
plan_misses = 0

for elasticity in config.ELASTICITIES:
    # flat benchmarks, scored on all hours
    for name, flat in [("flat 15", 15.0), ("flat 18", 18.0)]:
        h, out = harm(np.full(len(table), flat), elasticity, all_rows)
        results.append({
            "elasticity": elasticity, "plan": name, "average_price_paid": flat,
            "congestion_pct": 100 * (out["congestion"].mean() / real_c.mean() - 1),
            "no2_pct": 100 * (out["no2"].mean() / real_n.mean() - 1),
            "pm25_pct": 100 * (out["pm25"].mean() / real_p.mean() - 1),
            "harm": h, "flat_matched_harm": h, "gain": 0.0, "gain_low": np.nan, "gain_high": np.nan,
        })

    for source in SOURCES:
        price = np.zeros(len(table))
        for day, block, index in blocks:
            c = forecast("congestion", source, index)
            n = forecast("no2", source, index)
            p = forecast("pm25", source, index)
            x = optimiser.solve_matched(elasticity, c, n, p, shares, TARGET)
            x = np.clip(x, config.PRICE_FLOOR, config.PRICE_CEILING)
            planned = pricing.evaluate_many(x, elasticity, c, n, p, shares)["average_price_paid"][0]
            if abs(planned - TARGET) > 0.05:
                plan_misses += 1
            price[index] = x

        h, out = harm(price, elasticity, all_rows)
        paid = out["average_price_paid"]
        matched = flat_matched_harm(paid, elasticity, all_rows)

        # uncertainty: resample the days, with replacement
        gains = []
        for _ in range(BOOTSTRAPS):
            picked = rng.choice(unique_days, size=len(unique_days), replace=True)
            rows = np.concatenate([rows_of_day[d] for d in picked])
            hd, od = harm(price[rows], elasticity, rows)
            gains.append(flat_matched_harm(od["average_price_paid"], elasticity, rows) - hd)
        low, high = np.percentile(gains, [2.5, 97.5])

        results.append({
            "elasticity": elasticity, "plan": f"dynamic ({SOURCE_NAMES[source]})", "average_price_paid": paid,
            "congestion_pct": 100 * (out["congestion"].mean() / real_c.mean() - 1),
            "no2_pct": 100 * (out["no2"].mean() / real_n.mean() - 1),
            "pm25_pct": 100 * (out["pm25"].mean() / real_p.mean() - 1),
            "harm": h, "flat_matched_harm": matched, "gain": matched - h, "gain_low": low, "gain_high": high,
        })
        print(f"elasticity {elasticity}: {SOURCE_NAMES[source]} done")

result = pd.DataFrame(results)
result.to_csv(config.TABLES_DIR / "pricing_comparison.csv", index=False)
print(f"\nBlocks where the plan missed the price target by more than 0.05: {plan_misses}")
print("\nHarm: 1.00 = as observed, lower is better. Gain = matched flat harm minus dynamic harm (positive = dynamic wins).")
show = result.copy()
for column in ["average_price_paid", "congestion_pct", "no2_pct", "pm25_pct"]:
    show[column] = show[column].round(2)
for column in ["harm", "flat_matched_harm", "gain", "gain_low", "gain_high"]:
    show[column] = show[column].round(4)
print(show.to_string(index=False))
# The S6 table: every strategy, every elasticity, all outcomes, judged on what really happened.
# Also saves the dynamic price schedules for the cap and Pareto scripts.
import numpy as np
import pandas as pd
from ccz import config, optimiser, pricing

SOURCES = {"actual": "perfect", "model": "our model", "profile": "weekly profile", "persistence": "persistence"}
TARGET = float(config.BASE_PRICE)

table = pd.read_csv(config.TABLES_DIR / "pricing_inputs.csv")
table = table.sort_values(["local_date", "block", "price_hour"]).reset_index(drop=True)
shares = pricing.load_shares()

real_c = table["congestion_actual"].to_numpy(float)
real_n = table["no2_actual"].to_numpy(float)
real_p = table["pm25_actual"].to_numpy(float)

blocks = [(day, block, g.index.to_numpy()) for (day, block), g in table.groupby(["local_date", "block"], sort=True)]

base_vehicles = pricing.baseline_traffic(real_c)
observed_revenue = float((base_vehicles * config.BASE_PRICE).sum())


def forecast(column, source, index):
    values = table.loc[index, f"{column}_{source}"].to_numpy(float)
    if column == "congestion":
        return np.clip(values, 1.0, 100.0)
    return np.clip(values, 0.1, None)


def summarise(elasticity, plan, price):
    out = pricing.outcomes(price, elasticity, real_c, real_n, real_p, shares)
    vehicles = base_vehicles * out["traffic_ratio"]
    return {
        "elasticity": elasticity,
        "plan": plan,
        "driver_cost": out["average_price_paid"],
        "traffic_pct": 100 * (vehicles.sum() / base_vehicles.sum() - 1),
        "congestion_pct": 100 * (out["congestion"].mean() / real_c.mean() - 1),
        "no2_pct": 100 * (out["no2"].mean() / real_n.mean() - 1),
        "pm25_pct": 100 * (out["pm25"].mean() / real_p.mean() - 1),
        "revenue_pct": 100 * (out["revenue"] / observed_revenue - 1),
    }


rows, schedules = [], []
for elasticity in config.ELASTICITIES:
    for name, flat in [("flat 15", 15.0), ("flat 18", 18.0)]:
        rows.append(summarise(elasticity, name, np.full(len(table), flat)))

    for source, label in SOURCES.items():
        price = np.zeros(len(table))
        for day, block, index in blocks:
            c, n, p = (forecast(col, source, index) for col in ["congestion", "no2", "pm25"])
            x = optimiser.solve_matched(elasticity, c, n, p, shares, TARGET)
            price[index] = np.clip(x, config.PRICE_FLOOR, config.PRICE_CEILING)
        rows.append(summarise(elasticity, f"dynamic ({label})", price))
        part = table[["local_date", "block", "price_hour"]].copy()
        part["elasticity"] = elasticity
        part["source"] = label
        part["price"] = price
        schedules.append(part)
        print(f"elasticity {elasticity}: {label} done")

summary = pd.DataFrame(rows)
summary.to_csv(config.TABLES_DIR / "pricing_summary.csv", index=False)
pd.concat(schedules).to_csv(config.TABLES_DIR / "dynamic_prices.csv", index=False)

print("\nAll changes are against the observed hours at a flat 15. Driver cost is the average price paid.")
print(summary.round(2).to_string(index=False))
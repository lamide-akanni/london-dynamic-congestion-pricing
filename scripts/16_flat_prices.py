# What do flat prices do to May and June conditions under each assumed driver response?
# Realised conditions only. Flat 15 is what drivers paid, so it leaves everything unchanged.
import numpy as np
import pandas as pd
from ccz import config, pricing

ELASTICITIES = [-0.1, -0.3, -0.5]
FLAT_PRICES = [10, 15, 18]

table = pd.read_csv(config.TABLES_DIR / "pricing_inputs.csv")
shares = pricing.load_shares()
print("Traffic shares used:", shares)
print("Blocks:", table.groupby(["local_date", "block"]).ngroups, "\n")

rows = []
for elasticity in ELASTICITIES:
    results = {}
    for price in FLAT_PRICES:
        congestion, no2, pm25, revenue = [], [], [], []
        for _, block in table.groupby(["local_date", "block"]):
            out = pricing.outcomes(
                np.full(len(block), float(price)), elasticity,
                block["congestion_actual"], block["no2_actual"], block["pm25_actual"], shares,
            )
            congestion.append(out["congestion"].mean())
            no2.append(out["no2"].mean())
            pm25.append(out["pm25"].mean())
            revenue.append(out["revenue"])
        results[price] = (np.mean(congestion), np.mean(no2), np.mean(pm25), np.sum(revenue))
    base = results[15]
    for price in FLAT_PRICES:
        c, n, p, r = results[price]
        rows.append({
            "elasticity": elasticity,
            "flat_price": price,
            "traffic_change_pct": 100 * ((price / config.BASE_PRICE) ** elasticity - 1),
            "congestion_mean": c,
            "congestion_change_pct": 100 * (c / base[0] - 1),
            "no2_change_pct": 100 * (n / base[1] - 1),
            "pm25_change_pct": 100 * (p / base[2] - 1),
            "revenue_change_pct": 100 * (r / base[3] - 1),
        })

out = pd.DataFrame(rows).round(2)
print(out.to_string(index=False))
config.TABLES_DIR.mkdir(parents=True, exist_ok=True)
out.to_csv(config.TABLES_DIR / "flat_price_outcomes.csv", index=False)
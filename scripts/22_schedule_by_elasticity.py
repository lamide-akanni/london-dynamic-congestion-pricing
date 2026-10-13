# S8 check: does the shape of the best morning schedule change with the assumed driver response?
# Same typical morning as script 21, planned with perfect knowledge, average price paid fixed at 15.
import pandas as pd
from ccz import config, optimiser, pricing

table = pd.read_csv(config.TABLES_DIR / "pricing_inputs.csv")
table = table.sort_values(["local_date", "block", "price_hour"]).reset_index(drop=True)
shares = pricing.load_shares()

mornings = table[table["block"] == "morning"]
level = mornings.groupby("local_date")["congestion_actual"].mean().sort_values()
day = level.index[len(level) // 2]
one = mornings[mornings["local_date"] == day]
c, n, p = (one[f"{x}_actual"].to_numpy(float) for x in ["congestion", "no2", "pm25"])

rows = {"hour": list(one["price_hour"]), "real_congestion": c.round(1)}
for elasticity in config.ELASTICITIES:
    rows[f"price at {elasticity}"] = optimiser.solve_matched(elasticity, c, n, p, shares, 15.0).round(2)

print(f"Typical morning {day}: solver prices by assumed driver response")
print(pd.DataFrame(rows).to_string(index=False))
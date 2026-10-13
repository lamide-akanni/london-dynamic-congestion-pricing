# Try the optimiser on one morning block, planning with perfect knowledge of the hours.
# Question: does NSGA-II agree with the standard solver, and does a dynamic schedule beat flat 15?
import time

import numpy as np
import pandas as pd
from ccz import config, optimiser, pricing

ELASTICITY = -0.3
TARGET = 15.0

table = pd.read_csv(config.TABLES_DIR / "pricing_inputs.csv")
shares = pricing.load_shares()
day = table["local_date"].min()
one = table[(table["local_date"] == day) & (table["block"] == "morning")]
c, n, p = (one[f"{x}_actual"].to_numpy() for x in ["congestion", "no2", "pm25"])
print(f"Block: morning of {day}, hours {list(one['price_hour'])}")


def harm_of(prices):
    r = pricing.evaluate_many(prices, ELASTICITY, c, n, p, shares)
    return float(pricing.combined_harm(r, c, n, p)[0]), float(r["average_price_paid"][0])


harms, schedules = [], []
start = time.time()
for seed in range(1, 6):
    X, F = optimiser.pareto_prices(ELASTICITY, c, n, p, shares, seed, population=100, generations=300)
    price, _ = optimiser.pick_matched(X, F, c, n, p, TARGET)
    schedules.append(price)
    harms.append(harm_of(price)[0])
    if seed == 1:
        print(f"Trade-off set size (seed 1): {len(X)}")
print(f"Time per run: {(time.time() - start) / 5:.2f} s")

exact = optimiser.solve_matched(ELASTICITY, c, n, p, shares, TARGET)
exact_harm, exact_price = harm_of(exact)

print("\nCombined harm (1.00 = no change). Flat 15 is exactly 1.00.")
print(f"  NSGA-II, five seeds: {[round(h, 4) for h in harms]}")
print(f"  Standard solver:     {exact_harm:.4f} (average price paid {exact_price:.2f})")
print(f"  NSGA-II average price paid (seed 1): {harm_of(schedules[0])[1]:.2f}")

view = pd.DataFrame({
    "hour": one["price_hour"].to_numpy(),
    "real_congestion": c.round(1),
    "price_NSGA2_seed1": schedules[0].round(2),
    "price_solver": exact.round(2),
})
print()
print(view.to_string(index=False))
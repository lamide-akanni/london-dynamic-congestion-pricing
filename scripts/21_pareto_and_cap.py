# Part A: trade-off set (Pareto) for one typical morning, with four example strategies.
# Part B: the daily cap, shown with three stylised drivers.
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from ccz import config, optimiser, pricing

ELASTICITY = -0.3
ENTRY_MORNING, ENTRY_AFTERNOON = 8, 15
FIGURES = config.TABLES_DIR.parent / "figures"
FIGURES.mkdir(exist_ok=True)

table = pd.read_csv(config.TABLES_DIR / "pricing_inputs.csv")
table = table.sort_values(["local_date", "block", "price_hour"]).reset_index(drop=True)
shares = pricing.load_shares()

# ---------- Part A ----------
mornings = table[table["block"] == "morning"]
level = mornings.groupby("local_date")["congestion_actual"].mean().sort_values()
day = level.index[len(level) // 2]
one = mornings[mornings["local_date"] == day]
c, n, p = (one[f"{x}_actual"].to_numpy(float) for x in ["congestion", "no2", "pm25"])
print(f"Typical morning: {day}, hours {list(one['price_hour'])}, mean congestion {c.mean():.1f}")

X, F = optimiser.pareto_prices(ELASTICITY, c, n, p, shares, seed=1, population=100, generations=300)
print(f"Trade-off set size: {len(X)}")

congestion_pct = 100 * (F[:, 0] / c.mean() - 1)
pollution_ratio = (F[:, 1] / n.mean() + F[:, 2] / p.mean()) / 2
harm = pricing.combined_harm({"congestion": F[:, 0], "no2": F[:, 1], "pm25": F[:, 2]}, c, n, p)
cost_range = max(F[:, 3].max() - F[:, 3].min(), 1e-9)
harm_range = max(harm.max() - harm.min(), 1e-9)
balanced_score = (F[:, 3] - F[:, 3].min()) / cost_range + (harm - harm.min()) / harm_range

picks = {
    "lowest driver cost": int(np.argmin(F[:, 3])),
    "strongest congestion cut": int(np.argmin(F[:, 0])),
    "strongest pollution cut": int(np.argmin(pollution_ratio)),
    "balanced compromise": int(np.argmin(balanced_score)),
}

base_revenue = float((pricing.baseline_traffic(c) * config.BASE_PRICE).sum())
rows = []
plans = [("flat 15", np.full(len(c), 15.0))] + [(name, X[i]) for name, i in picks.items()]
plans.append(("dynamic at 15 (solver)", optimiser.solve_matched(ELASTICITY, c, n, p, shares, 15.0)))
for name, price in plans:
    out = pricing.outcomes(price, ELASTICITY, c, n, p, shares)
    row = {"strategy": name}
    for hour, value in zip(one["price_hour"], price):
        row[f"price_{hour}"] = round(float(value), 2)
    row["driver_cost"] = out["average_price_paid"]
    row["congestion_pct"] = 100 * (out["congestion"].mean() / c.mean() - 1)
    row["no2_pct"] = 100 * (out["no2"].mean() / n.mean() - 1)
    row["pm25_pct"] = 100 * (out["pm25"].mean() / p.mean() - 1)
    row["revenue_pct"] = 100 * (out["revenue"] / base_revenue - 1)
    rows.append(row)

strategies = pd.DataFrame(rows)
strategies.to_csv(config.TABLES_DIR / "pareto_strategies.csv", index=False)
print("\nFour example strategies on the trade-off set (changes against flat 15 on this morning):")
print(strategies.round(2).to_string(index=False))

fig, ax = plt.subplots(figsize=(8, 5))
points = ax.scatter(F[:, 3], congestion_pct, c=harm, s=18)
fig.colorbar(points, label="combined harm (1.00 = as observed)")
for name, i in picks.items():
    ax.scatter(F[i, 3], congestion_pct[i], s=90, facecolors="none", edgecolors="black")
    ax.annotate(name, (F[i, 3], congestion_pct[i]), textcoords="offset points", xytext=(6, 6), fontsize=8)
ax.scatter(15, 0, marker="x", color="black")
ax.annotate("flat 15", (15, 0), textcoords="offset points", xytext=(6, -12), fontsize=8)
ax.set_xlabel("Average price paid (£)")
ax.set_ylabel("Mean congestion against flat £15 (%)")
ax.set_title(f"Trade-off set, morning of {day} (elasticity {ELASTICITY})")
fig.tight_layout()
fig.savefig(FIGURES / "pareto_example_block.png", dpi=150)
print(f"\nChart saved to {FIGURES / 'pareto_example_block.png'}")

# ---------- Part B ----------
schedule = pd.read_csv(config.TABLES_DIR / "dynamic_prices.csv")
schedule = schedule[(schedule["source"] == "our model") & ((schedule["elasticity"] - ELASTICITY).abs() < 1e-9)]
daily = schedule.pivot_table(index="local_date", columns="price_hour", values="price")
cap = float(config.DAILY_CAP)

cap_rows = []
for plan, morning, afternoon in [
    ("flat 15", pd.Series(15.0, index=daily.index), pd.Series(15.0, index=daily.index)),
    ("flat 18", pd.Series(18.0, index=daily.index), pd.Series(18.0, index=daily.index)),
    ("dynamic (our model)", daily[ENTRY_MORNING], daily[ENTRY_AFTERNOON]),
]:
    both_uncapped = morning + afternoon
    for driver, paid in [
        ("A: enters once (08:00)", morning),
        ("B: enters twice (08:00 and 15:00), capped", np.minimum(both_uncapped, cap)),
        ("C: enters once and stays", morning),
    ]:
        cap_rows.append({
            "plan": plan, "driver": driver,
            "average_paid": paid.mean(), "lowest_day": paid.min(), "highest_day": paid.max(),
            "days_cap_applies": int((both_uncapped > cap).sum()) if driver.startswith("B") else 0,
        })

cap_table = pd.DataFrame(cap_rows)
cap_table.to_csv(config.TABLES_DIR / "cap_drivers.csv", index=False)
print(f"\nDaily cap £{cap:.0f}, three stylised drivers over {len(daily)} days (illustrations, not measured behaviour):")
print(cap_table.round(2).to_string(index=False))

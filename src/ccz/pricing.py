# Price to outcome model for the simulation.
# Own-price demand with constant elasticity, the BPR road curve, and the traffic share of pollution.
import json

import numpy as np
from ccz import config


def load_shares():
    # traffic shares measured in scripts/15_traffic_shares.py (None means 0)
    with open(config.TABLES_DIR / "traffic_shares.json") as f:
        raw = json.load(f)
    return {"no2": raw["no2"] or 0.0, "pm25": raw["pm25"] or 0.0}


def baseline_traffic(congestion):
    # Congestion is extra travel time in percent. The BPR curve says
    # congestion / 100 = alpha * (traffic / capacity) ** exponent, so we can recover
    # the traffic level (relative to capacity) that sits behind each congestion value.
    return (np.asarray(congestion, dtype=float) / 100 / config.BPR_ALPHA) ** (1 / config.BPR_EXPONENT)


def traffic_ratio(price, elasticity):
    # Traffic after the price change divided by traffic before, constant elasticity.
    return (np.asarray(price, dtype=float) / config.BASE_PRICE) ** elasticity


def outcomes(price, elasticity, congestion, no2, pm25, shares):
    # price, congestion, no2 and pm25 hold one value per priced hour.
    price = np.asarray(price, dtype=float)
    ratio = traffic_ratio(price, elasticity)
    vehicles = baseline_traffic(congestion) * ratio
    return {
        "traffic_ratio": ratio,
        "congestion": np.asarray(congestion, dtype=float) * ratio ** config.BPR_EXPONENT,
        "no2": np.asarray(no2, dtype=float) * (1 - shares["no2"] + shares["no2"] * ratio),
        "pm25": np.asarray(pm25, dtype=float) * (1 - shares["pm25"] + shares["pm25"] * ratio),
        "average_price_paid": float((vehicles * price).sum() / vehicles.sum()),
        "revenue": float((vehicles * price).sum()),
    }
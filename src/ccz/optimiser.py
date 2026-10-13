# Choosing a price schedule for one block of hours.
# NSGA-II (pymoo) finds the trade-off set. A standard solver (SLSQP) is the cross-check.
import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import Problem
from pymoo.optimize import minimize as pymoo_minimize
from scipy.optimize import minimize as scipy_minimize
from ccz import config, pricing


class BlockProblem(Problem):
    # Four things to minimise: mean congestion, mean NO2, mean PM2.5 and the average price paid.
    def __init__(self, elasticity, congestion, no2, pm25, shares):
        super().__init__(n_var=len(congestion), n_obj=4, xl=config.PRICE_FLOOR, xu=config.PRICE_CEILING)
        self.args = (elasticity, congestion, no2, pm25, shares)

    def _evaluate(self, X, out, *args, **kwargs):
        r = pricing.evaluate_many(X, *self.args)
        out["F"] = np.column_stack([r["congestion"], r["no2"], r["pm25"], r["average_price_paid"]])


def pareto_prices(elasticity, congestion, no2, pm25, shares, seed, population=60, generations=80):
    problem = BlockProblem(elasticity, congestion, no2, pm25, shares)
    result = pymoo_minimize(problem, NSGA2(pop_size=population), ("n_gen", generations), seed=seed, verbose=False)
    return np.atleast_2d(result.X), np.atleast_2d(result.F)


def pick_matched(prices, objectives, congestion, no2, pm25, target_price, tolerance=0.25):
    # From the trade-off set, keep schedules whose average price paid is close to the target
    # and take the one with the lowest combined harm. Judged on the numbers it was planned on.
    result = {"congestion": objectives[:, 0], "no2": objectives[:, 1], "pm25": objectives[:, 2]}
    harm = pricing.combined_harm(result, congestion, no2, pm25)
    gap = np.abs(objectives[:, 3] - target_price)
    near = gap <= tolerance
    if not near.any():
        near = gap == gap.min()
    index = np.where(near)[0][np.argmin(harm[near])]
    return prices[index], index


def solve_matched(elasticity, congestion, no2, pm25, shares, target_price):
    # Independent check: lowest combined harm with the average price paid fixed at the target.
    def harm(p):
        r = pricing.evaluate_many(p, elasticity, congestion, no2, pm25, shares)
        return float(pricing.combined_harm(r, congestion, no2, pm25)[0])

    def price_gap(p):
        r = pricing.evaluate_many(p, elasticity, congestion, no2, pm25, shares)
        return float(r["average_price_paid"][0] - target_price)

    n = len(congestion)
    result = scipy_minimize(
        harm, np.full(n, target_price), method="SLSQP",
        bounds=[(config.PRICE_FLOOR, config.PRICE_CEILING)] * n,
        constraints=[{"type": "eq", "fun": price_gap}],
        options={"ftol": 1e-10, "maxiter": 500},
    )
    return result.x
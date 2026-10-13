import numpy as np
import pytest
from ccz import config, pricing

SHARES = {"no2": 0.2, "pm25": 0.4}
CONGESTION = np.array([50.0, 70.0, 90.0])
NO2 = np.array([20.0, 25.0, 30.0])
PM25 = np.array([10.0, 12.0, 14.0])


def run(price, elasticity=-0.3, shares=SHARES):
    return pricing.outcomes(np.full(3, float(price)), elasticity, CONGESTION, NO2, PM25, shares)


def test_base_price_changes_nothing():
    out = run(config.BASE_PRICE)
    assert out["congestion"] == pytest.approx(CONGESTION)
    assert out["no2"] == pytest.approx(NO2)
    assert out["pm25"] == pytest.approx(PM25)


def test_higher_price_lowers_everything():
    out = run(18)
    assert (out["congestion"] < CONGESTION).all()
    assert (out["no2"] < NO2).all()
    assert (out["pm25"] < PM25).all()


def test_lower_price_raises_everything():
    out = run(10)
    assert (out["congestion"] > CONGESTION).all()
    assert (out["no2"] > NO2).all()


def test_stronger_response_has_bigger_effect():
    assert run(18, -0.5)["congestion"][0] < run(18, -0.1)["congestion"][0]


def test_congestion_formula():
    # price 18 against base 15, elasticity -0.3, exponent 4: factor 1.2 ** -1.2 = 0.8035
    out = run(18, -0.3)
    assert out["congestion"] / CONGESTION == pytest.approx(0.8035, rel=1e-3)


def test_no_traffic_share_means_pollution_unchanged():
    out = run(18, -0.3, shares={"no2": 0.0, "pm25": 0.0})
    assert out["no2"] == pytest.approx(NO2)
    assert out["pm25"] == pytest.approx(PM25)


def test_only_the_traffic_part_of_pollution_moves():
    ratio = 1.2 ** -0.3
    out = run(18, -0.3)
    assert out["no2"] == pytest.approx(NO2 * (1 - 0.2 + 0.2 * ratio))


def test_road_curve_round_trip():
    traffic = pricing.baseline_traffic(CONGESTION)
    assert 100 * config.BPR_ALPHA * traffic ** config.BPR_EXPONENT == pytest.approx(CONGESTION)


def test_flat_price_means_average_price_paid_is_that_price():
    assert run(16.0)["average_price_paid"] == pytest.approx(16.0)

def test_many_schedules_match_the_single_schedule_model():
    prices = np.array([[12.0, 15.0, 18.0], [18.0, 18.0, 10.0]])
    many = pricing.evaluate_many(prices, -0.3, CONGESTION, NO2, PM25, SHARES)
    for i, row in enumerate(prices):
        one = pricing.outcomes(row, -0.3, CONGESTION, NO2, PM25, SHARES)
        assert many["congestion"][i] == pytest.approx(one["congestion"].mean())
        assert many["no2"][i] == pytest.approx(one["no2"].mean())
        assert many["pm25"][i] == pytest.approx(one["pm25"].mean())
        assert many["average_price_paid"][i] == pytest.approx(one["average_price_paid"])


def test_combined_harm_is_one_when_nothing_changes():
    out = pricing.evaluate_many(np.full((1, 3), 15.0), -0.3, CONGESTION, NO2, PM25, SHARES)
    assert pricing.combined_harm(out, CONGESTION, NO2, PM25)[0] == pytest.approx(1.0)   
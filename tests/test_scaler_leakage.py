import numpy as np
import pandas as pd
import pytest
from ccz import models


def test_scaler_learns_from_training_rows_only():
    rng = np.random.default_rng(0)
    train = pd.DataFrame(rng.normal(0, 1, (200, 3)), columns=["a", "b", "c"])
    test = pd.DataFrame(rng.normal(10, 1, (50, 3)), columns=["a", "b", "c"])
    model = models.make_model("ridge")
    model.fit(train, train["a"] * 2)
    scaler = model.named_steps["standardscaler"]
    learned = scaler.mean_.copy()

    assert learned == pytest.approx(train.mean().to_numpy())
    assert abs(learned[0] - pd.concat([train, test]).mean().iloc[0]) > 1

    model.predict(test)
    assert scaler.mean_ == pytest.approx(learned)
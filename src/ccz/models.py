# The three models, their untuned default settings, and a way to build one with chosen settings.
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor
from ccz import config

DEFAULTS = {
    "ridge": {"alpha": 1.0},
    "random_forest": {"n_estimators": 200, "min_samples_leaf": 5},
    "xgboost": {"n_estimators": 200, "learning_rate": 0.05, "max_depth": 4,
                "subsample": 0.8, "colsample_bytree": 0.8},
}


def make_model(kind, params=None):
    params = DEFAULTS[kind] if params is None else params
    seed = config.RANDOM_SEED
    if kind == "ridge":
        return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(**params))
    if kind == "random_forest":
        return make_pipeline(
            SimpleImputer(strategy="median"),
            RandomForestRegressor(random_state=seed, n_jobs=-1, **params),
        )
    if kind == "xgboost":
        return XGBRegressor(random_state=seed, **params)
    raise ValueError(f"unknown model: {kind}")


def make_models():
    return {kind: make_model(kind) for kind in DEFAULTS}
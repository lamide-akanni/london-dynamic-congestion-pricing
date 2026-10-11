# The three models and their untuned first settings.
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor
from ccz import config


def make_models():
    seed = config.RANDOM_SEED
    return {
        "ridge": make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(alpha=1.0)),
        "random_forest": make_pipeline(
            SimpleImputer(strategy="median"),
            RandomForestRegressor(n_estimators=200, min_samples_leaf=5, random_state=seed, n_jobs=-1),
        ),
        "xgboost": XGBRegressor(n_estimators=200, learning_rate=0.05, max_depth=4,
                                subsample=0.8, colsample_bytree=0.8, random_state=seed),
    }
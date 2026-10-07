"""
Project settings.
Every date, path, name and number used in the project file lives here.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# This file is at <root>/src/ccz/config.py, so the project root is two
# folders up from the folder this file sits in.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
LOGS_DIR = PROJECT_ROOT / "logs"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
TABLES_DIR = REPORTS_DIR / "tables"

# The traffic file you place in data/raw by hand.
TOMTOM_FILE = DATA_RAW / "tomtom_london_2025H1.csv"

# ---------------------------------------------------------------------------
# Time window and splits
# ---------------------------------------------------------------------------
TIMEZONE = "Europe/London"
DATA_START = "2025-01-01"
DATA_END = "2025-06-30"

# Which TomTom areas stand in for the Congestion Charging Zone?
# And both are whole boroughs, so they are approximations of the zone.
CENTRAL_REGION = "Westminster"
CHECK_REGION = "City of London"

# Air quality and weather sources ( times are UTC).
AIR_SITES = ["WM6", "CE2", "MY1", "CE3", "BL0"]
AIR_SPECIES = ["NO2", "PM25"]
WEATHER_LATITUDE = 51.51
WEATHER_LONGITUDE = -0.13
WEATHER_VARIABLES = [
    "temperature_2m", "relative_humidity_2m", "precipitation",
    "surface_pressure", "wind_speed_10m", "wind_direction_10m", "cloud_cover",
]
LAQN_FILE = DATA_RAW / "laqn_2025H1.csv"
WEATHER_FILE = DATA_RAW / "weather_2025H1.csv"

MASTER_START = "2025-01-01 00:00"  # first hour of the master calendar, UTC
MASTER_END = "2025-06-30 22:00"  # last hour, UTC (TomTom ends at 23:00 London time = 22:00 UTC)
TOMTOM_CLEAN_FILE = DATA_PROCESSED / "tomtom_clean.csv"

# Training months are January to April. May and June are the hold-out test.
TRAIN_END = "2025-04-30 23:00"
TEST_START = "2025-05-01 00:00"

# Rolling-origin check: each month below is predicted by a model trained
# only on the months before it.
ROLLING_TEST_MONTHS = ["2025-03", "2025-04", "2025-05", "2025-06"]

# ---------------------------------------------------------------------------
# Forecasting
# ---------------------------------------------------------------------------
TARGETS = ["congestion", "no2", "pm25"]
HORIZONS = [1, 3, 6]               # hours ahead
CONGESTION_ALARM_LEVEL = 60        # "high congestion" means above this (S3)
RANDOM_SEED = 42

# ---------------------------------------------------------------------------
# Pricing simulation
# ---------------------------------------------------------------------------
CURRENT_CHARGE = 15.0              # flat daily charge during the data window (to verify)
PRICE_FLOOR = 10.0                 # lowest price the optimiser may choose
PRICE_CEILING = 18.0               # highest price the optimiser may choose
DAILY_CAP = 18.0                   # most one vehicle pays in a day

# Assumed driver response. These are scenarios, not measured values.
ELASTICITIES = [-0.1, -0.3, -0.5]
DEFAULT_ELASTICITY = -0.3

# Prices are published at these hours and cover the next block of hours.
PRICING_DECISION_HOURS = [7, 13]
HOURS_PER_DECISION = 6

# Five optimiser runs with different seeds, to measure the spread (S5, S9).
OPTIMISER_SEEDS = [1, 2, 3, 4, 5]

# Stress test: forecast error multiplied by these amounts (S7).
FORECAST_ERROR_MULTIPLIERS = [0.0, 0.5, 1.0, 1.5, 2.0]
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

# Air quality series used as model inputs (rule R6 in docs/05_cleaning_rules.md).
# CE3 NO2 and all of BL0 are downloaded but not used.
AIR_SERIES = [("WM6", "NO2"), ("WM6", "PM25"), ("CE2", "NO2"), ("CE2", "PM25"), ("MY1", "NO2")]
MAX_FILL_HOURS = 2  # gaps up to this many hours in a row are filled by a straight line (rule R8)
AIR_CLEAN_FILE = DATA_PROCESSED / "air_clean.csv"
AIR_CLEAN_LOG_FILE = DATA_PROCESSED / "air_clean_log.csv"

# The joined hourly table and the record of the run that made it (scripts/03_build_hourly_table.py).
HOURLY_FILE = DATA_PROCESSED / "hourly_clean.csv"
MANIFEST_FILE = DATA_PROCESSED / "run_manifest.json"

# Training months are January to April. May and June are the hold-out test.
# Both split times are read as UTC, the same clock as the master calendar.
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

# Which column of hourly_clean.csv each target is read from.
# Decided 10/10/2026, before any model was trained: WM6 is the main air
# site (best coverage, closest to the road). CE2 is kept as a later check.

TARGET_COLUMNS = {
    "congestion": "congestion_central",
    "no2": "wm6_no2",
    "pm25": "wm6_pm25",
}

# How far back the model may look (hours before the row's own hour).
LAG_HOURS = [1, 2, 3, 6, 12, 24]

# England bank holidays, January to June 2025 (check against gov.uk/bank-holidays).
BANK_HOLIDAYS = ["2025-01-01", "2025-04-18", "2025-04-21", "2025-05-05", "2025-05-26"]

# Weather columns the models may use. Same list as WEATHER_VARIABLES above.
WEATHER_INPUTS = WEATHER_VARIABLES

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

# The simple rule each model starts from and then corrects.
# Decided 10 October 2026 after the first look at March and April.
BASE_RULE = {"congestion": "weekly_profile", "no2": "persistence", "pm25": "persistence"}

# Practice inside the training months. Each month is predicted by a model
# trained only on earlier months. May and June are never used here.
VALIDATION_FOLDS = [("2025-03", "2025-02-28 23:00"), ("2025-04", "2025-03-31 23:00")]

# Extra input groups to test (Step 6 of the build guide).
ROLLING_HOURS = 6                      # window for the recent mean and spread
NEIGHBOUR_COLUMN = "congestion_check"  # City of London congestion, next to Westminster
NEIGHBOUR_LAGS = [0, 1, 3]             # now, 1 hour ago, 3 hours ago
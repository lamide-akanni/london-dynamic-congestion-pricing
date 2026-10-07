# Brick 19: cut the weather file (rule R10), join TomTom, air quality and weather
# into one hourly table (R1), add London-time columns (R3), run the stop-checks,
# and write a manifest that records what went into the run.
# Run scripts 01 and 02 first. Reads cleaned files, writes data/processed/hourly_clean.csv.

import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone

import pandas as pd

from ccz import config


def check(condition, message):
    # Stop the run if a check fails.
    if not condition:
        raise SystemExit(f"CHECK FAILED: {message}")
    print(f"ok: {message}")


def read_hourly(path, label):
    # Read a file that has a time_utc column and put that column in the index.
    if not path.exists():
        raise SystemExit(f"{label} not found at {path}. Run the earlier cleaning scripts first.")
    frame = pd.read_csv(path)
    frame["time_utc"] = pd.to_datetime(frame["time_utc"], utc=True)
    return frame.set_index("time_utc")


def sha256(path):
    # A fingerprint of a file. If one byte changes, the fingerprint changes.
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_info():
    # Which commit the code was at when this ran, and whether files had unsaved changes.
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True, cwd=config.PROJECT_ROOT
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, check=True, cwd=config.PROJECT_ROOT
        ).stdout.strip()
        return commit, bool(dirty)
    except (OSError, subprocess.CalledProcessError):
        return "unknown", None


calendar = pd.date_range(config.MASTER_START, config.MASTER_END, freq="h", tz="UTC")

# ---- The three inputs ----
tomtom = read_hourly(config.TOMTOM_CLEAN_FILE, "Clean TomTom file")
air = read_hourly(config.AIR_CLEAN_FILE, "Clean air quality file")
check(len(tomtom) == len(calendar) and (tomtom.index == calendar).all(), "TomTom hours match the master calendar")
check(len(air) == len(calendar) and (air.index == calendar).all(), "air quality hours match the master calendar")

# R10: weather is already clean and in UTC. Check it, then cut it to the calendar.
weather_raw = read_hourly(config.WEATHER_FILE, "Raw weather file")
check(not weather_raw.index.duplicated().any(), "weather has no duplicate hours")
check(int(weather_raw.isna().sum().sum()) == 0, "weather has no missing values")
weather = weather_raw.loc[calendar[0] : calendar[-1]]
check(len(weather) == len(calendar) and (weather.index == calendar).all(), "weather hours match the master calendar")
weather_dropped = len(weather_raw) - len(weather)
print(f"weather rows cut to the calendar: {weather_dropped}\n")

# ---- The join: one row per UTC hour ----
hourly = pd.DataFrame(index=calendar)
hourly.index.name = "time_utc"
hourly = hourly.join(tomtom).join(air).join(weather)

# R3: hour of day and day of week come from the London clock, not UTC.
london = hourly.index.tz_convert(config.TIMEZONE)
hourly["hour_london"] = london.hour
hourly["dayofweek_london"] = london.dayofweek  # Monday = 0, Sunday = 6

# ---- Checks that stop the run ----
check(len(hourly) == len(calendar), f"joined table has {len(hourly)} rows, one per calendar hour")
check(not hourly.index.duplicated().any(), "no duplicate hours in the joined table")
check(hourly["congestion_central"].notna().all(), "no missing Westminster congestion")
check(int(hourly["hour_london"].iloc[0]) == 0 and int(hourly["hour_london"].iloc[-1]) == 23,
      "London hour runs from 0 on the first row to 23 on the last")

# Every London hour should appear 181 times (one per day, 1 Jan to 30 Jun),
# except 01:00, which is missing once because of the spring clock change.
per_hour = hourly["hour_london"].value_counts()
check(per_hour.drop(1).eq(181).all() and per_hour[1] == 180,
      "each London hour appears 181 times, except 01:00 which appears 180 times")

# ---- Save ----
config.DATA_PROCESSED.mkdir(exist_ok=True)
hourly.reset_index().to_csv(config.HOURLY_FILE, index=False)

missing = hourly.isna().sum()
missing = {column: int(count) for column, count in missing.items() if count > 0}
print("\nColumns with empty hours:")
for column, count in missing.items():
    print(f"  {column}: {count} ({100 * count / len(hourly):.1f}%)")

# ---- Manifest: what went in, what came out, and how it was made ----
commit, dirty = git_info()
inputs = {
    "tomtom_raw": config.TOMTOM_FILE,
    "laqn_raw": config.LAQN_FILE,
    "weather_raw": config.WEATHER_FILE,
    "tomtom_clean": config.TOMTOM_CLEAN_FILE,
    "air_clean": config.AIR_CLEAN_FILE,
}
manifest = {
    "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    "git_commit": commit,
    "uncommitted_changes": dirty,
    "python": platform.python_version(),
    "pandas": pd.__version__,
    "master_calendar": {
        "start_utc": str(calendar[0]),
        "end_utc": str(calendar[-1]),
        "hours": len(calendar),
    },
    "split_times_read_as_utc": {"train_end": config.TRAIN_END, "test_start": config.TEST_START},
    "inputs": {
        name: {"file": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)}
        for name, path in inputs.items()
        if path.exists()
    },
    "weather_rows_cut": weather_dropped,
    "output": {
        "file": config.HOURLY_FILE.name,
        "rows": len(hourly),
        "columns": list(hourly.columns),
        "sha256": sha256(config.HOURLY_FILE),
    },
    "empty_hours_per_column": missing,
}
if config.AIR_CLEAN_LOG_FILE.exists():
    manifest["air_cleaning_counts"] = pd.read_csv(config.AIR_CLEAN_LOG_FILE).to_dict("records")

with open(config.MANIFEST_FILE, "w") as handle:
    json.dump(manifest, handle, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o))

print(f"\nSaved {len(hourly)} rows x {hourly.shape[1]} columns -> {config.HOURLY_FILE.name}")
print(f"Saved manifest -> {config.MANIFEST_FILE.name}")

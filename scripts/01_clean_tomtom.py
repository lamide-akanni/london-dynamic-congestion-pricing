# Brick 17: clean the TomTom file (rules R1 to R5 in docs/05_cleaning_rules.md).
# Reads data/raw (never edits it) and writes data/processed/tomtom_clean.csv.
# Stops with a message if any check fails.

import pandas as pd

from ccz import config


def check(condition, message):
    # Stop the run if a check fails.
    if not condition:
        raise SystemExit(f"CHECK FAILED: {message}")
    print(f"ok: {message}")


# The master calendar: every hour we keep, in UTC (rule R1).
calendar = pd.date_range(config.MASTER_START, config.MASTER_END, freq="h", tz="UTC")

raw = pd.read_csv(config.TOMTOM_FILE)

# R2: the Time column is London local time. Say so, then convert to UTC.
# "raise" means the script stops if it ever meets a clock-change hour it cannot place.
local = pd.to_datetime(raw["Time"]).dt.tz_localize(
    config.TIMEZONE, ambiguous="raise", nonexistent="raise"
)
raw["time_utc"] = local.dt.tz_convert("UTC")

# R4: keep Westminster (central) and City of London (check). Drop the other 12 boroughs.
keep = [config.CENTRAL_REGION, config.CHECK_REGION]
raw = raw[raw["Region label"].isin(keep)]

# One row per hour, one column per borough.
wide = raw.pivot(index="time_utc", columns="Region label", values="Congestion level [%]")
wide = wide.rename(
    columns={config.CENTRAL_REGION: "congestion_central", config.CHECK_REGION: "congestion_check"}
)
wide = wide.sort_index()

# Show the clock change, so we can see R2 working.
print("\nHours around the spring clock change (UTC):")
print(wide.loc["2025-03-29 23:00":"2025-03-30 02:00"])
print()

# Checks that stop the run.
check(not wide.index.duplicated().any(), "no duplicate hours")
check(len(wide) == len(calendar), f"{len(wide)} rows, calendar has {len(calendar)} hours")
check((wide.index == calendar).all(), "every hour matches the master calendar")
check(not wide.isna().any().any(), "no missing congestion values")

# R5: zeros and values above 100 are kept. Count them for the run log.
for column in wide.columns:
    print(
        f"{column}: zeros = {(wide[column] == 0).sum()}, above 100 = {(wide[column] > 100).sum()}, "
        f"min = {wide[column].min():.1f}, median = {wide[column].median():.1f}, max = {wide[column].max():.1f}"
    )

config.DATA_PROCESSED.mkdir(exist_ok=True)
wide.reset_index().to_csv(config.TOMTOM_CLEAN_FILE, index=False)
print(f"\nSaved {len(wide)} rows -> {config.TOMTOM_CLEAN_FILE.name}")

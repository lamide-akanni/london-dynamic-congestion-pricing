# Brick 18: clean the air quality file (rules R6 to R9 in docs/05_cleaning_rules.md).
# Reads data/raw (never edits it) and writes data/processed/air_clean.csv
# plus a count table, air_clean_log.csv. Stops with a message if any check fails.

import numpy as np
import pandas as pd

from ccz import config


def check(condition, message):
    # Stop the run if a check fails.
    if not condition:
        raise SystemExit(f"CHECK FAILED: {message}")
    print(f"ok: {message}")


def fill_short_gaps(series, max_gap, train_end):
    # Rule R8. Walk along the series, find each run of missing hours, and decide.
    #   - run of max_gap hours or fewer, with a reading on both sides: straight-line fill
    #   - longer run: leave empty
    #   - run at the very start or end (no reading on one side): leave empty
    #   - run that starts in training and ends in test: leave empty, so no test
    #     reading is ever used to fill a training hour
    result = series.copy()
    index = series.index
    missing = series.isna().to_numpy()
    counts = {"filled": 0, "left_long": 0, "left_edge": 0, "left_split": 0}

    i = 0
    while i < len(series):
        if not missing[i]:
            i += 1
            continue
        start = i
        while i < len(series) and missing[i]:
            i += 1
        end = i  # first position after the gap
        length = end - start

        if start == 0 or end == len(series):
            counts["left_edge"] += length
        elif length > max_gap:
            counts["left_long"] += length
        elif index[start] <= train_end < index[end]:
            counts["left_split"] += length
        else:
            before = series.iloc[start - 1]
            after = series.iloc[end]
            result.iloc[start:end] = np.linspace(before, after, length + 2)[1:-1]
            counts["filled"] += length
    return result, counts


# The master calendar and the split line, both in UTC.
calendar = pd.date_range(config.MASTER_START, config.MASTER_END, freq="h", tz="UTC")
train_end = pd.Timestamp(config.TRAIN_END, tz="UTC")

raw = pd.read_csv(config.LAQN_FILE)
raw["time_utc"] = pd.to_datetime(raw["time_utc"], utc=True)

# Checks on the raw file before we touch anything.
check(
    not raw.duplicated(subset=["site", "species", "time_utc"]).any(),
    "no duplicate readings in the raw file",
)
check(raw["time_utc"].min() >= calendar[0], "no readings before the master calendar starts")
check(
    (raw["time_utc"] <= calendar[-1] + pd.Timedelta(hours=1)).all(),
    "nothing later than one hour after the master calendar ends",
)
after_end = int((raw["time_utc"] > calendar[-1]).sum())
print(f"readings after the master calendar ends (dropped, rule R1): {after_end}\n")

columns = {}
log_rows = []

# R6: only the chosen site and pollutant pairs. Each keeps its own column (R9).
for site, species in config.AIR_SERIES:
    name = f"{site.lower()}_{species.lower()}"
    part = raw[(raw["site"] == site) & (raw["species"] == species)]

    # Put the readings on the full hourly calendar. Hours with no reading become empty.
    series = part.set_index("time_utc")["value"].reindex(calendar)
    present_raw = int(series.notna().sum())

    # R7: negative readings become 0, and we count them.
    negatives = int((series < 0).sum())
    series = series.clip(lower=0)

    # R8: fill short gaps only.
    series, counts = fill_short_gaps(series, config.MAX_FILL_HOURS, train_end)
    present_final = int(series.notna().sum())

    check(present_final == present_raw + counts["filled"], f"{name}: hours add up")
    check(not (series < 0).any(), f"{name}: no negative values left")

    columns[name] = series
    log_rows.append(
        {
            "series": name,
            "calendar_hours": len(calendar),
            "readings_in_raw": present_raw,
            "negatives_set_to_0": negatives,
            "hours_filled": counts["filled"],
            "left_empty_long_gap": counts["left_long"],
            "left_empty_at_edge": counts["left_edge"],
            "left_empty_at_split": counts["left_split"],
            "readings_final": present_final,
            "share_final_pct": round(100 * present_final / len(calendar), 1),
        }
    )

air = pd.DataFrame(columns, index=calendar)
air.index.name = "time_utc"

check(not air.index.duplicated().any(), "no duplicate hours in the output")
check((air.index == calendar).all(), "output hours match the master calendar")

log = pd.DataFrame(log_rows)
print("\nWhat the cleaning did, per series:")
print(log.to_string(index=False))

config.DATA_PROCESSED.mkdir(exist_ok=True)
air.reset_index().to_csv(config.AIR_CLEAN_FILE, index=False)
log.to_csv(config.AIR_CLEAN_LOG_FILE, index=False)
print(f"\nSaved {len(air)} rows -> {config.AIR_CLEAN_FILE.name}")
print(f"Saved counts -> {config.AIR_CLEAN_LOG_FILE.name}")

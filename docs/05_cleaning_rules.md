# Cleaning rules

Status: draft, 7 October 2026. The rules are written before the cleaning code.
Raw files in data/raw are never edited. Every rule below is applied by code
that reads the raw files and writes new files into data/processed.

## Which rules run before the split, and which do not

Rules that do not learn anything from the data (fixing types, time zones,
removing duplicates, joining tables) run once on the whole period.
Anything that learns from the data (averages, scaling, percentile cutoffs,
thresholds, models) is fitted on the training months only (Jan to Apr).
Nothing in this document learns from the data, so everything here is safe
to run before the split.

## Time

R1. All joins use UTC. The master calendar is every hour from
    2025-01-01 00:00 UTC to 2025-06-30 22:00 UTC (4,343 hours).
    Why it ends at 22:00: the last TomTom row is 30 June 23:00 London time,
    which is 22:00 UTC. The air and weather files run one hour longer, and
    that last hour is dropped.

R2. TomTom times are London local time. Convert them to UTC before joining.
    London was on GMT until 30 March 2025 and on BST (UTC+1) after it.
    The hour missing from TomTom on 30 March (01:00 local) does not exist on
    the clock, so it leaves no gap in UTC. Expected result: 4,343 TomTom rows
    per borough, matching the master calendar exactly. If the numbers differ,
    the run stops (see the checks below).

R3. Hour of day, day of week and the charging window are built from London
    time, not UTC, because the charge follows the London clock.

## TomTom congestion

R4. Westminster is the central series. City of London is kept as a separate
    check column. The other 12 boroughs are not used in the model.

R5. Congestion values of 0 are kept. 0 means no delay compared with free flow.
    Values above 100 are kept too (the maximum is 170). They are real
    readings of very slow traffic. Both are counted in the run log.
    Whether the 170 rows look believable is checked in EDA on training months.

## Air quality (LAQN)

R6. Sites used: WM6 and CE2 for NO2 and PM2.5, MY1 for NO2 only (secondary).
    CE3 NO2 and BL0 are not used as inputs (see doc 04).

R7. Negative readings are set to 0 and counted per site and pollutant.
    A small negative value is instrument noise around zero, not a real
    negative concentration.

R8. Gaps are handled per site and pollutant, on the master calendar:
    - A gap of 1 or 2 hours in a row is filled by a straight line between
      the readings on either side.
    - A gap of 3 hours or more is left empty and counted. The model rows that
      depend on it are dropped later, not invented.
    - No fill crosses the split line (TRAIN_END / TEST_START in config).
      A gap that touches that line is left empty, so no test value is used
      to fill a training row.

R9. Readings are never averaged across sites in this step. Each site keeps
    its own column. A combined central NO2 or PM2.5 value, if we use one,
    is built later in feature engineering and the choice is logged.

## Weather

R10. Weather is already clean (4,344 rows, no gaps, no duplicates) and in UTC.
     It is only cut to the master calendar.

## Checks that stop the run

The cleaning script must stop with a clear message, if any of
these fail:
- the master calendar has duplicate or missing hours
- TomTom has more or fewer than 4,343 rows for Westminster after conversion
- any joined column has timestamps outside the master calendar
- a pollutant value is still negative after R7
- the output has duplicate rows for the same hour

## What the run records

A run log with counts: negatives set to 0, hours filled (R8), hours left
empty, rows dropped, and the final shape. Saved with the cleaned file so the
numbers in the report come from the run, not from memory.

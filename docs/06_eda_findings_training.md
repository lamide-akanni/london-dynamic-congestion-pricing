# EDA findings, training months (January to April 2025)

10 October 2026. Source: scripts/04_eda_training_summary.py, parts 1 to 8.

## Scope

- Only the 2,880 training hours (1 January to 30 April 2025)
- May and June (the test months) were not used for any of these findings.
- Nothing here changes a threshold, a split or a cleaning rule. It only describes the data.
- Congestion is the Westminster series, which is a borough-level proxy for the Central zone.

## Findings

### 1. Zeros are night-time free flow
Congestion is at or near zero between 02:00 and 05:00. At 04:00 the median is 0.0 and 88.3% of hours are exactly zero. Zeros are real free-flow hours, not missing data.

### 2. Westminster congestion is a broad daytime plateau
From 11:00 to 17:00 the median sits at about 60 to 64. The average day peaks at 12:00 (62.2) and stays between 59 and 62 until 18:00, then falls (48.2 at 19:00, 36.3 at 20:00). Because the daily shape is so regular, a simple hour-of-day profile will be a hard baseline to beat.

### 3. Where a forecast could add value
The clock alone cannot decide hours where high congestion happens only some of the time. For example, 27.5% of hours at 08:00 and 48.3% at 10:00 reach 60 or more, against 61.7% at 12:00. These in-between hours are where forecasts have room to help.

### 4. Weekdays are heavier than weekends, but not hugely
Weekday (2,065 hours): mean 38.5, 75th percentile 62.3, maximum 103.2.
Weekend (815 hours): mean 32.5, 75th percentile 51.2, maximum 81.1.

### 5. Share of hours at or above each level (threshold review)
| Level | Westminster | City of London |
|---|---|---|
| 50 | 38.1% | 36.1% |
| 60 | 24.3% | 28.0% |
| 70 | 8.7% | 21.8% |

Decision (already logged in doc 02): keep 60 as high congestion, and report the alarm result at 50, 60 and 70.

### 6. City of London follows Westminster but has a heavier top end
Hourly correlation is 0.88 and the correlation of the average daily shapes is 0.96. Both are strong, not perfect. The daily shape is closer because averaging removes day-to-day noise. City of London has 130 hours above 100, Westminster has 4. It is a useful check series but not the same size.

### 7. The two main air sites agree
WM6 against CE2: NO2 0.83, PM2.5 0.95. PM2.5 agrees more, which fits fine particles spreading across an area while NO2 stays closer to the road. This is a plausible reading, not a tested one.

### 8. Congestion and pollution are only weakly linked
Correlation of Westminster congestion now with WM6 pollution later:
| Hours later | NO2 | PM2.5 |
|---|---|---|
| 0 | 0.21 | -0.04 |
| 1 | 0.23 | -0.04 |
| 3 | 0.22 | -0.05 |
| 6 | 0.15 | -0.03 |

NO2 shows a weak positive link (about 5% shared movement at best). PM2.5 shows no link at all.

### 9. The daily shapes do not line up
Congestion peaks between 11:00 and 18:00 and stays flat, while NO2 rises from 31.9 (11:00) to 42.1 (18:00) and peaks at 43.6 at 20:00, after congestion has fallen. NO2 never drops below about 26, even at 04:00. PM2.5 stays in a narrow band from 21.7 to 26.2 all day, lowest in the afternoon.

## What this means for the modelling

- Hour-of-day (and hour-of-week) profile baselines will be strong for congestion and for NO2.
- Persistence will probably be strong for pollution at 1 hour, because pollution changes slowly.
- Congestion features are not expected to help PM2.5 much, and only modestly for NO2. We will test this and not assume it.
- A model that only matches the baselines is a finding, not a failure.

## What this means for the pricing simulation

The pricing simulation assumes less congestion means less pollution. This data supports that link only weakly at hourly level, and the highest-congestion hours are not the highest-NO2 hours. Pollution results from the simulation depend on that assumption and must be reported that way.

## What we did not conclude

- These are plain hour-by-hour correlations. Weather and outside background pollution are not removed.
- January to April only. The plan notes NO2 falls into summer, and we have not looked at the test months.
- We do not claim traffic has no effect on pollution. We only say this data shows a weak link.


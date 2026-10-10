# 04. Data dictionary: Air Quality and Weather Files

## Air quality: `data/raw/laqn_2025H1.csv`

Source: London Air Quality Network (Imperial College London, Environmental Research Group), by API. Downloaded 6 October 2026 with `scripts/00_download_air_weather.py`.

### Shape

- 30,344 rows and 4 columns. One row is one site, one pollutant, one hour.
- No duplicate rows.
- First reading 2025-01-01 00:00, last reading 2025-06-30 23:00 (UTC).
- Rows only exist where the site reported a value. The file has no empty rows for missing hours.

### Columns

| Column | Type | Unit | Meaning |
|---|---|---|---|
| site | text | none | LAQN site code: WM6, CE2, MY1, CE3, BL0 |
| species | text | none | NO2 (nitrogen dioxide) or PM25 (fine particles, PM2.5) |
| time_utc | date and time | UTC (GMT) | Time of the reading. Whether it marks the start or end of the hour is to be confirmed |
| value | decimal | probably micrograms per cubic metre, to confirm | Measured concentration |

### Sites (from the LAQN site records, checked 7 October 2026)

| Site | Name | Type | Borough | Opened | Pollutants measured |
|---|---|---|---|---|---|
| WM6 | Westminster - Oxford Street | Kerbside | Westminster | 2011 | NO2 since Jan 2016, PM25 since Feb 2024. Closed 1 April 2026 |
| CE2 | Waterloo Place (The Crown Estate) | Roadside | Westminster | Dec 2020 | NO2 since Sep 2021, PM25 since Dec 2020 |
| CE3 | Regent Street (The Crown Estate) | Roadside | Westminster | Nov 2022 | NO2 and PM25 since Oct 2022 |
| MY1 | Westminster - Marylebone Road | Kerbside | Westminster | 1997 | NO2. No PM25 |
| BL0 | Camden - Bloomsbury | Urban Background | Camden | 1992 | NO2 and PM25 since Dec 2007 |

Data manager for all five: King's College London. Kerbside means the instrument is at the kerb, roadside means a few metres back, and urban background means away from direct road emissions.

### Coverage (share of the 4,344 hours with a reading)

| Site | NO2 | PM25 | Note |
|---|---|---|---|
| WM6 | 98.9% | 98.4% | Longest gap 37 hours |
| CE2 | 99.2% | 96.7% | PM25 longest gap 112 hours |
| MY1 | 80.5% | none | The station does not measure PM25 |
| CE3 | 24.8% | 91.9% | NO2 instrument is listed since 2022, so the low coverage is missing data. PM25 first reading 15 January 2025 |
| BL0 | 54.0% | 54.1% | Instruments listed since 2007, but the first reading in the file is 25 March 2025. Reason unknown |

### Known issues

- Negative values: 6 at CE2 NO2 (lowest -0.7) and 6 at MY1 NO2 (lowest -1.9). Small instrument noise. The cleaning rule sets them to 0 and counts them.
- Download correction: the first download missed the last day of every month, because the LAQN end date is not included. The script now asks up to the first day of the next month. Rows went from 29,294 to 30,344.
- WM6 closed on 1 April 2026. This does not affect January to June 2025, but a live or longer version of the work could not use it.

## Weather: `data/raw/weather_2025H1.csv`

Source: Open-Meteo historical weather API, one point in central London (latitude 51.51, longitude -0.13). Downloaded 6 October 2026 with the same script.

### Shape

- 4,344 rows and 8 columns. One row is one hour.
- No missing values, no duplicate times, every step exactly one hour.
- First row 2025-01-01 00:00, last row 2025-06-30 23:00 (UTC).

### Columns (Open-Meteo default units, to confirm against their documentation)

| Column | Unit | Range in the file |
|---|---|---|
| time_utc | UTC | 2025-01-01 00:00 to 2025-06-30 23:00 |
| temperature_2m | degrees Celsius | -4.5 to 32.0 |
| relative_humidity_2m | percent | 17 to 100 |
| precipitation | millimetres | 0.0 to 4.2 |
| surface_pressure | hectopascals | 968.0 to 1040.3 |
| wind_speed_10m | kilometres per hour | 0.0 to 33.5 |
| wind_direction_10m | degrees | 1 to 360 |
| cloud_cover | percent | 0 to 100 |

## Decisions (7 October 2026)

- Main air quality sites: WM6 and CE2, for both NO2 and PM25.
- MY1 is kept as a secondary NO2 site. It does not measure PM25.
- CE3 NO2 is excluded because it has almost no readings from January to May.
- BL0 has no readings before 25 March 2025, so it is not a model input. It may support descriptive work later.
- All sources are joined on UTC. TomTom is converted from London time first.

## To check

- Whether LAQN time marks the start or the end of the hour (this affects how air quality lines up with TomTom by one hour).
- Units for NO2 and PM25 and the weather columns, from the source documentation.
- Where the long gaps sit in time (CE2 PM25 112 hours, WM6 37 hours).
- Whether the zero readings at WM6 PM25 and BL0 NO2 are real or a floor.
- Spikes, before anything is called an outlier.
- Whether Marylebone Road lies on the zone boundary (outside the charge) on TfL's map.

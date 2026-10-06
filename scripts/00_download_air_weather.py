"""Download hourly air quality (LAQN) and weather (Open-Meteo).
Writes two files into data/raw, 
"""

import time

import pandas as pd
import requests

from ccz import config

LAQN_URL = (
    "https://api.erg.ic.ac.uk/AirQuality/Data/SiteSpecies/"
    "SiteCode={site}/SpeciesCode={species}/StartDate={start}/EndDate={end}/Json"
)
WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"


def get(url, params=None):
    """Try a request up to 3 times. Return the response, or None if it fails."""
    for attempt in range(3):
        try:
            response = requests.get(url, params=params, timeout=90)
        except requests.RequestException as error:
            print(f"  attempt {attempt + 1} failed: {error}")
            time.sleep(3)
            continue
        if response.status_code == 200:
            return response
        print(f"  HTTP {response.status_code} for {url[:100]}")
        return None
    return None


# ---- Air quality: one request per site, species and month ----
rows = []
month_starts = pd.date_range(config.DATA_START, config.DATA_END, freq="MS")
data_end = pd.Timestamp(config.DATA_END)

for site in config.AIR_SITES:
    for species in config.AIR_SPECIES:
        count = 0
        for month in month_starts:
            start = month.strftime("%Y-%m-%d")
            end = min(month + pd.offsets.MonthEnd(0), data_end).strftime("%Y-%m-%d")
            response = get(LAQN_URL.format(site=site, species=species, start=start, end=end))
            if response is None:
                continue
            try:
                data = response.json()["RawAQData"]["Data"]
            except (KeyError, ValueError):
                continue
            if isinstance(data, dict):  # a month with one reading comes back as a dict
                data = [data]
            for item in data:
                value = item.get("@Value", "")
                if value not in ("", None):
                    rows.append((site, species, item["@MeasurementDateGMT"], float(value)))
                    count += 1
        print(f"{site} {species}: {count} hourly values")

air = pd.DataFrame(rows, columns=["site", "species", "time_utc", "value"])
air.to_csv(config.LAQN_FILE, index=False)
print(f"\nAir quality rows saved: {len(air)} -> {config.LAQN_FILE.name}")

# ---- Weather: one request for the whole period ----
params = {
    "latitude": config.WEATHER_LATITUDE,
    "longitude": config.WEATHER_LONGITUDE,
    "start_date": config.DATA_START,
    "end_date": config.DATA_END,
    "timezone": "UTC",
    "hourly": ",".join(config.WEATHER_VARIABLES),
}
response = get(WEATHER_URL, params=params)
if response is None:
    print("Weather download failed.")
else:
    weather = pd.DataFrame(response.json()["hourly"]).rename(columns={"time": "time_utc"})
    weather.to_csv(config.WEATHER_FILE, index=False)
    print(f"Weather rows saved: {len(weather)} -> {config.WEATHER_FILE.name}")
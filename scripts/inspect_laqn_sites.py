"""Brick 15: print the LAQN details of our five monitoring sites.

This script only reads from the LAQN website. It changes nothing on disk.
"""

import requests

from ccz import config

BASE = "https://api.erg.ic.ac.uk/AirQuality/Information/"
URLS = {
    "sites": BASE + "MonitoringSites/GroupName=London/Json",
    "site species": BASE + "MonitoringSiteSpecies/GroupName=London/Json",
}


def walk(node):
    """Go through any nested JSON and hand back every dictionary inside it."""
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)


def plain(item):
    """Keep only the simple fields of a dictionary (no nested lists or dictionaries)."""
    return {key: value for key, value in item.items() if not isinstance(value, (dict, list))}


for name, url in URLS.items():
    print("=" * 20, name.upper(), "=" * 20)
    try:
        response = requests.get(url, timeout=90)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as error:
        print(f"Could not load the {name} list: {error}")
        continue

    found = 0
    for site in (d for d in walk(data) if "@SiteCode" in d):
        if site["@SiteCode"] not in config.AIR_SITES:
            continue
        found += 1
        print()
        for key, value in plain(site).items():
            print(f"  {key}: {value}")
        for species in (d for d in walk(site) if "@SpeciesCode" in d):
            print("  species:", plain(species))
    if found == 0:
        print("No matching sites found. Top of the reply:", list(data)[:5] if isinstance(data, dict) else type(data))
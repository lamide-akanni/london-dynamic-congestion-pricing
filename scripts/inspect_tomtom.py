"""The raw TomTom file, Print what is in it.
This script only reads. It changes nothing.
"""

import pandas as pd

from ccz import config

df = pd.read_csv(config.TOMTOM_FILE)

print("ROWS AND COLUMNS")
print(df.shape)

print("\nCOLUMN NAMES AND TYPES")
print(df.dtypes)

print("\nFIRST 5 ROWS")
print(df.head().to_string())

print("\nMISSING VALUES PER COLUMN")
print(df.isna().sum())

print("\nDUPLICATE ROWS")
print(df.duplicated().sum())

print("\nROWS PER REGION")
print(df["Region label"].value_counts())

df["Time"] = pd.to_datetime(df["Time"])

print("\nTIME RANGE")
print("First:", df["Time"].min())
print("Last: ", df["Time"].max())

print("\nTIME STEPS THAT ARE NOT EXACTLY ONE HOUR (per region)")
for name, group in df.groupby("Region label"):
    steps = group["Time"].sort_values().diff().dropna()
    odd = steps[steps != pd.Timedelta(hours=1)]
    print(name, ":", len(odd), "odd steps")
    if len(odd) > 0:
        print(odd.head(10))

print("\nSUMMARY OF THE NUMBERS")
print(df.describe().to_string())
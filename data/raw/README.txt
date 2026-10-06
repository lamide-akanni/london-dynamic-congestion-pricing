RAW DATA FOLDER
Files here are exactly as received, raw data.
Cleaned versions are written to data/processed by the pipeline.

These files are not in the GitHub repository (see .gitignore), because of
size and licence terms. To rerun the project, place the files listed below
in this folder.

FILE 1: tomtom_london_2025H1.csv
What it is: Traffic congestion data for central London (TomTom).
Original file name: London - smaller area, UK.csv (from london-uk.zip)
Where it came from: https://docs.tomtom.com/
Date downloaded: 04/10/2026
Terms of use: TomTom provides the city datasets as free downloadable CSV data.  
Period covered: 01 January 2025 – 30 June 2025 (2025 H1)
Time interval and units or Granularity: Hourly observations.(`YYYY-MM-DDTHH:MM`), 
Hourly rows for 14 London boroughs.
Time is London local time with no time zone marker. 
One hour is absent on 30 March 2025 where the clocks went forward
with traffic measurements reported for each area at hourly intervals.

FILE 2: air quality (NO2 and PM2.5), London Air Quality Network
To be downloaded by a script later. Details to be added.

FILE 3: weather, Open-Meteo
To be downloaded by the same script. Details to be added.
# 03. Data dictionary: TomTom traffic file

File: `data/raw/tomtom_london_2025H1.csv`. Original name: London - smaller area, UK.csv.

## Shape

- 60,802 rows and 7 columns.
- 14 London areas, each with 4,343 hourly rows.
- First row 2025-01-01 00:00, last row 2025-06-30 23:00.
- No missing values and no duplicate rows.

## Columns

| Column | Type | Unit | Meaning |
|---|---|---|---|
| Region index | whole number | none | Code from 0 to 13 for each area |
| Region label | text | none | Name of the London borough |
| Time | text, ISO 8601 | London local time | Start of the hour. No time zone marker in the file |
| Speed [kmh] | decimal | km per hour | Average speed in the area during the hour. Range 7.3 to 48.0 |
| Free flow speed [kmh] | decimal | km per hour | Typical speed with no traffic. Changes a little from hour to hour. Range 17.7 to 48.1 |
| Congestion level [%] | decimal | percent | Extra travel time compared with free flow. Range 0 to 170. Can exceed 100 |
| Travel time per 10 km [min] | decimal | minutes | Time to cover 10 km at that speed. Range 12.4 to 81.1 |

The congestion level matches (free flow speed divided by speed, minus 1) times 100 on the first rows. To be confirmed against TomTom's documentation.

## Time

- Rows are hourly.
- One hour is absent in every area, at the same point (30 March 2025, when UK clocks went forward). This is the clock change, not missing data.
- When joined to other sources, times are converted to UTC. Hour of day and the charging window are built in London time.

## Limits

- Areas are boroughs, not the Congestion Charge Zone itself.
- The file holds speeds, not vehicle counts or entries into the zone.
- Congestion level is based on speed, so it is a measure of delay, not of traffic volume.


## Decisions 

- Central series: Westminster. This is a borough-level stand-in for the Congestion Charging Zone, not the zone itself. Westminster extends well beyond the zone, and the zone also covers parts of other boroughs.
- Check series: City of London. Every main result is also run on this area. If the two agree, the finding does not depend on one borough.
- High congestion definition: congestion level above 60 to start with. This is provisional. It is reviewed during EDA using January to April only. Any change is logged in doc 02 with the date and the reason. S3 is also reported at 50 and 70.
- Time: sources are joined on UTC. Hour of day and the charging window are built in London time.

## To check during cleaning

- How many hours have congestion level exactly 0 (a possible floor).
- The highest congestion values (170 and nearby) and whether they are real.
- Whether Westminster and City of London move together hour by hour.
- Exact zone boundary, charge and operating hours, from TfL.
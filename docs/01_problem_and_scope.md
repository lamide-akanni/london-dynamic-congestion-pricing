# 01. Problem and scope

## The problem

London's Congestion Charge is one daily fee per vehicle. Once a vehicle has paid for the day, it can enter and leave the zone as many times as it likes without paying again.

But traffic and air quality change hour by hour. 08:00 can be heavily congested with high roadside NO₂. 11:00 can be much quieter. A single daily fee does not respond to that.

## The question behind the project

**Could a charge that changes with forecast conditions, and is published before the journey, reduce congestion and pollution while keeping the cost to drivers reasonable?**

To publish a price in advance, you first need to know what the next few hours will look like. So the first thing this project tests is whether congestion, NO₂ and PM₂.₅ can be forecast 1, 3 and 6 hours ahead well enough to set a price. The second is whether prices chosen from those forecasts do better than a flat daily charge.

## Who the output is for

- Transport and policy analysts who want to know whether forecast-based pricing is worth studying further.
- Data science and machine learning reviewers, who will judge the method and how honestly it is reported.
- Researchers who may take the research agenda forward.

It is not written for TfL to adopt. This is a simulation and decision-support study, not a proposal for implementation.

## The decision this project supports

At 07:00 and 13:00 on a weekday: what hourly prices should be published for the next six hours?

A smaller second decision: which upcoming hours should be flagged as high congestion?

## Scope

- Forecasting congestion, NO₂ and PM₂.₅ at 1, 3 and 6 hours ahead.
- Hour-of-entry pricing, published in advance, with one charge per day and a daily cap represented in the simulation.
- Driver response to price shown as three scenarios (low, moderate, high), because the data cannot measure it.
- Comparison with a flat daily charge.

## Future research

- Per-entry pricing with a daily cap, and time-in-zone charging. These need entry and exit records we do not have.
- Satellite or distance-based charging.
- Measuring real price response from past price changes.
- Fairness, CO₂, revenue detail and traffic displacement outside the zone.
- A live, real-time system.

## Limits 

1. **NO₂ is not just traffic.** It also depends on weather, wind, background pollution and other sources. We do not assume more traffic means proportionally more NO₂.
2. **Traffic displacement.** Less congestion inside the zone does not automatically mean less congestion across London.
3. **Fairness.** A £10 charge does not weigh the same on every driver. We cannot study this without income and travel data.

## What this project does not claim

- That we invented dynamic road pricing or the daily cap. Other cities already use variable and per-passage charging.
- That we measured how drivers respond to price.
- That the results should be implemented.


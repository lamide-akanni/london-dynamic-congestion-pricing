# Dynamic congestion pricing for London: Central Zone

Report. Olamide Akanni, October 2026.

Live dashboard: [london-congestion-pricing.streamlit.app](https://london-congestion-pricing.streamlit.app)

## Executive summary

London's Congestion Charge is one flat daily fee, but traffic and air quality change hour by hour. This project asked whether an hourly charge, set from forecasts and published in advance, could reduce congestion and air pollution while keeping costs reasonable for drivers.

Using six months of hourly data (January to June 2025) for central London, machine learning models forecast congestion, NO₂ and PM₂.₅ 1, 3 and 6 hours ahead. The forecasts were scored once on unseen months (May and June). Hourly prices were then chosen by an optimiser in a simulation, under three assumed levels of driver response.

Congestion forecasts were strong: 33% to 48% fewer errors than the best simple rule. Pollution forecasts were not: they barely beat simple rules. In the pricing simulation, hourly prices at the same £15 average cut congestion by under half a percent, while a flat £18 charge cut it by about 20%. The price level matters far more than hourly timing, and a simple weekly-average forecast priced as well as the machine learning model.

The main caution: driver response to price was assumed, not measured. The pricing results are scenarios, not predictions.

## Key findings

1. Congestion can be forecast well. At 6 hours ahead the model makes 33.1% fewer errors than the best simple rule (47.5% at 1 hour).
2. Air pollution cannot, beyond simple rules. The best NO₂ result is 9.6% fewer errors (3 hours ahead), below the 10% bar. PM₂.₅ at 6 hours is 3.1% worse than the rule.
3. The congestion alarm works. At 6 hours ahead it catches 81% of high-congestion hours, and 98% of its alarms are correct.
4. Hourly timing is a weak lever. At a £15 average price, hourly pricing changes congestion by -0.44%.
5. The price level is a strong lever. A flat £18 charge changes congestion by -19.7%, NO₂ by -1.0% and PM₂.₅ by -2.5%.
6. Better forecasts did not mean better prices. A weekly-average forecast gave the same pricing gain as the model (0.0012), so the forecast is sufficient but not shown to be necessary.

## The question

The project had three research questions, with nine success criteria written before any modelling ([docs/02](02_research_questions_and_success_criteria.md)).

- RQ1, forecasting: can congestion, NO₂ and PM₂.₅ be forecast 1, 3 and 6 hours ahead accurately enough to support advance pricing? (S1 to S4)
- RQ2, pricing: under different assumptions about driver response, which hourly pricing strategies give the best trade-off between congestion, pollution and driver cost? (S5, S6)
- RQ3, robustness: how sensitive are those strategies to forecast errors and to uncertainty in driver response? (S7 to S9)

This is a simulation and decision-support study. It is not a proposal for Transport for London.

## Data

- Traffic: TomTom Traffic Index congestion level, hourly, for Westminster (standing in for the charging zone) and the City of London (its neighbour). The congestion level is the extra travel time compared with free flow, in percent.
- Air quality: London Air Quality Network roadside sites. WM6 (Oxford Street) is the target; CE2 and MY1 are model inputs.
- Weather: Open-Meteo historical weather for central London (temperature, humidity, rain, pressure, wind, cloud).
- Period: 1 January to 30 June 2025, 4,343 hours, all in UTC. Short gaps of up to 2 hours were filled by a straight line; longer gaps were left empty.

## Method

- Split: training months January to April. Settings were tuned on validation months (March and April) only. May and June were the test months, scored once, with nothing changed afterwards.
- Baselines: persistence (the value now) and weekly profile (the average for that weekday and hour). Every model had to beat the better of the two.
- Models: ridge, random forest and XGBoost, either predicting directly or correcting the simple rule. One model per target and horizon. Inputs use only past values.
- Pricing simulation: weekday prices published at 07:00 (for 07:00 to 12:00) and 13:00 (for 13:00 to 17:00), between £10 and £18, with an £18 daily cap. Driver response is a constant elasticity of -0.1, -0.3 or -0.5 around today's £15. Traffic turns into delay through the standard BPR road curve (alpha 0.15, exponent 4). Pollution changes only through the measured traffic share of each pollutant (NO₂ 0.19, PM₂.₅ 0.47, an upper bound).
- Optimisation: a standard solver (SLSQP) finds the best schedule at a fixed average price. NSGA-II maps the full trade-off between cost and harm, and cross-checks the solver.
- Comparison: each hourly schedule is compared with a flat charge at the same average price. The gain is the harm under the flat charge minus the harm under the hourly schedule, with a 95% range from resampling the 40 test days.

## Results: forecasting (RQ1)

Average error (MAE) of the model against the best simple rule, May and June 2025:

| Target | 1h ahead | 3h ahead | 6h ahead |
|---|---|---|---|
| Congestion | 4.12 vs 7.84 | 5.29 vs 9.40 | 6.28 vs 9.39 |
| NO₂ (µg/m³) | 4.48 vs 4.60 | 6.45 vs 7.13 | 9.05 vs 9.64 |
| PM₂.₅ (µg/m³) | 2.69 vs 2.83 | 3.42 vs 3.45 | 4.15 vs 4.03 |

| Criterion | Result | Verdict |
|---|---|---|
| S1 At least 10% fewer errors than the best simple rule | Congestion 47.5%, 43.7%, 33.1%. NO₂ 2.6%, 9.6%, 6.1%. PM₂.₅ 4.7%, 1.1%, -3.1% | Pass for congestion only (3 of 9) |
| S2 No month worse than 1.5 times the average error | Fails only for PM₂.₅ at 3h (1.50) and 6h (1.76), driven by March | 7 of 9 |
| S3 Congestion alarm at 6h: recall 0.80 or more, precision 0.85 or more | Recall 0.81, precision 0.98 | Pass (narrow) |
| S4 Average bias under 10% of the level | Fails for congestion 6h (10.7%), NO₂ 6h (28.6%), PM₂.₅ 3h (11.2%) and 6h (18.0%) | 5 of 9 |

What the errors show:

- May and June differ from the training months. NO₂ and PM₂.₅ levels fell and congestion rose as the season changed, so forecasts drifted. Congestion was under-predicted at peaks and in rain, more so in June.
- Retraining helps. For congestion 1 hour ahead in June, the error falls from 4.76 with the April model to 3.37 when retrained monthly.
- The congestion alarm separates high and normal hours well (ROC-AUC 0.989 at 6 hours, against 0.983 for the best rule). Recall of 0.81 at 6 hours suggests a lower alarm level would catch more jams, but the level was fixed before testing and was not changed.
- Temperature and pressure rank high among the inputs for congestion at 6 hours. This is likely a stand-in for season rather than a cause, so it should be read with caution.

## Results: pricing (RQ2)

At moderate driver response (elasticity -0.3), compared with today's flat £15:

| Plan | Average price | Congestion | NO₂ | PM₂.₅ | Revenue |
|---|---|---|---|---|---|
| Hourly, from our forecast | £15 | -0.44% | +0.02% | +0.06% | +0.05% |
| Hourly, weekly-average forecast | £15 | -0.46% | +0.02% | +0.05% | +0.05% |
| Hourly, perfect foresight | £15 | -0.49% | +0.02% | +0.02% | +0.05% |
| Hourly, persistence forecast | £15 | 0% | 0% | 0% | 0% |
| Flat £18 | £18 | -19.7% | -1.0% | -2.5% | +13.6% |

- S5, hourly beats flat at the same average price: pass, but small. The gain is 0.0012 (95% range 0.0010 to 0.0014), roughly what 5p on the average price would buy. The persistence forecast gives no gain because it is flat within each pricing block.
- S6, full trade-off reported: pass. Every plan is reported for congestion, NO₂, PM₂.₅, driver cost and revenue, at all three driver responses.
- NO₂ and PM₂.₅ rise very slightly under hourly pricing. Moving traffic between hours does not cut pollution, because pollution here responds only to the traffic share, not to delay.
- The trade-off set on a typical morning (4 June) is essentially a line from flat £10 to flat £18. Lowest cost (flat £10) raises congestion by 62.6%. The lowest congestion and lowest pollution are the same schedule (flat £18). Any "balanced" choice in between depends on how cost and harm are weighted, so none is recommended.
- The £18 daily cap removes the price signal for drivers who enter more than once: at a £10 floor, two entries already reach the cap, so they pay £18 under every plan.

## Results: robustness (RQ3)

| Criterion | Result | Verdict |
|---|---|---|
| S7 Advantage survives forecast error at twice the measured level | Positive at 1.5 times, gone at 2 times, at all three driver responses (break-even about 1.8 times) | Narrow fail |
| S8 Best schedule stable across driver response | Same shape at -0.1, -0.3 and -0.5: cheapest at 07:00, dearest at 11:00. Weaker response needs wider swings (£11 to £17 against £12 to £16) | Pass |
| S9 Forecast necessary, not just sufficient | Weekly-average forecast gives the same gain as the model | Sufficient, not shown necessary |

Two further checks: with a gentler road curve (exponent 2 instead of 4) the hourly gain shrinks to below 0.0003 at every driver response. Halving the assumed PM₂.₅ traffic share makes almost no difference.

## Monitoring

A model that worked in testing can go stale. Two checks were built:

- Drift: comparing May and June with the training months, temperature, NO₂, PM₂.₅ and congestion all shifted well past the usual warning level (PSI above 0.2).
- Weekly replay: replaying May and June week by week, the model never lost to the best simple rule two weeks running. But a weekly monitor would have flagged the 6-hour pollution forecasts for retraining from the first week, and congestion at 6 hours from early June, all because of bias.

## Policy implications

These results describe a framework, not a recommendation.

- Forecasting congestion a few hours ahead is feasible with open data, so publishing prices in advance is technically possible.
- In this simulation, most of the benefit comes from the overall price level, not from hourly variation. A more complex hourly scheme adds little unless drivers respond to timing much more than assumed here.
- TfL raised the standard charge from £15 to £18 on 2 January 2026. In this simulation, a rise of that size cuts congestion far more than hourly timing does. This is not a prediction of what happened in 2026, because driver response was assumed.
- If hourly pricing were pursued, a simple weekday-and-hour schedule would capture almost all of the timing benefit found here, without needing a live forecasting system.

## Limitations

- Six months of data, so seasons are not fully covered, and the test months differ from the training months.
- Congestion is measured for whole boroughs, not the exact charging zone.
- Driver response to price is assumed, in three scenarios, not measured.
- NO₂ and PM₂.₅ depend on weather and background pollution, not only on traffic. Pollution responds in the simulation only through the measured traffic share.
- Traffic pushed outside the zone, fairness (who pays) and CO₂ are not modelled.
- Whether LAQN hourly times mark the start or the end of the hour is not confirmed. Times were not shifted.
- The S5 yardstick was changed after the first optimiser runs, from a spread across five random seeds to a 95% range from resampling the test days, because the final solver has no random seed.

## Recommendations for further work

1. Measure real driver response from past price changes, including the 2026 rise to £18, using traffic counts before and after.
2. Request aggregated, anonymised entry and exit data, to study how often vehicles re-enter and how long they stay.
3. Extend to two or three years of data, so every season is covered in both training and testing.
4. Forecast further ahead (up to 24 hours) and add prediction intervals, so prices can reflect uncertainty.
5. Only then consider a learning agent (reinforcement learning) to set prices over time. Before driver response is measured, it would only learn the response we assumed.

## Reproducibility

The code, final models and result tables are in the repository. The full pipeline runs with one command (`python run_all.py`), and 32 automated tests cover data checks, leakage rules, pricing and model loading. Results reproduce exactly on the author's machine. On another operating system XGBoost scores move by about 0.1 MAE; no pass or fail result changes.

## Data and credits

- Traffic: [TomTom Traffic Index](https://www.tomtom.com/downloads/traffic-index/). © TomTom. Not redistributed.
- Air quality: [London Air Quality Network](https://www.londonair.org.uk), Environmental Research Group, Imperial College London.
- Weather: [Weather data by Open-Meteo.com](https://open-meteo.com/), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Historical weather is based on reanalysis data from the Copernicus Climate Change Service (C3S).
- Congestion Charge amounts: [Transport for London](https://tfl.gov.uk/modes/driving/congestion-charge).

This is an independent research project. It is not affiliated with TfL.

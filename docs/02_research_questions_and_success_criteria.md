# 02. Research Questions and Success Criteria

Written before any modelling. The rules below are fixed first, so the results cannot be used to choose the rules.

## Terms used

- **Hold-out period:** May and June 2025, kept unseen until the final score.
- **Persistence:** forecast equals the value now.
- **Profile:** forecast equals the average for that weekday and hour in the training months.
- **Skill score:** 1 minus (model error divided by baseline error). 0.10 means 10% fewer errors than the baseline.
- **Bias:** average of (forecast minus actual). Positive means over-forecasting.
- **Precision:** when the alarm is raised, how often it was right.
- **Recall:** of the real high-congestion hours, how many the alarm caught.
- **Elasticity:** how much traffic falls when price rises. Three assumed scenarios: -0.1 (low response), -0.3 (moderate), -0.5 (high).

## RQ1. Forecasting

Can machine learning forecast traffic congestion, NO₂ and PM₂.₅ in the CCZ area 1, 3 and 6 hours ahead accurately enough to support advance pricing decisions?

| Criterion | Pass rule | Why |
|---|---|---|
| S1. Beats the best simple baseline | Skill score of 0.10 or more against the better of persistence and profile, on the hold-out period | A model that cannot beat a free rule adds nothing |
| S2. Stable | No rolling month has an error above 1.5 times the hold-out error | One lucky month is not evidence |
| S3. Alarm quality | At 6 hours, recall of 0.80 or more and precision of 0.85 or more for congestion above 60% | A pricing rule needs to catch most jams without too many false alarms |
| S4. Low bias | Absolute average bias below 10% of the average level | Catches a forecast that sits consistently too high or too low, for example after a seasonal shift |

A target at a given horizon counts as accurate enough to support pricing only if it meets S1. Congestion must also meet S2 and S3. Pollutants must also have S4 reported.

## RQ2. Pricing

Under different assumptions about driver price responsiveness, what dynamic pricing strategies give the best trade-off between congestion, pollution and driver cost?

| Criterion | Pass rule | Why |
|---|---|---|
| S5. Beats flat | At the same average price paid, the best dynamic schedule gives lower simulated congestion than a flat charge, by more than the spread across five optimiser runs with different random seeds | Stops noise being counted as a win |
| S6. Full trade-off shown | Congestion, NO₂, PM₂.₅, driver cost and revenue are all reported for each strategy | A trade-off cannot be hidden behind one score |

## RQ3. Robustness

How sensitive are the recommended pricing strategies to forecast errors and to uncertainty in driver price responsiveness?

| Criterion | Pass rule | Why |
|---|---|---|
| S7. Survives forecast error | The dynamic advantage over flat remains when forecast error is raised to twice the model's measured error. We report the error level at which the advantage disappears | Real forecasts will be worse than a test |
| S8. Survives behaviour uncertainty | Repeat for elasticity -0.1, -0.3 and -0.5, and report whether the best strategy changes | Driver response is assumed, not measured |
| S9. Forecast value | The forecast is called necessary only if it beats the profile and persistence forecasts on the pricing outcome by more than the seed spread. Otherwise it is called sufficient but not shown to be necessary | Accurate and useful are different things |


## Threshold review, 10 October 2026

Reviewed on the training months (1 January to 30 April 2025 - 2,880 hours).
Share of hours at or above each level:

| Level | Westminster | City of London |
|---|---|---|
| 50 | 38.1% | 36.1% |
| 60 | 24.3% | 28.0% |
| 70 | 8.7% | 21.8% |

Decision: keep 60 as the definition of high congestion. It marks about a quarter of Westminster hours, so it is neither rare nor constant. 50 flags more than a third of hours, and 70 flags too few (8.7%) for a stable alarm score. S3 is still reported at 50, 60 and 70.## Threshold review, 10 October 2026

Reviewed on the training months only (1 January to 30 April 2025, 2,880 hours).
Share of hours at or above each level:

| Level | Westminster | City of London |
|---|---|---|
| 50 | 38.1% | 36.1% |
| 60 | 24.3% | 28.0% |
| 70 | 8.7% | 21.8% |

Decision: keep 60 as the definition of high congestion. It marks about a quarter of Westminster hours, so it is neither rare nor constant. 50 flags more than a third of hours, and 70 flags too few (8.7%) for a stable alarm score. S3 is still reported at 50, 60 and 70.
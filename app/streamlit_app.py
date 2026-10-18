"""
Dashboard: Dynamic congestion pricing for London, Central Zone.
Three pages: Overview, Forecasts, Pricing.
Reads only saved summary tables in reports/tables. No raw data.
Run: streamlit run app/streamlit_app.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import altair as alt
import pandas as pd
import streamlit as st

from ccz import config

st.set_page_config(page_title="London dynamic congestion pricing", layout="wide")

BLUE, RED = "#0019A8", "#DC241F"
NAMES = {"congestion": "Congestion", "no2": "NO₂", "pm25": "PM₂.₅"}
E = config.DEFAULT_ELASTICITY


@st.cache_data
def table(name):
    return pd.read_csv(config.TABLES_DIR / name)


def banner(title, subtitle):
    st.markdown(
        f"<div style='background:{BLUE};padding:18px 24px;border-radius:6px;margin-bottom:16px'>"
        f"<div style='color:white;font-size:28px;font-weight:700'>{title}</div>"
        f"<div style='color:#DDE3FF;font-size:15px'>{subtitle}</div></div>",
        unsafe_allow_html=True,
    )


def plan_row(prices, e, start):
    """First row for this driver response whose plan name starts with `start`."""
    rows = prices[(prices["elasticity"] == e) & prices["plan"].str.startswith(start)]
    return rows.iloc[0]


# ---------------- Page 1: Overview ----------------
def page_overview():
    banner("Dynamic congestion pricing for London: Central Zone",
           "Could an hourly charge, set from forecasts, beat today's flat daily fee?")
    st.markdown(
        "London's Congestion Charge is one flat daily fee, but traffic and air quality change hour by hour. "
        "We forecast congestion, NO₂ and PM₂.₅ 1, 3 and 6 hours ahead with machine learning "
        "(January to June 2025), scored the forecasts once on unseen months (May and June), "
        "then let an optimiser choose hourly prices in a simulation."
    )

    score = table("final_holdout_score.csv")
    prices = table("pricing_summary.csv")
    c6 = score[(score["target"] == "congestion") & (score["hours_ahead"] == 6)].iloc[0]
    ours = plan_row(prices, E, "dynamic (our")
    flat18 = plan_row(prices, E, "flat 18")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Congestion 6h ahead: fewer errors than rules", f"{c6['skill_pct']:.1f}%")
    c2.metric("Forecasts that clearly beat simple rules (S1)", f"{int(score['S1_pass'].sum())} of {len(score)}")
    c3.metric("Hourly pricing, same £15 average: congestion", f"{ours['congestion_pct']:.2f}%")
    c4.metric("Flat £18 instead of £15: congestion", f"{flat18['congestion_pct']:.1f}%")
    st.caption("Pricing figures assume a moderate driver response (elasticity -0.3).")

    st.subheader("The answer in four lines")
    st.markdown(
        "1. Congestion can be forecast well up to 6 hours ahead. Pollution forecasts barely beat simple rules.\n"
        "2. Changing the price hour by hour helps only a little. The overall price level matters far more.\n"
        "3. A simple weekly-average forecast prices as well as the model: the forecast is sufficient, not shown to be necessary.\n"
        "4. Driver response is assumed, not measured, so these are scenarios, not predictions."
    )
    st.info("Evidence on the Forecasts and Pricing pages. Limits are listed at the end of the Pricing page.")


# ---------------- Page 2: Forecasts ----------------
def page_forecasts():
    banner("Can we forecast congestion and air quality?",
           "Forecasts scored once on unseen months (May and June 2025).")
    score = table("final_holdout_score.csv")
    cong = score[score["target"] == "congestion"]
    for col, (_, r) in zip(st.columns(len(cong)), cong.iterrows()):
        col.metric(f"Congestion {r['hours_ahead']}h ahead: fewer errors than simple rule",
                   f"{r['skill_pct']:.1f}%",
                   help=f"Average error {r['model_mae']} vs best simple rule {r['baseline_mae']}")

    st.subheader("Scorecard: model against the best simple rule")
    metrics = table("holdout_metrics.csv")
    s4 = metrics[metrics["forecaster"] == "model"][["target", "hours_ahead", "S4_pass"]]
    card = score.merge(s4, on=["target", "hours_ahead"])
    card["target"] = card["target"].map(NAMES)
    card = card[["target", "hours_ahead", "model_mae", "baseline_mae", "skill_pct",
                 "S1_pass", "S2_pass", "S4_pass"]].rename(columns={
        "target": "Forecast", "hours_ahead": "Hours ahead", "model_mae": "Model error",
        "baseline_mae": "Simple rule error", "skill_pct": "Skill %",
        "S1_pass": "S1 beats rule", "S2_pass": "S2 stable", "S4_pass": "S4 low bias"})
    st.dataframe(card, hide_index=True)
    st.caption("Error = average size of the miss (MAE). S1: at least 10% fewer errors than the best simple rule. "
               "S2: no month worse than 1.5 times the average error. S4: average bias under 10% of the level.")

    st.subheader("Weekly check through May and June")
    weekly = table("monitoring_weekly.csv")
    c1, c2 = st.columns(2)
    t = c1.selectbox("Forecast", list(NAMES), format_func=NAMES.get)
    h = c2.selectbox("Hours ahead", config.HORIZONS)
    part = weekly[(weekly["target"] == t) & (weekly["hours_ahead"] == h)].set_index("week_start")
    st.line_chart(part[["model_mae", "baseline_mae"]].rename(
        columns={"model_mae": "Model", "baseline_mae": "Best simple rule"}), color=[RED, BLUE])
    st.markdown(f"Retraining flag raised in **{int(part['retrain_flag'].sum())} of {len(part)} weeks** "
                f"(model no better than the rule {config.RETRAIN_WEEKS} weeks running, "
                f"or weekly bias above {config.BIAS_LIMIT_PCT}% of the level).")


# ---------------- Page 3: Pricing ----------------
def page_pricing():
    banner("Would an hourly charge do better than a flat one?",
           "Simulation with assumed driver response. Prices published at 07:00 and 13:00 on weekdays.")
    prices = table("pricing_summary.csv")
    labels = {-0.1: "Low (-0.1)", -0.3: "Moderate (-0.3)", -0.5: "High (-0.5)"}
    e = st.radio("How strongly drivers respond to price (assumed, not measured)", config.ELASTICITIES,
                 index=config.ELASTICITIES.index(E),
                 format_func=lambda x: labels.get(x, str(x)), horizontal=True)
    part = prices[prices["elasticity"] == e]
    ours = plan_row(prices, e, "dynamic (our")
    flat18 = plan_row(prices, e, "flat 18")

    st.markdown(
        f"**What to notice:** at the same £15 average price, hourly pricing changes congestion by only "
        f"**{ours['congestion_pct']:.2f}%**. Raising the flat charge to £18 changes it by "
        f"**{flat18['congestion_pct']:.1f}%**. The price level is the strong lever; hourly timing is weak."
    )
    chart = alt.Chart(part).mark_bar().encode(
        x=alt.X("congestion_pct:Q", title="Change in congestion compared with flat £15 (%)"),
        y=alt.Y("plan:N", sort="x", title=None, axis=alt.Axis(labelLimit=300)),
        color=alt.condition("indexof(datum.plan, 'flat') == 0", alt.value(RED), alt.value(BLUE)),
        tooltip=["plan", "driver_cost", "congestion_pct"],
    )
    st.altair_chart(chart)
    st.caption("Blue: hourly (dynamic) plans at a £15 average. Red: flat daily charges.")

    show = part[["plan", "driver_cost", "congestion_pct", "no2_pct", "pm25_pct", "revenue_pct"]].rename(columns={
        "plan": "Plan", "driver_cost": "Average price paid (£)", "congestion_pct": "Congestion %",
        "no2_pct": "NO₂ %", "pm25_pct": "PM₂.₅ %", "revenue_pct": "Revenue %"}).round(2)
    st.dataframe(show, hide_index=True)

    st.subheader("Limits")
    st.markdown(
        "- Six months of data (January to June 2025), so seasons are not fully covered.\n"
        "- Congestion is measured for whole boroughs (Westminster), not the exact zone.\n"
        "- Driver response to price is assumed, in three scenarios.\n"
        "- NO₂ and PM₂.₅ depend on weather and background pollution, not only traffic.\n"
        "- Traffic pushed outside the zone, and who pays, are not modelled.\n"
        "- Simulation only. Not a proposal for implementation."
    )


# ---------------- Navigation ----------------
PAGES = {"Overview": page_overview, "Forecasts": page_forecasts, "Pricing": page_pricing}
choice = st.sidebar.radio("Page", list(PAGES))
st.sidebar.caption("Traffic data: TomTom Traffic Index. Air quality: London Air Quality Network. "
                   "Weather: Open-Meteo.")
st.sidebar.caption("[lamide-akanni](https://github.com/lamide-akanni)  \n"
                   "Independent research project. Not affiliated with TfL.")
PAGES[choice]()
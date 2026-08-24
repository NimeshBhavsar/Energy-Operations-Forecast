import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Operational Energy Forecasts", layout="wide")

@st.cache_data
def load_data():
    base = pd.read_csv("forecast_baseline.csv", parse_dates=["datetime"])
    scen = pd.read_csv("forecast_scenario_shock.csv", parse_dates=["datetime"])
    delta = pd.read_csv("forecast_scenario_delta.csv", parse_dates=["datetime"])
    # stand. column names (in case)
    for df in (base, scen, delta):
        if "region" in df.columns:
            df["region"] = df["region"].astype(str)
    return base, scen, delta

base, scen, delta = load_data()

# --- Sidebar controls
st.sidebar.header("Filters")
regions = sorted(base["region"].unique().tolist())
region = st.sidebar.selectbox("Region", regions, index=0)

min_dt = base["datetime"].min()
max_dt = base["datetime"].max()
dt_range = st.sidebar.date_input("Date range (baseline domain)", [min_dt.date(), max_dt.date()])
if not isinstance(dt_range, (list, tuple)):
    dt_range = [dt_range, dt_range]

start_dt = pd.Timestamp(dt_range[0])
end_dt = pd.Timestamp(dt_range[-1]) + pd.Timedelta(days=1)

tzinfo = getattr(base["datetime"].dt, "tz", None)
if tzinfo is not None:
    if start_dt.tzinfo is None:
        start_dt = start_dt.tz_localize(tzinfo)
    else:
        start_dt = start_dt.tz_convert(tzinfo)
    if end_dt.tzinfo is None:
        end_dt = end_dt.tz_localize(tzinfo)
    else:
        end_dt = end_dt.tz_convert(tzinfo)

show_downloads = st.sidebar.checkbox("Show download buttons", value=True)

# --- Prepare filtered frames
b_reg = base[(base["region"]==region) & (base["datetime"]>=start_dt) & (base["datetime"]<end_dt)].copy()
s_reg = scen[(scen["region"]==region) & (scen["datetime"]>=start_dt) & (scen["datetime"]<end_dt)].copy()
d_reg = delta[(delta["region"]==region) & (delta["datetime"]>=start_dt) & (delta["datetime"]<end_dt)].copy()

# --- Top KPIs
def kpi(val, fmt="{:,.2f}", label=""):
    st.metric(label, fmt.format(val) if pd.notna(val) else "—")

col1, col2, col3, col4 = st.columns(4)
with col1:
    kpi(b_reg["forecast_price"].mean(), "${:,.2f}/MWh", "Avg Price (Baseline)")
with col2:
    kpi(b_reg["forecast_demand"].mean(), "{:,.0f} MW", "Avg Demand (Baseline)")
with col3:
    kpi(d_reg["delta_price"].mean(), "${:,.2f}/MWh", "Avg Δ Price (Scenario-Baseline)")
with col4:
    kpi(d_reg["delta_demand"].mean(), "{:,.0f} MW", "Avg Δ Demand (Scenario-Baseline)")

st.markdown(f"### Region: **{region}**  |  Period: {start_dt.date()} → { (end_dt - pd.Timedelta(days=1)).date() }")

# --- Charts
tab1, tab2, tab3 = st.tabs(["Price & Demand (level)", "Scenario deltas (Δ)", "Tables / Export"])

with tab1:
    st.subheader("Baseline vs Scenario — Price")
    price_lvl = pd.DataFrame({
        "datetime": b_reg["datetime"],
        "Baseline Price": b_reg["forecast_price"],
        "Scenario Price": s_reg["forecast_price"]
    }).set_index("datetime")
    st.line_chart(price_lvl)

    st.subheader("Baseline vs Scenario — Demand")
    dem_lvl = pd.DataFrame({
        "datetime": b_reg["datetime"],
        "Baseline Demand": b_reg["forecast_demand"],
        "Scenario Demand": s_reg["forecast_demand"]
    }).set_index("datetime")
    st.line_chart(dem_lvl)

with tab2:
    st.subheader("Scenario Deltas (Scenario − Baseline)")
    st.area_chart(d_reg.set_index("datetime")[["delta_price"]].rename(columns={"delta_price":"Δ Price ($/MWh)"}))
    st.area_chart(d_reg.set_index("datetime")[["delta_demand"]].rename(columns={"delta_demand":"Δ Demand (MW)"}))

    # Simple $ impact estimator (optional)
    st.markdown("**Quick $ Impact Estimator**")
    assumed_load_mw = st.number_input("Assumed affected load (MW)", value=100.0, min_value=0.0, step=10.0)
    # $ impact ≈ sum(ΔPrice * load * 0.5h)
    hours_factor = 0.5  # 30-min intervals
    est_cost = (d_reg["delta_price"].fillna(0) * assumed_load_mw * hours_factor).sum()
    st.info(f"Estimated weekly scenario cost impact (for {assumed_load_mw:.0f} MW): **${est_cost:,.0f}**")

with tab3:
    st.subheader("Baseline (head)")
    st.dataframe(b_reg.head(100))
    st.subheader("Scenario (head)")
    st.dataframe(s_reg.head(100))
    st.subheader("Deltas (head)")
    st.dataframe(d_reg.head(100))

    if show_downloads:
        c1, c2, c3 = st.columns(3)
        c1.download_button("Download Baseline CSV", b_reg.to_csv(index=False), file_name=f"baseline_{region}.csv")
        c2.download_button("Download Scenario CSV", s_reg.to_csv(index=False), file_name=f"scenario_{region}.csv")
        c3.download_button("Download Deltas CSV", d_reg.to_csv(index=False), file_name=f"deltas_{region}.csv")

st.caption("Tip: This app reads the CSVs your pipeline exports. Schedule the pipeline (cron/Airflow) → refresh this page to see updated forecasts.")

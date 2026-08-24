import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import warnings
import os
import sys
import smtplib
from email.message import EmailMessage
from pathlib import Path
warnings.filterwarnings('ignore')

# Import authentication
import auth

# Add parent directory to path to import the forecast function
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))
from pipeline.operational import automated_operational_forecast

# Page configuration
st.set_page_config(
    page_title="Energy Ops Forecast | Executive Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional enterprise styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        --ink:        #0f172a;
        --ink-muted:  #64748b;
        --line:       #e2e8f0;
        --surface:    #ffffff;
        --accent:     #2563eb;
        --accent-dark:#1d4ed8;
        --pos:        #059669;
        --neg:        #dc2626;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    .stApp {
        background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
        background-attachment: fixed;
    }

    .main > div { padding-top: 1.5rem; }

    /* ---- Typography ------------------------------------------------ */
    h1 {
        color: var(--ink) !important;
        font-weight: 800 !important;
        font-size: 2.35rem !important;
        letter-spacing: -0.02em;
        margin-bottom: 0.25rem;
    }

    h2 {
        color: #334155;
        font-weight: 700;
        font-size: 1.5rem;
        letter-spacing: -0.01em;
        margin: 1.5rem 0 0.75rem 0;
    }

    h3 {
        color: #334155;
        font-weight: 650;
        font-size: 1.15rem;
        letter-spacing: -0.01em;
        margin: 1.75rem 0 0.75rem 0;
    }

    p.page-subtitle {
        color: var(--ink-muted) !important;
        font-size: 1.02rem !important;
        font-weight: 450;
        margin: 0 0 1.75rem 0;
    }

    /* ---- Cards ------------------------------------------------------ */
    .kpi-container {
        background: var(--surface);
        padding: 1.25rem 1.35rem;
        border-radius: 14px;
        border: 1px solid var(--line);
        border-left: 4px solid var(--accent);
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04), 0 4px 16px rgba(15, 23, 42, 0.05);
        height: 100%;
        transition: transform 0.18s ease, box-shadow 0.18s ease;
    }

    .kpi-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 2px 4px rgba(15, 23, 42, 0.05), 0 10px 28px rgba(15, 23, 42, 0.09);
    }

    .kpi-container p.metric-label {
        font-size: 0.72rem !important;
        color: var(--ink-muted) !important;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin: 0 0 0.45rem 0;
    }

    .kpi-container p.metric-value {
        font-size: 1.9rem !important;
        font-weight: 700;
        color: var(--ink) !important;
        letter-spacing: -0.02em;
        line-height: 1.15;
        margin: 0;
        font-variant-numeric: tabular-nums;
    }

    .kpi-container .metric-delta {
        display: inline-block;
        margin: 0.55rem 0 0 0;
        padding: 0.12rem 0.5rem;
        border-radius: 999px;
        font-size: 0.75rem !important;
        font-weight: 600;
        font-variant-numeric: tabular-nums;
    }

    .metric-delta.up   { color: var(--pos); background: rgba(5, 150, 105, 0.10); }
    .metric-delta.down { color: var(--neg); background: rgba(220, 38, 38, 0.10); }
    .metric-delta.flat { color: var(--ink-muted); background: rgba(100, 116, 139, 0.10); }

    .risk-card {
        background: var(--surface);
        padding: 1.15rem 1.3rem;
        border-radius: 14px;
        border: 1px solid var(--line);
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04), 0 4px 16px rgba(15, 23, 42, 0.05);
        height: 100%;
    }

    .risk-card p.risk-title {
        font-size: 0.72rem !important;
        color: var(--ink-muted) !important;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin: 0 0 0.5rem 0;
    }

    .risk-card p.risk-level {
        font-size: 1.35rem !important;
        font-weight: 700;
        letter-spacing: -0.01em;
        margin: 0 0 0.75rem 0;
    }

    .risk-card .risk-row {
        display: flex;
        justify-content: space-between;
        font-size: 0.87rem !important;
        color: #475569;
        padding: 0.28rem 0;
        border-top: 1px solid #f1f5f9;
        font-variant-numeric: tabular-nums;
    }

    .risk-card .risk-row span:last-child { font-weight: 600; color: var(--ink); }

    /* ---- Controls --------------------------------------------------- */
    .stAlert { border-radius: 12px; border: none; }

    div[data-testid="stMetric"] {
        background: var(--surface);
        border: 1px solid var(--line);
        padding: 1rem 1.15rem;
        border-radius: 12px;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 6px;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        color: var(--ink-muted);
        font-weight: 550;
        border: none;
        padding: 10px 20px;
        transition: background 0.2s ease, color 0.2s ease;
    }

    .stTabs [aria-selected="true"] {
        background: var(--accent);
        color: white !important;
    }

    .stButton > button {
        background: var(--accent);
        color: white;
        border: none;
        border-radius: 9px;
        font-weight: 600;
        padding: 0.6rem 1.5rem;
        box-shadow: 0 1px 2px rgba(37, 99, 235, 0.25);
        transition: background 0.18s ease, transform 0.18s ease, box-shadow 0.18s ease;
    }

    .stButton > button:hover {
        background: var(--accent-dark);
        transform: translateY(-1px);
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.3);
    }

    .stButton > button:active { transform: translateY(0); }

    section[data-testid="stSidebar"] {
        background: var(--surface);
        border-right: 1px solid var(--line);
    }

    p.dashboard-footer {
        color: #94a3b8 !important;
        font-size: 0.83rem !important;
        text-align: center;
        padding: 0.5rem 0 1.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def get_secret(key, default=None):
    """Get secret from Streamlit secrets first, then environment fallback."""
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, default)

def get_smtp_config():
    """Get SMTP configuration from Streamlit secrets or environment variables."""
    smtp_host = get_secret("SMTP_HOST")
    smtp_port = int(get_secret("SMTP_PORT", "587"))
    smtp_user = get_secret("SMTP_USER")
    smtp_pass = get_secret("SMTP_PASS")
    smtp_use_tls = str(get_secret("SMTP_USE_TLS", "true")).lower() == "true"

    return smtp_host, smtp_port, smtp_user, smtp_pass, smtp_use_tls

def send_forecast_email(csv_files, recipient_email="nimeshbhavsar006@gmail.com"):
    """Send forecast CSV files via email using SMTP."""
    try:
        # Get SMTP configuration
        smtp_host, smtp_port, smtp_user, smtp_pass, smtp_use_tls = get_smtp_config()

        if not all([smtp_host, smtp_user, smtp_pass]):
            return False, "SMTP configuration missing. Please set SMTP_HOST, SMTP_USER, and SMTP_PASS in Streamlit secrets or environment variables."

        # Create email message
        msg = EmailMessage()
        msg['Subject'] = f'Energy Ops Forecast - {datetime.now().strftime("%Y-%m-%d %H:%M")}'
        msg['From'] = smtp_user
        msg['To'] = recipient_email

        # Email body
        body = f"""
Energy Operations Forecast Report
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

This email contains the latest energy forecast outputs:

📊 Attachments:
• forecast_baseline.csv - Base case operational forecast
• forecast_scenario_shock.csv - Extreme scenario forecast
• forecast_scenario_delta.csv - Impact analysis (shock - baseline)

Files are ready for Power BI consumption and further analysis.

---
Generated by Energy Ops Forecast Dashboard
"""
        msg.set_content(body)

        # Attach CSV files (abort rather than send an email with no attachments)
        missing = [f for f in csv_files if not os.path.exists(f)]
        if missing:
            return False, "Forecast files not found: " + ", ".join(missing)

        for file_path in csv_files:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            file_name = os.path.basename(file_path)
            msg.add_attachment(file_data, maintype='text', subtype='csv', filename=file_name)

        # Send email using proper SMTP sequence
        server = smtplib.SMTP(smtp_host, smtp_port)
        try:
            server.ehlo()
            if smtp_use_tls:
                server.starttls()
                server.ehlo()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            return True, f"Email sent successfully to {recipient_email}"
        finally:
            server.quit()

    except smtplib.SMTPException as e:
        return False, f"SMTP error: {str(e)}"
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"

def run_forecast_and_preview():
    """Run forecast and show preview of results."""
    try:
        # Run the forecast (paths resolved relative to project root, not cwd)
        project_root = os.path.dirname(os.path.dirname(__file__))
        success, message = automated_operational_forecast(
            input_file=os.path.join(project_root, 'fact_energy_market.parquet'),
            output_dir=os.path.join(project_root, 'data')
        )

        if not success:
            return False, message, None

        # Load the generated data for preview
        data_dir = os.path.join(project_root, "data")
        base = pd.read_csv(os.path.join(data_dir, "forecast_baseline.csv"), parse_dates=["datetime"])
        shock = pd.read_csv(os.path.join(data_dir, "forecast_scenario_shock.csv"), parse_dates=["datetime"])
        delta = pd.read_csv(os.path.join(data_dir, "forecast_scenario_delta.csv"), parse_dates=["datetime"])

        # Create preview summary with raw numeric values
        preview_data = {
            'Baseline': {
                'Records': len(base),
                'Avg Price ($/MWh)': round(base['forecast_price'].mean(), 2),
                'Avg Demand (MW)': int(base['forecast_demand'].mean()),
                'Date Range': f"{base['datetime'].min().date()} to {base['datetime'].max().date()}"
            },
            'Shock Scenario': {
                'Records': len(shock),
                'Avg Price ($/MWh)': round(shock['forecast_price'].mean(), 2),
                'Avg Demand (MW)': int(shock['forecast_demand'].mean()),
                'Price Impact (%)': round(((shock['forecast_price'].mean() / base['forecast_price'].mean() - 1) * 100), 1)
            },
            'Delta Analysis': {
                'Records': len(delta),
                'Max Price Delta ($/MWh)': round(delta['delta_price'].max(), 2),
                'Min Price Delta ($/MWh)': round(delta['delta_price'].min(), 2),
                'Avg Price Delta ($/MWh)': round(delta['delta_price'].mean(), 2)
            }
        }

        return True, "Forecast generated successfully", preview_data

    except Exception as e:
        return False, f"Forecast failed: {str(e)}", None

@st.cache_data
def load_forecast_data():
    """Load all forecast data with error handling."""
    try:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        base = pd.read_csv(os.path.join(data_dir, "forecast_baseline.csv"), parse_dates=["datetime"])
        shock = pd.read_csv(os.path.join(data_dir, "forecast_scenario_shock.csv"), parse_dates=["datetime"])
        delta = pd.read_csv(os.path.join(data_dir, "forecast_scenario_delta.csv"), parse_dates=["datetime"])

        # Standardize column names
        for df in [base, shock, delta]:
            if "region" in df.columns:
                df["region"] = df["region"].astype(str)

        return base, shock, delta
    except FileNotFoundError:
        st.error("⚠️ Forecast data not found. Please run the automation pipeline first.")
        st.info("Run: `python run_forecast.py` to generate the required CSV files.")
        return None, None, None

def create_kpi_card(value, label, format_str="{:,.2f}", icon="📊", delta=None):
    """Create a beautiful KPI card."""
    formatted_value = format_str.format(value) if pd.notna(value) else "—"

    delta_html = ""
    if delta is not None and pd.notna(delta):
        trend = "up" if delta > 0 else "down" if delta < 0 else "flat"
        delta_symbol = "↗" if delta > 0 else "↘" if delta < 0 else "→"
        delta_html = (
            f'<span class="metric-delta {trend}">{delta_symbol} {delta:+.1f}% vs shock</span>'
        )

    # Rendered as a single line: a blank line inside the block would close the
    # HTML element early and leak the closing tags onto the page as text.
    st.markdown(
        f'<div class="kpi-container">'
        f'<p class="metric-label">{icon} {label}</p>'
        f'<p class="metric-value">{formatted_value}</p>'
        f'{delta_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def create_risk_card(title, level, rows):
    """Create a risk summary card matching the KPI card styling."""
    row_html = "".join(
        f'<div class="risk-row"><span>{k}</span><span>{v}</span></div>' for k, v in rows
    )
    st.markdown(
        f'<div class="risk-card">'
        f'<p class="risk-title">{title}</p>'
        f'<p class="risk-level">{level}</p>'
        f'{row_html}'
        f'</div>',
        unsafe_allow_html=True,
    )

def create_executive_summary_chart(base_df, shock_df):
    """Create executive summary visualization."""
    # Aggregate data by day for overview
    base_daily = base_df.groupby(base_df['datetime'].dt.date).agg({
        'forecast_price': 'mean',
        'forecast_demand': 'mean'
    }).reset_index()

    shock_daily = shock_df.groupby(shock_df['datetime'].dt.date).agg({
        'forecast_price': 'mean',
        'forecast_demand': 'mean'
    }).reset_index()

    # Create subplot
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Average Daily Price Forecast', 'Average Daily Demand Forecast'),
        vertical_spacing=0.15,
        specs=[[{"secondary_y": False}], [{"secondary_y": False}]]
    )

    # Price chart
    fig.add_trace(
        go.Scatter(
            x=base_daily['datetime'],
            y=base_daily['forecast_price'],
            name='Baseline Price',
            line=dict(color='#2563eb', width=2.5),
            fill='tozeroy',
            fillcolor='rgba(37, 99, 235, 0.08)',
            hovertemplate='Baseline · $%{y:,.2f}/MWh<extra></extra>'
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=shock_daily['datetime'],
            y=shock_daily['forecast_price'],
            name='Shock Scenario Price',
            line=dict(color='#dc2626', width=2.5, dash='dash'),
            hovertemplate='Shock · $%{y:,.2f}/MWh<extra></extra>'
        ),
        row=1, col=1
    )

    # Demand chart
    fig.add_trace(
        go.Scatter(
            x=base_daily['datetime'],
            y=base_daily['forecast_demand'],
            name='Baseline Demand',
            line=dict(color='#059669', width=2.5),
            fill='tozeroy',
            fillcolor='rgba(5, 150, 105, 0.08)',
            hovertemplate='Baseline · %{y:,.0f} MW<extra></extra>'
        ),
        row=2, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=shock_daily['datetime'],
            y=shock_daily['forecast_demand'],
            name='Shock Scenario Demand',
            line=dict(color='#d97706', width=2.5, dash='dash'),
            hovertemplate='Shock · %{y:,.0f} MW<extra></extra>'
        ),
        row=2, col=1
    )

    fig.update_layout(
        height=620,
        showlegend=True,
        template="plotly_white",
        font=dict(family="Inter, sans-serif", size=13, color="#475569"),
        hovermode="x unified",
        margin=dict(l=70, r=30, t=70, b=50),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.04,
            xanchor="right",
            x=1,
            bgcolor='rgba(0,0,0,0)'
        )
    )

    fig.update_annotations(font=dict(size=14, color="#334155"))

    fig.update_xaxes(showgrid=False, linecolor="#e2e8f0", ticks="outside",
                     tickcolor="#e2e8f0")
    fig.update_yaxes(gridcolor="#eef2f7", zeroline=False, linecolor="#e2e8f0")

    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_yaxes(title_text="Price ($/MWh)", row=1, col=1)
    fig.update_yaxes(title_text="Demand (MW)", row=2, col=1)

    return fig

# Main dashboard
def main():
    # Require authentication
    if not auth.require_login():
        st.stop()

    # Header
    st.markdown(
        '<h1>⚡ Energy Operations Forecast</h1>'
        '<p class="page-subtitle">Executive dashboard · real-time market intelligence</p>',
        unsafe_allow_html=True,
    )

    # Run Forecast + Send Outputs via Email Section
    st.markdown("### 🚀 Run Forecast + Send Outputs via Email")

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown("""
        **Generate fresh forecasts and email results automatically:**
        - Runs automated_operational_forecast with 7-day horizon
        - Generates 3 CSV files (baseline, shock, delta)
        - Sends files as email attachments to nimeshbhavsar006@gmail.com
        - Shows preview of results in dashboard
        """)

    with col2:
        # SMTP Configuration Status
        smtp_host, smtp_port, smtp_user, smtp_pass, smtp_use_tls = get_smtp_config()
        smtp_configured = all([smtp_host, smtp_user, smtp_pass])

        if smtp_configured:
            st.success("📧 SMTP Configured")
            st.caption(f"Host: {smtp_host}")
        else:
            st.warning("⚠️ SMTP Not Configured")
            st.caption("Set SMTP settings in Streamlit secrets")

    with col3:
        # Run Forecast Button
        if st.button("🎯 Run Forecast & Email", type="primary", use_container_width=True):
            with st.spinner("🔄 Running forecast..."):
                # Run forecast
                forecast_success, forecast_message, preview_data = run_forecast_and_preview()

                if forecast_success:
                    st.success(f"✅ {forecast_message}")

                    # Show preview
                    if preview_data:
                        st.markdown("#### 📊 Forecast Preview")
                        st.dataframe(preview_data, use_container_width=True)

                    # Send email if SMTP is configured
                    if smtp_configured:
                        with st.spinner("📧 Sending email..."):
                            csv_files = [
                                str(PROJECT_ROOT / "data" / "forecast_baseline.csv"),
                                str(PROJECT_ROOT / "data" / "forecast_scenario_shock.csv"),
                                str(PROJECT_ROOT / "data" / "forecast_scenario_delta.csv")
                            ]
                            email_success, email_message = send_forecast_email(csv_files)

                            if email_success:
                                st.success(f"📧 {email_message}")
                            else:
                                st.error(f"❌ {email_message}")
                    else:
                        st.warning("📧 Email not sent - SMTP configuration missing")

                    # Clear cached data to reload new forecast
                    load_forecast_data.clear()

                else:
                    st.error(f"❌ {forecast_message}")

    st.markdown("---")

    # Load data
    base_df, shock_df, delta_df = load_forecast_data()

    if base_df is None:
        return

    # Sidebar filters
    st.sidebar.markdown("## 🎛️ Controls")

    # Region selector
    regions = sorted(base_df["region"].unique())
    selected_region = st.sidebar.selectbox("🌍 Region", regions, index=0)

    # Date range
    min_date = base_df["datetime"].min().date()
    max_date = base_df["datetime"].max().date()

    date_range = st.sidebar.date_input(
        "📅 Forecast Period",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range

    # Filter data
    mask = (
        (base_df["region"] == selected_region) &
        (base_df["datetime"].dt.date >= start_date) &
        (base_df["datetime"].dt.date <= end_date)
    )

    base_filtered = base_df[mask].copy()
    shock_filtered = shock_df[mask].copy()
    delta_filtered = delta_df[
        (delta_df["region"] == selected_region) &
        (delta_df["datetime"].dt.date >= start_date) &
        (delta_df["datetime"].dt.date <= end_date)
    ].copy()

    # Key Metrics Row
    st.markdown("### 📊 Key Performance Indicators")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        avg_base_price = base_filtered["forecast_price"].mean()
        price_change = ((shock_filtered["forecast_price"].mean() / avg_base_price - 1) * 100) if avg_base_price > 0 else 0
        create_kpi_card(
            avg_base_price,
            "Average Price (Baseline)",
            "${:,.2f}/MWh",
            "💰",
            price_change
        )

    with col2:
        avg_base_demand = base_filtered["forecast_demand"].mean()
        demand_change = ((shock_filtered["forecast_demand"].mean() / avg_base_demand - 1) * 100) if avg_base_demand > 0 else 0
        create_kpi_card(
            avg_base_demand,
            "Average Demand (Baseline)",
            "{:,.0f} MW",
            "⚡",
            demand_change
        )

    with col3:
        avg_price_delta = delta_filtered["delta_price"].mean()
        create_kpi_card(
            avg_price_delta,
            "Price Impact (Shock)",
            "${:+,.2f}/MWh",
            "📈"
        )

    with col4:
        avg_demand_delta = delta_filtered["delta_demand"].mean()
        create_kpi_card(
            avg_demand_delta,
            "Demand Impact (Shock)",
            "{:+,.0f} MW",
            "📊"
        )

    # Risk Assessment
    st.markdown("### ⚠️ Risk Assessment")

    col1, col2 = st.columns(2)

    with col1:
        # Price volatility
        price_volatility = base_filtered["forecast_price"].std()
        max_price_spike = delta_filtered["delta_price"].max()

        if max_price_spike > 50:
            risk_level = "🔴 HIGH"
            risk_color = "error"
        elif max_price_spike > 20:
            risk_level = "🟡 MEDIUM"
            risk_color = "warning"
        else:
            risk_level = "🟢 LOW"
            risk_color = "success"

        create_risk_card(
            "Price Risk Level",
            risk_level,
            [
                ("Volatility", f"${price_volatility:,.2f}/MWh"),
                ("Max spike", f"${max_price_spike:+,.2f}/MWh"),
            ],
        )

    with col2:
        # Demand stress
        demand_stress = (shock_filtered["forecast_demand"].max() / base_filtered["forecast_demand"].mean() - 1) * 100

        if demand_stress > 20:
            stress_level = "🔴 HIGH"
        elif demand_stress > 10:
            stress_level = "🟡 MEDIUM"
        else:
            stress_level = "🟢 LOW"

        create_risk_card(
            "Demand Stress",
            stress_level,
            [
                ("Peak vs average", f"{demand_stress:+.1f}%"),
                ("Max demand", f"{shock_filtered['forecast_demand'].max():,.0f} MW"),
            ],
        )

    # Executive Summary Chart
    st.markdown("### 📊 Executive Summary")
    fig = create_executive_summary_chart(base_filtered, shock_filtered)

    # Display with high-quality settings for professional screenshots
    st.plotly_chart(fig, use_container_width=True, config={
        'displayModeBar': True,
        'displaylogo': False,
        'modeBarButtonsToRemove': ['pan2d', 'lasso2d'],
        'toImageButtonOptions': {
            'format': 'png',
            'filename': 'energy_forecast_executive_summary',
            'height': 800,
            'width': 1400,
            'scale': 3  # High DPI for crisp screenshots
        }
    })

    # Financial Impact Calculator
    st.markdown("### 💰 Financial Impact Calculator")

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        portfolio_size = st.number_input(
            "Portfolio Size (MW)",
            min_value=0.0,
            value=100.0,
            step=10.0,
            help="Enter your total exposure in MW"
        )

    with col2:
        risk_factor = st.selectbox(
            "Risk Multiplier",
            options=[0.5, 1.0, 1.5, 2.0],
            index=1,
            format_func=lambda x: f"{x}x ({'Conservative' if x < 1 else 'Baseline' if x == 1 else 'Aggressive'})"
        )

    with col3:
        # Calculate financial impact
        hours_in_period = len(delta_filtered) * 0.5  # 30-min intervals
        price_impact = delta_filtered["delta_price"].sum() * portfolio_size * 0.5 * risk_factor

        if price_impact > 0:
            impact_color = "🔴"
            impact_text = "Additional Cost"
        else:
            impact_color = "🟢"
            impact_text = "Potential Savings"

        st.markdown(f"""
        **{impact_color} Estimated {impact_text}**

        **${abs(price_impact):,.0f}** over {hours_in_period:.0f} hours

        *Based on {portfolio_size:.0f} MW portfolio with {risk_factor}x risk factor*
        """)

    # Quick Actions
    st.markdown("### 🎯 Quick Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 View Regional Analysis", use_container_width=True):
            st.switch_page("pages/2_Regional_Analysis.py")

    with col2:
        if st.button("💥 Price Spike Analysis", use_container_width=True):
            st.switch_page("pages/3_Price_and_Spikes.py")

    with col3:
        if st.button("🌤️ Weather Impact", use_container_width=True):
            st.switch_page("pages/4_Weather_Impact.py")

    # Data freshness info
    st.markdown("---")
    last_update = base_df["datetime"].max()
    st.info(f"📅 Data freshness: Forecast generated for period starting {last_update.strftime('%Y-%m-%d %H:%M')} UTC")

    # Footer
    st.markdown(
        '<p class="dashboard-footer">Energy Operations Forecast Dashboard · '
        'powered by advanced analytics</p>',
        unsafe_allow_html=True,
    )

if __name__ == "__main__":
    main()
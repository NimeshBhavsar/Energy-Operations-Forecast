import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Price & Spikes Analysis | Energy Ops Forecast",
    page_icon="💥",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .spike-alert {
        background: linear-gradient(135deg, #ff7979 0%, #ff6b6b 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(255,107,107,0.3);
    }

    .price-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #e74c3c;
        margin: 1rem 0;
    }

    .volatility-indicator {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }

    .metric-highlight {
        font-size: 2rem;
        font-weight: bold;
        color: #e74c3c;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_forecast_data():
    """Load forecast data."""
    try:
        import os
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
        base = pd.read_csv(os.path.join(data_dir, "forecast_baseline.csv"), parse_dates=["datetime"])
        shock = pd.read_csv(os.path.join(data_dir, "forecast_scenario_shock.csv"), parse_dates=["datetime"])
        delta = pd.read_csv(os.path.join(data_dir, "forecast_scenario_delta.csv"), parse_dates=["datetime"])

        for df in [base, shock, delta]:
            if "region" in df.columns:
                df["region"] = df["region"].astype(str)

        return base, shock, delta
    except FileNotFoundError:
        st.error("Forecast data not found. Please run the automation pipeline first.")
        return None, None, None

def detect_price_spikes(df, threshold_percentile=95):
    """Detect price spikes based on statistical threshold."""
    threshold = np.percentile(df['forecast_price'], threshold_percentile)
    df['is_spike'] = df['forecast_price'] > threshold
    return df, threshold

def create_price_spike_chart(base_df, shock_df, selected_region):
    """Create comprehensive price spike visualization."""
    # Filter for selected region
    base_region = base_df[base_df['region'] == selected_region].copy()
    shock_region = shock_df[shock_df['region'] == selected_region].copy()

    # Detect spikes
    base_region, base_threshold = detect_price_spikes(base_region)
    shock_region, shock_threshold = detect_price_spikes(shock_region)

    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=(
            f'📈 Price Trends & Spikes - {selected_region}',
            f'💥 Price Spike Intensity Analysis'
        ),
        vertical_spacing=0.1,
        specs=[[{"secondary_y": True}], [{"secondary_y": False}]]
    )

    # Main price trends
    fig.add_trace(
        go.Scatter(
            x=base_region['datetime'],
            y=base_region['forecast_price'],
            name='Baseline Price',
            line=dict(color='#3498db', width=2),
            opacity=0.8
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=shock_region['datetime'],
            y=shock_region['forecast_price'],
            name='Shock Scenario Price',
            line=dict(color='#e74c3c', width=2),
            opacity=0.8
        ),
        row=1, col=1
    )

    # Spike markers
    base_spikes = base_region[base_region['is_spike']]
    shock_spikes = shock_region[shock_region['is_spike']]

    if len(base_spikes) > 0:
        fig.add_trace(
            go.Scatter(
                x=base_spikes['datetime'],
                y=base_spikes['forecast_price'],
                mode='markers',
                name='Baseline Spikes',
                marker=dict(color='#3498db', size=10, symbol='triangle-up'),
                opacity=0.8
            ),
            row=1, col=1
        )

    if len(shock_spikes) > 0:
        fig.add_trace(
            go.Scatter(
                x=shock_spikes['datetime'],
                y=shock_spikes['forecast_price'],
                mode='markers',
                name='Shock Spikes',
                marker=dict(color='#e74c3c', size=12, symbol='triangle-up'),
                opacity=0.8
            ),
            row=1, col=1
        )

    # Threshold lines
    fig.add_hline(
        y=base_threshold,
        line_dash="dash",
        line_color="#3498db",
        annotation_text=f"Baseline Threshold: ${base_threshold:.2f}",
        row=1, col=1
    )

    fig.add_hline(
        y=shock_threshold,
        line_dash="dash",
        line_color="#e74c3c",
        annotation_text=f"Shock Threshold: ${shock_threshold:.2f}",
        row=1, col=1
    )

    # Price delta (shock - baseline)
    price_delta = shock_region['forecast_price'] - base_region['forecast_price']

    fig.add_trace(
        go.Scatter(
            x=shock_region['datetime'],
            y=price_delta,
            name='Price Delta (Shock - Baseline)',
            line=dict(color='#f39c12', width=3),
            fill='tonexty'
        ),
        row=2, col=1
    )

    # Add zero line
    fig.add_hline(y=0, line_dash="solid", line_color="gray", opacity=0.5, row=2, col=1)

    fig.update_layout(
        height=700,
        template="plotly_white",
        title_text="💥 Price Spike Analysis Dashboard",
        title_x=0.5
    )

    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_yaxes(title_text="Price ($/MWh)", row=1, col=1)
    fig.update_yaxes(title_text="Price Delta ($/MWh)", row=2, col=1)

    return fig

def create_spike_distribution_chart(base_df, shock_df):
    """Create distribution analysis of price spikes."""
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('📊 Price Distribution', '⏰ Spike Timing Analysis'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}]]
    )

    # Price distribution histogram
    fig.add_trace(
        go.Histogram(
            x=base_df['forecast_price'],
            name='Baseline Distribution',
            opacity=0.7,
            nbinsx=30,
            marker_color='#3498db'
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Histogram(
            x=shock_df['forecast_price'],
            name='Shock Distribution',
            opacity=0.7,
            nbinsx=30,
            marker_color='#e74c3c'
        ),
        row=1, col=1
    )

    # Spike timing analysis by hour
    base_spikes, _ = detect_price_spikes(base_df)
    shock_spikes, _ = detect_price_spikes(shock_df)

    base_spike_hours = base_spikes[base_spikes['is_spike']]['datetime'].dt.hour.value_counts().sort_index()
    shock_spike_hours = shock_spikes[shock_spikes['is_spike']]['datetime'].dt.hour.value_counts().sort_index()

    fig.add_trace(
        go.Bar(
            x=base_spike_hours.index,
            y=base_spike_hours.values,
            name='Baseline Spike Count',
            marker_color='#3498db',
            opacity=0.7
        ),
        row=1, col=2
    )

    fig.add_trace(
        go.Bar(
            x=shock_spike_hours.index,
            y=shock_spike_hours.values,
            name='Shock Spike Count',
            marker_color='#e74c3c',
            opacity=0.7
        ),
        row=1, col=2
    )

    fig.update_layout(
        height=400,
        template="plotly_white",
        title_text="📊 Price Spike Distribution & Timing",
        barmode='overlay'
    )

    fig.update_xaxes(title_text="Price ($/MWh)", row=1, col=1)
    fig.update_xaxes(title_text="Hour of Day", row=1, col=2)
    fig.update_yaxes(title_text="Frequency", row=1, col=1)
    fig.update_yaxes(title_text="Spike Count", row=1, col=2)

    return fig

def create_volatility_heatmap(base_df, shock_df):
    """Create volatility heatmap by region and time."""
    # Calculate hourly volatility by region
    base_vol = base_df.groupby(['region', base_df['datetime'].dt.hour])['forecast_price'].std().reset_index()
    shock_vol = shock_df.groupby(['region', shock_df['datetime'].dt.hour])['forecast_price'].std().reset_index()

    # Pivot for heatmap
    base_matrix = base_vol.pivot(index='region', columns='datetime', values='forecast_price')
    shock_matrix = shock_vol.pivot(index='region', columns='datetime', values='forecast_price')

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('🌡️ Baseline Volatility', '🌡️ Shock Scenario Volatility'),
        specs=[[{"type": "heatmap"}, {"type": "heatmap"}]]
    )

    fig.add_trace(
        go.Heatmap(
            z=base_matrix.values,
            x=[f"{h:02d}:00" for h in base_matrix.columns],
            y=base_matrix.index,
            colorscale='Blues',
            name='Baseline',
            hovertemplate='Region: %{y}<br>Hour: %{x}<br>Volatility: $%{z:.2f}<extra></extra>'
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Heatmap(
            z=shock_matrix.values,
            x=[f"{h:02d}:00" for h in shock_matrix.columns],
            y=shock_matrix.index,
            colorscale='Reds',
            name='Shock',
            hovertemplate='Region: %{y}<br>Hour: %{x}<br>Volatility: $%{z:.2f}<extra></extra>'
        ),
        row=1, col=2
    )

    fig.update_layout(
        height=400,
        template="plotly_white",
        title_text="🌡️ Price Volatility Heatmap by Region & Time"
    )

    return fig

def calculate_risk_metrics(base_df, shock_df, selected_region):
    """Calculate comprehensive risk metrics."""
    base_region = base_df[base_df['region'] == selected_region]
    shock_region = shock_df[shock_df['region'] == selected_region]

    metrics = {}

    # Basic statistics
    metrics['base_mean'] = base_region['forecast_price'].mean()
    metrics['shock_mean'] = shock_region['forecast_price'].mean()
    metrics['base_std'] = base_region['forecast_price'].std()
    metrics['shock_std'] = shock_region['forecast_price'].std()

    # Risk metrics
    metrics['var_95_base'] = np.percentile(base_region['forecast_price'], 95)
    metrics['var_95_shock'] = np.percentile(shock_region['forecast_price'], 95)

    # Spike analysis
    base_spikes, base_threshold = detect_price_spikes(base_region)
    shock_spikes, shock_threshold = detect_price_spikes(shock_region)

    metrics['spike_count_base'] = base_spikes['is_spike'].sum()
    metrics['spike_count_shock'] = shock_spikes['is_spike'].sum()
    metrics['spike_intensity_base'] = base_spikes[base_spikes['is_spike']]['forecast_price'].mean() if metrics['spike_count_base'] > 0 else 0
    metrics['spike_intensity_shock'] = shock_spikes[shock_spikes['is_spike']]['forecast_price'].mean() if metrics['spike_count_shock'] > 0 else 0

    # Financial impact
    price_delta = shock_region['forecast_price'] - base_region['forecast_price']
    metrics['max_price_increase'] = price_delta.max()
    metrics['avg_price_increase'] = price_delta.mean()

    return metrics

# Main application
def main():
    st.markdown("# 💥 Price & Spikes Analysis")
    st.markdown("## Advanced price volatility and spike detection dashboard")

    # Load data
    base_df, shock_df, delta_df = load_forecast_data()

    if base_df is None:
        return

    # Sidebar controls
    st.sidebar.markdown("## 🎛️ Analysis Controls")

    # Region selector
    regions = sorted(base_df["region"].unique())
    selected_region = st.sidebar.selectbox("🌍 Select Region", regions, index=0)

    # Spike sensitivity
    spike_threshold = st.sidebar.slider(
        "💥 Spike Detection Sensitivity",
        min_value=85,
        max_value=99,
        value=95,
        help="Percentile threshold for spike detection (higher = more sensitive)"
    )

    # Analysis type
    analysis_type = st.sidebar.selectbox(
        "📊 Analysis Type",
        ["Overview", "Detailed Spikes", "Distribution", "Volatility Heatmap", "Risk Metrics"]
    )

    # Risk assessment
    st.markdown("### ⚠️ Price Risk Alert System")

    # Calculate risk metrics
    risk_metrics = calculate_risk_metrics(base_df, shock_df, selected_region)

    # Risk level determination
    price_increase_pct = ((risk_metrics['shock_mean'] / risk_metrics['base_mean'] - 1) * 100) if risk_metrics['base_mean'] > 0 else 0
    spike_increase = risk_metrics['spike_count_shock'] - risk_metrics['spike_count_base']

    if price_increase_pct > 30 or spike_increase > 10:
        risk_level = "🔴 CRITICAL"
        risk_color = "#e74c3c"
    elif price_increase_pct > 15 or spike_increase > 5:
        risk_level = "🟡 HIGH"
        risk_color = "#f39c12"
    elif price_increase_pct > 5 or spike_increase > 0:
        risk_level = "🟠 MEDIUM"
        risk_color = "#e67e22"
    else:
        risk_level = "🟢 LOW"
        risk_color = "#27ae60"

    st.markdown(f"""
    <div class="spike-alert">
        <h3>🚨 Risk Level: {risk_level}</h3>
        <div style="display: flex; justify-content: space-between; margin-top: 1rem;">
            <div>
                <strong>Price Impact:</strong> {price_increase_pct:+.1f}%<br>
                <strong>Spike Increase:</strong> +{spike_increase} events<br>
                <strong>Max Price Jump:</strong> ${risk_metrics['max_price_increase']:+.2f}/MWh
            </div>
            <div>
                <strong>Region:</strong> {selected_region}<br>
                <strong>VaR 95%:</strong> ${risk_metrics['var_95_shock']:.2f}/MWh<br>
                <strong>Volatility:</strong> ${risk_metrics['shock_std']:.2f}/MWh
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Main analysis content
    if analysis_type == "Overview":
        # Key metrics cards
        st.markdown("### 📊 Price Performance Metrics")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div class="price-card">
                <h4>💰 Average Price</h4>
                <div class="metric-highlight">${risk_metrics['base_mean']:.2f}</div>
                <p>Baseline: ${risk_metrics['base_mean']:.2f}/MWh<br>
                Shock: ${risk_metrics['shock_mean']:.2f}/MWh</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="price-card">
                <h4>📈 Price Volatility</h4>
                <div class="metric-highlight">${risk_metrics['shock_std']:.2f}</div>
                <p>Baseline: ${risk_metrics['base_std']:.2f}/MWh<br>
                Shock: ${risk_metrics['shock_std']:.2f}/MWh</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="price-card">
                <h4>💥 Spike Count</h4>
                <div class="metric-highlight">{risk_metrics['spike_count_shock']}</div>
                <p>Baseline: {risk_metrics['spike_count_base']} spikes<br>
                Shock: {risk_metrics['spike_count_shock']} spikes</p>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="price-card">
                <h4>⚡ Max Impact</h4>
                <div class="metric-highlight">${risk_metrics['max_price_increase']:+.2f}</div>
                <p>Peak price increase<br>during shock scenario</p>
            </div>
            """, unsafe_allow_html=True)

        # Main spike chart
        fig_spikes = create_price_spike_chart(base_df, shock_df, selected_region)
        st.plotly_chart(fig_spikes, use_container_width=True)

    elif analysis_type == "Detailed Spikes":
        st.markdown(f"### 💥 Detailed Spike Analysis - {selected_region}")

        # Spike detection with custom threshold
        base_region = base_df[base_df['region'] == selected_region].copy()
        shock_region = shock_df[shock_df['region'] == selected_region].copy()

        # Apply custom threshold
        base_threshold = np.percentile(base_region['forecast_price'], spike_threshold)
        shock_threshold = np.percentile(shock_region['forecast_price'], spike_threshold)

        base_region['is_spike'] = base_region['forecast_price'] > base_threshold
        shock_region['is_spike'] = shock_region['forecast_price'] > shock_threshold

        # Spike statistics
        base_spikes = base_region[base_region['is_spike']]
        shock_spikes = shock_region[shock_region['is_spike']]

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📊 Baseline Scenario Spikes")
            if len(base_spikes) > 0:
                st.dataframe(
                    base_spikes[['datetime', 'forecast_price']].head(10),
                    use_container_width=True
                )
            else:
                st.info("No spikes detected in baseline scenario")

        with col2:
            st.markdown("#### 🚨 Shock Scenario Spikes")
            if len(shock_spikes) > 0:
                st.dataframe(
                    shock_spikes[['datetime', 'forecast_price']].head(10),
                    use_container_width=True
                )
            else:
                st.info("No spikes detected in shock scenario")

        # Spike timing analysis
        if len(shock_spikes) > 0:
            st.markdown("#### ⏰ Spike Timing Patterns")
            spike_hours = shock_spikes['datetime'].dt.hour.value_counts().sort_index()

            fig_timing = px.bar(
                x=spike_hours.index,
                y=spike_hours.values,
                title="Price Spikes by Hour of Day",
                labels={'x': 'Hour of Day', 'y': 'Number of Spikes'},
                color=spike_hours.values,
                color_continuous_scale='Reds'
            )

            fig_timing.update_layout(
                template="plotly_white",
                height=400
            )

            st.plotly_chart(fig_timing, use_container_width=True)

    elif analysis_type == "Distribution":
        st.markdown("### 📊 Price Distribution Analysis")
        fig_dist = create_spike_distribution_chart(base_df, shock_df)
        st.plotly_chart(fig_dist, use_container_width=True)

        # Statistical comparison
        st.markdown("#### 📈 Statistical Comparison")

        col1, col2 = st.columns(2)

        with col1:
            base_stats = base_df['forecast_price'].describe()
            st.markdown("**Baseline Statistics**")
            st.dataframe(base_stats.to_frame().T, use_container_width=True)

        with col2:
            shock_stats = shock_df['forecast_price'].describe()
            st.markdown("**Shock Scenario Statistics**")
            st.dataframe(shock_stats.to_frame().T, use_container_width=True)

    elif analysis_type == "Volatility Heatmap":
        st.markdown("### 🌡️ Price Volatility Analysis")
        fig_heatmap = create_volatility_heatmap(base_df, shock_df)
        st.plotly_chart(fig_heatmap, use_container_width=True)

        # Volatility insights
        st.markdown("#### 💡 Volatility Insights")

        base_vol_by_hour = base_df.groupby(base_df['datetime'].dt.hour)['forecast_price'].std()
        shock_vol_by_hour = shock_df.groupby(shock_df['datetime'].dt.hour)['forecast_price'].std()

        peak_vol_hour = shock_vol_by_hour.idxmax()
        peak_vol_value = shock_vol_by_hour.max()

        st.info(f"""
        **🕐 Peak Volatility Time:** {peak_vol_hour:02d}:00

        **📊 Peak Volatility:** ${peak_vol_value:.2f}/MWh

        **📈 Volatility Increase:** {((shock_vol_by_hour.mean() / base_vol_by_hour.mean() - 1) * 100):+.1f}% on average
        """)

    elif analysis_type == "Risk Metrics":
        st.markdown("### 📊 Comprehensive Risk Metrics")

        # Value at Risk analysis
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📈 Value at Risk (VaR)")
            var_levels = [90, 95, 99]
            var_data = []

            for level in var_levels:
                base_var = np.percentile(base_df[base_df['region'] == selected_region]['forecast_price'], level)
                shock_var = np.percentile(shock_df[shock_df['region'] == selected_region]['forecast_price'], level)
                var_data.append({
                    'Confidence Level (%)': level,
                    'Baseline VaR ($/MWh)': round(base_var, 2),
                    'Shock VaR ($/MWh)': round(shock_var, 2),
                    'Risk Increase (%)': round(((shock_var / base_var - 1) * 100), 1)
                })

            st.dataframe(pd.DataFrame(var_data), use_container_width=True)

        with col2:
            st.markdown("#### ⚡ Extreme Event Analysis")

            # Calculate extreme events (top 1% of prices)
            base_region = base_df[base_df['region'] == selected_region]
            shock_region = shock_df[shock_df['region'] == selected_region]

            base_extreme = np.percentile(base_region['forecast_price'], 99)
            shock_extreme = np.percentile(shock_region['forecast_price'], 99)

            extreme_events_base = (base_region['forecast_price'] > base_extreme).sum()
            extreme_events_shock = (shock_region['forecast_price'] > shock_extreme).sum()

            st.metric(
                "Extreme Events (99th percentile)",
                f"{extreme_events_shock}",
                f"{extreme_events_shock - extreme_events_base:+d} vs baseline"
            )

            st.metric(
                "Extreme Price Level",
                f"${shock_extreme:.2f}/MWh",
                f"${shock_extreme - base_extreme:+.2f} vs baseline"
            )

        # Financial impact calculator
        st.markdown("#### 💰 Financial Impact Calculator")

        col1, col2, col3 = st.columns(3)

        with col1:
            portfolio_mw = st.number_input("Portfolio Size (MW)", value=100.0, min_value=0.0, step=10.0)

        with col2:
            exposure_hours = st.number_input("Exposure Hours", value=24.0, min_value=1.0, step=1.0)

        with col3:
            confidence_level = st.selectbox("Confidence Level", [90, 95, 99], index=1)

        # Calculate potential loss
        region_data = shock_df[shock_df['region'] == selected_region]
        var_price = np.percentile(region_data['forecast_price'], confidence_level)
        baseline_price = base_df[base_df['region'] == selected_region]['forecast_price'].mean()

        potential_loss = (var_price - baseline_price) * portfolio_mw * exposure_hours

        if potential_loss > 0:
            st.error(f"""
            **🚨 Potential Additional Cost at {confidence_level}% confidence:**

            **${potential_loss:,.0f}**

            *Based on {portfolio_mw:.0f} MW portfolio over {exposure_hours:.0f} hours*
            """)
        else:
            st.success(f"""
            **✅ No additional cost risk identified at {confidence_level}% confidence level**
            """)

if __name__ == "__main__":
    main()
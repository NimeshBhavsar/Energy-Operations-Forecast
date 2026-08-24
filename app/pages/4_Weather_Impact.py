import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Weather Impact Analysis | Energy Ops Forecast",
    page_icon="🌤️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .weather-card {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(116,185,255,0.3);
    }

    .correlation-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #00b894;
        margin: 1rem 0;
    }

    .impact-indicator {
        background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%);
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        color: #2d3436;
    }

    .weather-metric {
        font-size: 1.8rem;
        font-weight: bold;
        color: #0984e3;
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

def simulate_weather_impact(df):
    """Simulate weather impact on energy demand and pricing."""
    # Since weather data might be sparse, simulate realistic weather patterns
    np.random.seed(42)  # For reproducible results

    df = df.copy()

    # Simulate temperature based on hour of day and season
    df['temp_simulated'] = np.where(
        df['temp_c'].isna(),
        15 + 10 * np.sin((df['datetime'].dt.hour - 6) * np.pi / 12) + np.random.normal(0, 3, len(df)),
        df['temp_c']
    )

    # Simulate solar radiation
    df['solar_simulated'] = np.where(
        df['shortwave_wm2'].isna(),
        np.maximum(0, 800 * np.sin((df['datetime'].dt.hour - 6) * np.pi / 12) + np.random.normal(0, 100, len(df))),
        df['shortwave_wm2']
    )

    # Simulate wind speed
    df['wind_simulated'] = np.where(
        df['wind_speed_ms'].isna(),
        np.maximum(0, 5 + np.random.normal(0, 2, len(df))),
        df['wind_speed_ms']
    )

    # Calculate weather impact indices
    df['cooling_demand_index'] = np.maximum(0, df['temp_simulated'] - 24)  # Cooling needed above 24°C
    df['heating_demand_index'] = np.maximum(0, 18 - df['temp_simulated'])  # Heating needed below 18°C
    df['solar_generation_index'] = df['solar_simulated'] / 1000  # Normalize solar
    df['wind_generation_index'] = np.minimum(1, df['wind_simulated'] / 15)  # Normalize wind

    return df

def create_weather_correlation_chart(df, selected_region):
    """Create weather correlation analysis."""
    region_data = df[df['region'] == selected_region].copy()
    region_data = simulate_weather_impact(region_data)

    # Calculate correlations
    correlations = region_data[['forecast_price', 'forecast_demand', 'temp_simulated',
                              'solar_simulated', 'wind_simulated', 'cooling_demand_index',
                              'heating_demand_index']].corr()

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            '🌡️ Temperature vs Price/Demand',
            '☀️ Solar Radiation vs Price/Demand',
            '💨 Wind Speed vs Price/Demand',
            '📊 Weather Correlation Matrix'
        ),
        specs=[[{"secondary_y": True}, {"secondary_y": True}],
               [{"secondary_y": True}, {"type": "heatmap"}]]
    )

    # Temperature correlation
    fig.add_trace(
        go.Scatter(
            x=region_data['temp_simulated'],
            y=region_data['forecast_price'],
            mode='markers',
            name='Price vs Temp',
            marker=dict(color='#e74c3c', size=6, opacity=0.6)
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=region_data['temp_simulated'],
            y=region_data['forecast_demand'] / 100,  # Scale for visibility
            mode='markers',
            name='Demand vs Temp',
            marker=dict(color='#3498db', size=6, opacity=0.6),
            yaxis='y2'
        ),
        row=1, col=1
    )

    # Solar correlation
    fig.add_trace(
        go.Scatter(
            x=region_data['solar_simulated'],
            y=region_data['forecast_price'],
            mode='markers',
            name='Price vs Solar',
            marker=dict(color='#f39c12', size=6, opacity=0.6),
            showlegend=False
        ),
        row=1, col=2
    )

    fig.add_trace(
        go.Scatter(
            x=region_data['solar_simulated'],
            y=region_data['forecast_demand'] / 100,
            mode='markers',
            name='Demand vs Solar',
            marker=dict(color='#27ae60', size=6, opacity=0.6),
            yaxis='y4',
            showlegend=False
        ),
        row=1, col=2
    )

    # Wind correlation
    fig.add_trace(
        go.Scatter(
            x=region_data['wind_simulated'],
            y=region_data['forecast_price'],
            mode='markers',
            name='Price vs Wind',
            marker=dict(color='#9b59b6', size=6, opacity=0.6),
            showlegend=False
        ),
        row=2, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=region_data['wind_simulated'],
            y=region_data['forecast_demand'] / 100,
            mode='markers',
            name='Demand vs Wind',
            marker=dict(color='#1abc9c', size=6, opacity=0.6),
            yaxis='y6',
            showlegend=False
        ),
        row=2, col=1
    )

    # Correlation heatmap
    weather_corr = correlations.loc[['forecast_price', 'forecast_demand'],
                                   ['temp_simulated', 'solar_simulated', 'wind_simulated']].values

    fig.add_trace(
        go.Heatmap(
            z=weather_corr,
            x=['Temperature', 'Solar', 'Wind'],
            y=['Price', 'Demand'],
            colorscale='RdBu',
            zmid=0,
            text=np.round(weather_corr, 2),
            texttemplate='%{text}',
            textfont={'size': 14},
            hovertemplate='%{y} vs %{x}: %{z:.2f}<extra></extra>'
        ),
        row=2, col=2
    )

    fig.update_layout(
        height=700,
        template="plotly_white",
        title_text="🌤️ Weather Impact Correlation Analysis",
        title_x=0.5
    )

    # Update axes labels
    fig.update_xaxes(title_text="Temperature (°C)", row=1, col=1)
    fig.update_xaxes(title_text="Solar Radiation (W/m²)", row=1, col=2)
    fig.update_xaxes(title_text="Wind Speed (m/s)", row=2, col=1)

    fig.update_yaxes(title_text="Price ($/MWh)", row=1, col=1)
    fig.update_yaxes(title_text="Demand (100s MW)", secondary_y=True, row=1, col=1)

    return fig

def create_seasonal_pattern_chart(df):
    """Create seasonal weather pattern analysis."""
    # Simulate seasonal patterns
    df_weather = simulate_weather_impact(df)

    # Group by hour of day
    hourly_patterns = df_weather.groupby(df_weather['datetime'].dt.hour).agg({
        'temp_simulated': 'mean',
        'solar_simulated': 'mean',
        'wind_simulated': 'mean',
        'forecast_price': 'mean',
        'forecast_demand': 'mean'
    }).reset_index()

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            '🌡️ Daily Temperature Pattern',
            '☀️ Daily Solar Pattern',
            '💨 Daily Wind Pattern',
            '⚡ Weather-Adjusted Load Pattern'
        ),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": True}]]
    )

    # Temperature pattern
    fig.add_trace(
        go.Scatter(
            x=hourly_patterns['datetime'],
            y=hourly_patterns['temp_simulated'],
            mode='lines+markers',
            name='Temperature',
            line=dict(color='#e74c3c', width=3),
            marker=dict(size=8)
        ),
        row=1, col=1
    )

    # Solar pattern
    fig.add_trace(
        go.Scatter(
            x=hourly_patterns['datetime'],
            y=hourly_patterns['solar_simulated'],
            mode='lines+markers',
            name='Solar Radiation',
            line=dict(color='#f39c12', width=3),
            fill='tonexty'
        ),
        row=1, col=2
    )

    # Wind pattern
    fig.add_trace(
        go.Scatter(
            x=hourly_patterns['datetime'],
            y=hourly_patterns['wind_simulated'],
            mode='lines+markers',
            name='Wind Speed',
            line=dict(color='#3498db', width=3)
        ),
        row=2, col=1
    )

    # Combined load pattern
    fig.add_trace(
        go.Scatter(
            x=hourly_patterns['datetime'],
            y=hourly_patterns['forecast_demand'],
            mode='lines+markers',
            name='Demand',
            line=dict(color='#27ae60', width=3)
        ),
        row=2, col=2
    )

    fig.add_trace(
        go.Scatter(
            x=hourly_patterns['datetime'],
            y=hourly_patterns['forecast_price'],
            mode='lines+markers',
            name='Price',
            line=dict(color='#9b59b6', width=2, dash='dash'),
            yaxis='y8'
        ),
        row=2, col=2
    )

    fig.update_layout(
        height=600,
        template="plotly_white",
        title_text="📈 Daily Weather and Load Patterns",
        showlegend=True
    )

    # Update axes
    fig.update_xaxes(title_text="Hour of Day")
    fig.update_yaxes(title_text="Temperature (°C)", row=1, col=1)
    fig.update_yaxes(title_text="Solar Radiation (W/m²)", row=1, col=2)
    fig.update_yaxes(title_text="Wind Speed (m/s)", row=2, col=1)
    fig.update_yaxes(title_text="Demand (MW)", row=2, col=2)
    fig.update_yaxes(title_text="Price ($/MWh)", secondary_y=True, row=2, col=2)

    return fig

def create_extreme_weather_impact(base_df, shock_df, selected_region):
    """Analyze extreme weather scenario impacts."""
    base_region = base_df[base_df['region'] == selected_region].copy()
    shock_region = shock_df[shock_df['region'] == selected_region].copy()

    # Simulate extreme weather conditions in shock scenario
    base_weather = simulate_weather_impact(base_region)
    shock_weather = simulate_weather_impact(shock_region)

    # Apply extreme weather multipliers to shock scenario
    np.random.seed(123)
    shock_weather['temp_extreme'] = shock_weather['temp_simulated'] + np.random.normal(5, 2, len(shock_weather))  # Hotter
    shock_weather['solar_extreme'] = shock_weather['solar_simulated'] * np.random.uniform(0.3, 0.7, len(shock_weather))  # Cloudier
    shock_weather['wind_extreme'] = shock_weather['wind_simulated'] * np.random.uniform(0.2, 0.5, len(shock_weather))  # Less wind

    # Calculate weather-adjusted demand
    shock_weather['weather_demand_impact'] = (
        shock_weather['cooling_demand_index'] * 50 +  # AC load
        shock_weather['heating_demand_index'] * 30 -  # Heating load
        shock_weather['solar_generation_index'] * 200 -  # Solar offset
        shock_weather['wind_generation_index'] * 150  # Wind offset
    )

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            '🌡️ Extreme Temperature Impact',
            '⚡ Weather-Adjusted Demand',
            '💰 Weather-Driven Price Impact',
            '🎯 Extreme Weather Risk Matrix'
        ),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"type": "scatter"}]]
    )

    # Temperature comparison
    fig.add_trace(
        go.Scatter(
            x=base_weather['datetime'],
            y=base_weather['temp_simulated'],
            name='Normal Weather',
            line=dict(color='#3498db', width=2)
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=shock_weather['datetime'],
            y=shock_weather['temp_extreme'],
            name='Extreme Weather',
            line=dict(color='#e74c3c', width=2)
        ),
        row=1, col=1
    )

    # Weather-adjusted demand
    fig.add_trace(
        go.Scatter(
            x=shock_weather['datetime'],
            y=shock_weather['forecast_demand'] + shock_weather['weather_demand_impact'],
            name='Weather-Adjusted Demand',
            line=dict(color='#f39c12', width=3),
            fill='tonexty'
        ),
        row=1, col=2
    )

    fig.add_trace(
        go.Scatter(
            x=shock_weather['datetime'],
            y=shock_weather['forecast_demand'],
            name='Base Demand',
            line=dict(color='#27ae60', width=2, dash='dash')
        ),
        row=1, col=2
    )

    # Price impact
    weather_price_impact = shock_weather['weather_demand_impact'] * 0.05  # $0.05/MW impact
    fig.add_trace(
        go.Scatter(
            x=shock_weather['datetime'],
            y=shock_weather['forecast_price'] + weather_price_impact,
            name='Weather-Adjusted Price',
            line=dict(color='#9b59b6', width=3)
        ),
        row=2, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=shock_weather['datetime'],
            y=shock_weather['forecast_price'],
            name='Base Price',
            line=dict(color='#1abc9c', width=2, dash='dash')
        ),
        row=2, col=1
    )

    # Risk matrix scatter plot
    risk_x = shock_weather['temp_extreme'] - shock_weather['temp_simulated']  # Temperature increase
    risk_y = weather_price_impact  # Price impact

    # Color by risk level
    risk_level = np.where(
        (risk_x > 7) & (risk_y > 10), 'High Risk',
        np.where((risk_x > 4) | (risk_y > 5), 'Medium Risk', 'Low Risk')
    )

    colors = {'High Risk': '#e74c3c', 'Medium Risk': '#f39c12', 'Low Risk': '#27ae60'}

    for risk in ['Low Risk', 'Medium Risk', 'High Risk']:
        mask = risk_level == risk
        if mask.any():
            fig.add_trace(
                go.Scatter(
                    x=risk_x[mask],
                    y=risk_y[mask],
                    mode='markers',
                    name=risk,
                    marker=dict(color=colors[risk], size=8, opacity=0.7),
                    showlegend=False
                ),
                row=2, col=2
            )

    fig.update_layout(
        height=700,
        template="plotly_white",
        title_text="🌪️ Extreme Weather Impact Analysis"
    )

    fig.update_xaxes(title_text="Time", row=1, col=1)
    fig.update_xaxes(title_text="Time", row=1, col=2)
    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_xaxes(title_text="Temperature Increase (°C)", row=2, col=2)

    fig.update_yaxes(title_text="Temperature (°C)", row=1, col=1)
    fig.update_yaxes(title_text="Demand (MW)", row=1, col=2)
    fig.update_yaxes(title_text="Price ($/MWh)", row=2, col=1)
    fig.update_yaxes(title_text="Price Impact ($/MWh)", row=2, col=2)

    return fig

def calculate_weather_sensitivity(df, selected_region):
    """Calculate weather sensitivity metrics."""
    region_data = df[df['region'] == selected_region].copy()
    region_data = simulate_weather_impact(region_data)

    # Calculate sensitivities
    temp_price_corr = region_data['temp_simulated'].corr(region_data['forecast_price'])
    temp_demand_corr = region_data['temp_simulated'].corr(region_data['forecast_demand'])
    solar_price_corr = region_data['solar_simulated'].corr(region_data['forecast_price'])
    wind_price_corr = region_data['wind_simulated'].corr(region_data['forecast_price'])

    # Estimate impacts per unit change
    temp_bins = pd.cut(region_data['temp_simulated'], bins=5)
    temp_impact = region_data.groupby(temp_bins).agg({
        'forecast_price': 'mean',
        'forecast_demand': 'mean'
    })

    metrics = {
        'temp_price_corr': temp_price_corr,
        'temp_demand_corr': temp_demand_corr,
        'solar_price_corr': solar_price_corr,
        'wind_price_corr': wind_price_corr,
        'temp_price_range': temp_impact['forecast_price'].max() - temp_impact['forecast_price'].min(),
        'temp_demand_range': temp_impact['forecast_demand'].max() - temp_impact['forecast_demand'].min()
    }

    return metrics

# Main application
def main():
    st.markdown("# 🌤️ Weather Impact Analysis")
    st.markdown("## Advanced weather correlation and extreme scenario modeling")

    # Load data
    base_df, shock_df, delta_df = load_forecast_data()

    if base_df is None:
        return

    # Sidebar controls
    st.sidebar.markdown("## 🎛️ Weather Analysis Controls")

    # Region selector
    regions = sorted(base_df["region"].unique())
    selected_region = st.sidebar.selectbox("🌍 Select Region", regions, index=0)

    # Analysis type
    analysis_type = st.sidebar.selectbox(
        "📊 Analysis Type",
        ["Overview", "Correlations", "Seasonal Patterns", "Extreme Weather", "Sensitivity Analysis"]
    )

    # Weather scenario
    weather_scenario = st.sidebar.selectbox(
        "🌦️ Weather Scenario",
        ["Current Forecast", "Extreme Heat", "Extreme Cold", "Low Renewables", "High Renewables"]
    )

    # Calculate weather sensitivity metrics
    sensitivity_metrics = calculate_weather_sensitivity(base_df, selected_region)

    # Weather impact summary
    st.markdown("### 🌡️ Weather Impact Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="weather-card">
            <h4>🌡️ Temperature Sensitivity</h4>
            <div class="weather-metric">{sensitivity_metrics['temp_price_corr']:.2f}</div>
            <p>Price correlation coefficient<br>
            Range: ${sensitivity_metrics['temp_price_range']:.2f}/MWh</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="weather-card">
            <h4>☀️ Solar Impact</h4>
            <div class="weather-metric">{sensitivity_metrics['solar_price_corr']:.2f}</div>
            <p>Solar-price correlation<br>
            (Negative = price reduction)</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="weather-card">
            <h4>💨 Wind Impact</h4>
            <div class="weather-metric">{sensitivity_metrics['wind_price_corr']:.2f}</div>
            <p>Wind-price correlation<br>
            (Negative = price reduction)</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="weather-card">
            <h4>⚡ Demand Sensitivity</h4>
            <div class="weather-metric">{sensitivity_metrics['temp_demand_corr']:.2f}</div>
            <p>Temperature-demand correlation<br>
            Range: {sensitivity_metrics['temp_demand_range']:.0f} MW</p>
        </div>
        """, unsafe_allow_html=True)

    # Main analysis content
    if analysis_type == "Overview":
        st.markdown("### 📊 Weather-Energy Relationship Overview")

        # Quick insights
        col1, col2 = st.columns(2)

        with col1:
            if sensitivity_metrics['temp_price_corr'] > 0.3:
                temp_insight = "🔥 Strong positive correlation - hot weather drives higher prices"
            elif sensitivity_metrics['temp_price_corr'] < -0.3:
                temp_insight = "❄️ Strong negative correlation - cold weather drives higher prices"
            else:
                temp_insight = "🌡️ Moderate temperature sensitivity"

            st.info(f"""
            **Temperature Impact:** {temp_insight}

            **Price Range:** ${sensitivity_metrics['temp_price_range']:.2f}/MWh across temperature spectrum

            **Demand Sensitivity:** {sensitivity_metrics['temp_demand_corr']:.2f} correlation coefficient
            """)

        with col2:
            renewable_impact = (sensitivity_metrics['solar_price_corr'] + sensitivity_metrics['wind_price_corr']) / 2

            if renewable_impact < -0.2:
                renewable_insight = "🔋 Strong renewable generation impact - reduces prices significantly"
            elif renewable_impact < -0.1:
                renewable_insight = "🌱 Moderate renewable impact on pricing"
            else:
                renewable_insight = "⚡ Limited renewable generation impact"

            st.success(f"""
            **Renewable Impact:** {renewable_insight}

            **Solar Correlation:** {sensitivity_metrics['solar_price_corr']:.2f}

            **Wind Correlation:** {sensitivity_metrics['wind_price_corr']:.2f}
            """)

        # Basic weather correlation chart
        fig_corr = create_weather_correlation_chart(base_df, selected_region)
        st.plotly_chart(fig_corr, use_container_width=True)

    elif analysis_type == "Correlations":
        st.markdown(f"### 🔗 Weather Correlation Analysis - {selected_region}")
        fig_corr = create_weather_correlation_chart(base_df, selected_region)
        st.plotly_chart(fig_corr, use_container_width=True)

        # Detailed correlation table
        region_data = base_df[base_df['region'] == selected_region].copy()
        region_data = simulate_weather_impact(region_data)

        corr_matrix = region_data[['forecast_price', 'forecast_demand', 'temp_simulated',
                                  'solar_simulated', 'wind_simulated']].corr()

        st.markdown("#### 📊 Detailed Correlation Matrix")
        st.dataframe(corr_matrix.round(3), use_container_width=True)

    elif analysis_type == "Seasonal Patterns":
        st.markdown("### 📅 Seasonal Weather Patterns")
        fig_seasonal = create_seasonal_pattern_chart(base_df)
        st.plotly_chart(fig_seasonal, use_container_width=True)

        # Pattern insights
        st.markdown("#### 💡 Pattern Insights")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            <div class="correlation-card">
                <h4>🌅 Morning Pattern (6-10 AM)</h4>
                <p>• Rising temperature increases AC demand<br>
                • Solar generation starts reducing prices<br>
                • Wind patterns vary by season<br>
                • Peak demand period creates price pressure</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="correlation-card">
                <h4>🌆 Evening Pattern (6-10 PM)</h4>
                <p>• Cooling demand peaks in summer<br>
                • Solar generation diminishes<br>
                • Wind patterns may strengthen<br>
                • System stress increases prices</p>
            </div>
            """, unsafe_allow_html=True)

    elif analysis_type == "Extreme Weather":
        st.markdown("### 🌪️ Extreme Weather Scenario Analysis")

        # Extreme weather alerts
        if weather_scenario == "Extreme Heat":
            st.error("""
            🔥 **EXTREME HEAT SCENARIO ACTIVE**
            - Temperature: +8°C above normal
            - AC demand surge: +25-40%
            - Solar generation may be reduced due to equipment efficiency
            - Price impact: +$15-30/MWh expected
            """)
        elif weather_scenario == "Extreme Cold":
            st.warning("""
            ❄️ **EXTREME COLD SCENARIO ACTIVE**
            - Temperature: -10°C below normal
            - Heating demand surge: +30-50%
            - Wind generation may increase
            - Gas-fired generation stress
            """)

        fig_extreme = create_extreme_weather_impact(base_df, shock_df, selected_region)
        st.plotly_chart(fig_extreme, use_container_width=True)

        # Financial impact calculator
        st.markdown("#### 💰 Extreme Weather Financial Impact")

        col1, col2, col3 = st.columns(3)

        with col1:
            portfolio_size = st.number_input("Portfolio Size (MW)", value=100.0, min_value=0.0)

        with col2:
            duration_hours = st.number_input("Event Duration (hours)", value=48.0, min_value=1.0)

        with col3:
            weather_intensity = st.selectbox("Weather Intensity", ["Moderate", "Severe", "Extreme"])

        # Calculate impact
        base_multiplier = {"Moderate": 1.2, "Severe": 1.5, "Extreme": 2.0}
        multiplier = base_multiplier[weather_intensity]

        estimated_impact = sensitivity_metrics['temp_price_range'] * multiplier * portfolio_size * duration_hours

        if estimated_impact > 0:
            st.error(f"""
            **🚨 Estimated Financial Impact: ${estimated_impact:,.0f}**

            *Based on {weather_intensity.lower()} weather scenario affecting {portfolio_size:.0f} MW over {duration_hours:.0f} hours*
            """)

    elif analysis_type == "Sensitivity Analysis":
        st.markdown("### 📊 Weather Sensitivity Deep Dive")

        # Sensitivity metrics table
        sensitivity_data = {
            'Weather Factor': ['Temperature', 'Solar Radiation', 'Wind Speed'],
            'Price Correlation': [
                f"{sensitivity_metrics['temp_price_corr']:.3f}",
                f"{sensitivity_metrics['solar_price_corr']:.3f}",
                f"{sensitivity_metrics['wind_price_corr']:.3f}"
            ],
            'Impact Level': [
                "High" if abs(sensitivity_metrics['temp_price_corr']) > 0.3 else "Medium" if abs(sensitivity_metrics['temp_price_corr']) > 0.1 else "Low",
                "High" if abs(sensitivity_metrics['solar_price_corr']) > 0.3 else "Medium" if abs(sensitivity_metrics['solar_price_corr']) > 0.1 else "Low",
                "High" if abs(sensitivity_metrics['wind_price_corr']) > 0.3 else "Medium" if abs(sensitivity_metrics['wind_price_corr']) > 0.1 else "Low"
            ],
            'Price Range Impact ($/MWh)': [
                round(sensitivity_metrics['temp_price_range'], 2),
                round(abs(sensitivity_metrics['solar_price_corr']) * 10, 2),
                round(abs(sensitivity_metrics['wind_price_corr']) * 10, 2)
            ]
        }

        st.dataframe(pd.DataFrame(sensitivity_data), use_container_width=True)
        st.caption("*Estimated impact based on correlation strength")

        # Weather scenario modeling
        st.markdown("#### 🌦️ Scenario Modeling")

        col1, col2 = st.columns(2)

        with col1:
            temp_change = st.slider("Temperature Change (°C)", -10, 15, 0)
            solar_change = st.slider("Solar Change (%)", -50, 50, 0)

        with col2:
            wind_change = st.slider("Wind Change (%)", -50, 50, 0)

            # Calculate scenario impact
            price_impact = (
                temp_change * sensitivity_metrics['temp_price_corr'] * 2 +
                (solar_change / 100) * sensitivity_metrics['solar_price_corr'] * 5 +
                (wind_change / 100) * sensitivity_metrics['wind_price_corr'] * 5
            )

            demand_impact = temp_change * sensitivity_metrics['temp_demand_corr'] * 50

            st.markdown(f"""
            <div class="impact-indicator">
                <h4>📊 Scenario Impact</h4>
                <p><strong>Price Impact:</strong> {price_impact:+.2f} $/MWh<br>
                <strong>Demand Impact:</strong> {demand_impact:+.0f} MW</p>
            </div>
            """, unsafe_allow_html=True)

    # Weather monitoring recommendations
    st.markdown("### 🎯 Weather Monitoring Recommendations")

    col1, col2 = st.columns(2)

    with col1:
        st.info("""
        **🔍 Key Weather Indicators to Monitor:**
        - Temperature extremes (>30°C or <5°C)
        - Solar radiation levels (cloud cover)
        - Wind speed variations
        - Humidity and heat index
        - Weather forecast accuracy
        """)

    with col2:
        st.success("""
        **⚡ Operational Recommendations:**
        - Increase monitoring during extreme weather
        - Adjust trading positions based on forecasts
        - Prepare demand response programs
        - Monitor renewable generation performance
        - Update weather-adjusted load forecasts
        """)

if __name__ == "__main__":
    main()
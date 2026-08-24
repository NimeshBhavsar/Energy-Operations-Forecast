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
    page_title="Regional Analysis | Energy Ops Forecast",
    page_icon="🌍",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        margin: 0.5rem 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    .region-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #3498db;
        margin: 1rem 0;
    }

    .comparison-table {
        background: white;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
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

def create_region_comparison_chart(base_df, shock_df):
    """Create regional comparison visualization."""
    # Aggregate by region
    base_region = base_df.groupby('region').agg({
        'forecast_price': ['mean', 'max', 'min', 'std'],
        'forecast_demand': ['mean', 'max', 'min', 'std']
    }).reset_index()

    shock_region = shock_df.groupby('region').agg({
        'forecast_price': ['mean', 'max', 'min', 'std'],
        'forecast_demand': ['mean', 'max', 'min', 'std']
    }).reset_index()

    # Flatten column names
    base_region.columns = ['region', 'price_mean', 'price_max', 'price_min', 'price_std',
                          'demand_mean', 'demand_max', 'demand_min', 'demand_std']
    shock_region.columns = ['region', 'price_mean_shock', 'price_max_shock', 'price_min_shock', 'price_std_shock',
                           'demand_mean_shock', 'demand_max_shock', 'demand_min_shock', 'demand_std_shock']

    # Merge dataframes
    comparison = pd.merge(base_region, shock_region, on='region')

    # Create subplot
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            '💰 Average Price by Region',
            '⚡ Average Demand by Region',
            '📊 Price Volatility (Std Dev)',
            '📈 Demand Range (Max-Min)'
        ),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )

    # Price comparison
    fig.add_trace(
        go.Bar(
            x=comparison['region'],
            y=comparison['price_mean'],
            name='Baseline Price',
            marker_color='#3498db',
            text=[f'${x:.1f}' for x in comparison['price_mean']],
            textposition='auto'
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Bar(
            x=comparison['region'],
            y=comparison['price_mean_shock'],
            name='Shock Price',
            marker_color='#e74c3c',
            text=[f'${x:.1f}' for x in comparison['price_mean_shock']],
            textposition='auto'
        ),
        row=1, col=1
    )

    # Demand comparison
    fig.add_trace(
        go.Bar(
            x=comparison['region'],
            y=comparison['demand_mean'],
            name='Baseline Demand',
            marker_color='#2ecc71',
            text=[f'{x:.0f}' for x in comparison['demand_mean']],
            textposition='auto',
            showlegend=False
        ),
        row=1, col=2
    )

    fig.add_trace(
        go.Bar(
            x=comparison['region'],
            y=comparison['demand_mean_shock'],
            name='Shock Demand',
            marker_color='#f39c12',
            text=[f'{x:.0f}' for x in comparison['demand_mean_shock']],
            textposition='auto',
            showlegend=False
        ),
        row=1, col=2
    )

    # Price volatility
    fig.add_trace(
        go.Bar(
            x=comparison['region'],
            y=comparison['price_std'],
            name='Price Volatility',
            marker_color='#9b59b6',
            text=[f'${x:.1f}' for x in comparison['price_std']],
            textposition='auto',
            showlegend=False
        ),
        row=2, col=1
    )

    # Demand range
    demand_range = comparison['demand_max'] - comparison['demand_min']
    fig.add_trace(
        go.Bar(
            x=comparison['region'],
            y=demand_range,
            name='Demand Range',
            marker_color='#1abc9c',
            text=[f'{x:.0f}' for x in demand_range],
            textposition='auto',
            showlegend=False
        ),
        row=2, col=2
    )

    fig.update_layout(
        height=700,
        showlegend=True,
        template="plotly_white",
        title_text="🌍 Regional Performance Comparison",
        title_x=0.5
    )

    return fig

def create_regional_time_series(base_df, shock_df, selected_regions):
    """Create time series comparison for selected regions."""
    # Filter for selected regions
    base_filtered = base_df[base_df['region'].isin(selected_regions)]
    shock_filtered = shock_df[shock_df['region'].isin(selected_regions)]

    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('📈 Price Trends by Region', '⚡ Demand Trends by Region'),
        vertical_spacing=0.1
    )

    colors = px.colors.qualitative.Set1

    for i, region in enumerate(selected_regions):
        region_base = base_filtered[base_filtered['region'] == region]
        region_shock = shock_filtered[shock_filtered['region'] == region]

        color = colors[i % len(colors)]

        # Price chart
        fig.add_trace(
            go.Scatter(
                x=region_base['datetime'],
                y=region_base['forecast_price'],
                name=f'{region} - Baseline',
                line=dict(color=color, width=2),
                opacity=0.8
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=region_shock['datetime'],
                y=region_shock['forecast_price'],
                name=f'{region} - Shock',
                line=dict(color=color, width=2, dash='dash'),
                opacity=0.8
            ),
            row=1, col=1
        )

        # Demand chart
        fig.add_trace(
            go.Scatter(
                x=region_base['datetime'],
                y=region_base['forecast_demand'],
                name=f'{region} - Baseline',
                line=dict(color=color, width=2),
                opacity=0.8,
                showlegend=False
            ),
            row=2, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=region_shock['datetime'],
                y=region_shock['forecast_demand'],
                name=f'{region} - Shock',
                line=dict(color=color, width=2, dash='dash'),
                opacity=0.8,
                showlegend=False
            ),
            row=2, col=1
        )

    fig.update_layout(
        height=600,
        template="plotly_white",
        title_text="📊 Regional Time Series Analysis"
    )

    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_yaxes(title_text="Price ($/MWh)", row=1, col=1)
    fig.update_yaxes(title_text="Demand (MW)", row=2, col=1)

    return fig

def create_regional_heatmap(base_df, shock_df):
    """Create heatmap showing regional patterns by hour."""
    # Create hourly averages by region
    base_hourly = base_df.groupby(['region', base_df['datetime'].dt.hour]).agg({
        'forecast_price': 'mean',
        'forecast_demand': 'mean'
    }).reset_index()

    shock_hourly = shock_df.groupby(['region', shock_df['datetime'].dt.hour]).agg({
        'forecast_price': 'mean',
        'forecast_demand': 'mean'
    }).reset_index()

    # Pivot for heatmap
    price_matrix = base_hourly.pivot(index='region', columns='datetime', values='forecast_price')
    demand_matrix = base_hourly.pivot(index='region', columns='datetime', values='forecast_demand')

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('🌡️ Price Heatmap ($/MWh)', '🌡️ Demand Heatmap (MW)'),
        specs=[[{"type": "heatmap"}, {"type": "heatmap"}]]
    )

    fig.add_trace(
        go.Heatmap(
            z=price_matrix.values,
            x=[f"{h:02d}:00" for h in price_matrix.columns],
            y=price_matrix.index,
            colorscale='RdYlBu_r',
            name='Price',
            hovertemplate='Region: %{y}<br>Hour: %{x}<br>Price: $%{z:.2f}/MWh<extra></extra>'
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Heatmap(
            z=demand_matrix.values,
            x=[f"{h:02d}:00" for h in demand_matrix.columns],
            y=demand_matrix.index,
            colorscale='Viridis',
            name='Demand',
            hovertemplate='Region: %{y}<br>Hour: %{x}<br>Demand: %{z:.0f} MW<extra></extra>'
        ),
        row=1, col=2
    )

    fig.update_layout(
        height=400,
        template="plotly_white",
        title_text="🌡️ Regional Heat Patterns by Hour of Day"
    )

    return fig

# Main application
def main():
    st.markdown("# 🌍 Regional Analysis")
    st.markdown("## Comprehensive regional market comparison and trends")

    # Load data
    base_df, shock_df, delta_df = load_forecast_data()

    if base_df is None:
        return

    # Sidebar controls
    st.sidebar.markdown("## 🎛️ Analysis Controls")

    # Region selector
    all_regions = sorted(base_df["region"].unique())
    selected_regions = st.sidebar.multiselect(
        "Select Regions for Comparison",
        all_regions,
        default=all_regions[:3] if len(all_regions) >= 3 else all_regions,
        help="Choose regions to compare in time series analysis"
    )

    # Analysis type
    analysis_type = st.sidebar.selectbox(
        "Analysis Type",
        ["Overview", "Time Series", "Heatmap", "Statistical Summary"]
    )

    # Date range
    min_date = base_df["datetime"].min().date()
    max_date = base_df["datetime"].max().date()

    date_range = st.sidebar.date_input(
        "Date Range",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )

    # Filter data by date
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range

    mask = (
        (base_df["datetime"].dt.date >= start_date) &
        (base_df["datetime"].dt.date <= end_date)
    )

    base_filtered = base_df[mask]
    shock_filtered = shock_df[mask]
    delta_filtered = delta_df[
        (delta_df["datetime"].dt.date >= start_date) &
        (delta_df["datetime"].dt.date <= end_date)
    ]

    # Main content based on analysis type
    if analysis_type == "Overview":
        # Regional summary cards
        st.markdown("### 📊 Regional Performance Summary")

        # Calculate regional statistics
        regional_stats = []
        for region in all_regions:
            base_region = base_filtered[base_filtered['region'] == region]
            shock_region = shock_filtered[shock_filtered['region'] == region]
            delta_region = delta_filtered[delta_filtered['region'] == region]

            if len(base_region) > 0:
                stats = {
                    'region': region,
                    'avg_price_base': base_region['forecast_price'].mean(),
                    'avg_price_shock': shock_region['forecast_price'].mean(),
                    'avg_demand_base': base_region['forecast_demand'].mean(),
                    'avg_demand_shock': shock_region['forecast_demand'].mean(),
                    'price_volatility': base_region['forecast_price'].std(),
                    'max_price_delta': delta_region['delta_price'].max() if len(delta_region) > 0 else 0
                }
                regional_stats.append(stats)

        # Display regional cards
        for i, stats in enumerate(regional_stats):
            if i % 2 == 0:
                cols = st.columns(2)

            with cols[i % 2]:
                price_impact = ((stats['avg_price_shock'] / stats['avg_price_base'] - 1) * 100) if stats['avg_price_base'] > 0 else 0
                demand_impact = ((stats['avg_demand_shock'] / stats['avg_demand_base'] - 1) * 100) if stats['avg_demand_base'] > 0 else 0

                st.markdown(f"""
                <div class="region-card">
                    <h4>🌍 {stats['region']}</h4>
                    <div style="display: flex; justify-content: space-between; margin: 1rem 0;">
                        <div>
                            <strong>Avg Price:</strong> ${stats['avg_price_base']:.2f}/MWh<br>
                            <strong>Price Impact:</strong> <span style="color: {'red' if price_impact > 0 else 'green'}">{price_impact:+.1f}%</span><br>
                            <strong>Volatility:</strong> ${stats['price_volatility']:.2f}
                        </div>
                        <div>
                            <strong>Avg Demand:</strong> {stats['avg_demand_base']:,.0f} MW<br>
                            <strong>Demand Impact:</strong> <span style="color: {'red' if demand_impact > 0 else 'green'}">{demand_impact:+.1f}%</span><br>
                            <strong>Max Spike:</strong> ${stats['max_price_delta']:+.2f}/MWh
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Regional comparison chart
        st.markdown("### 📈 Regional Comparison Charts")
        fig_comparison = create_region_comparison_chart(base_filtered, shock_filtered)
        st.plotly_chart(fig_comparison, use_container_width=True)

    elif analysis_type == "Time Series":
        if selected_regions:
            st.markdown(f"### 📈 Time Series Analysis - {', '.join(selected_regions)}")
            fig_timeseries = create_regional_time_series(base_filtered, shock_filtered, selected_regions)
            st.plotly_chart(fig_timeseries, use_container_width=True)
        else:
            st.warning("Please select at least one region for time series analysis.")

    elif analysis_type == "Heatmap":
        st.markdown("### 🌡️ Regional Heat Patterns")
        fig_heatmap = create_regional_heatmap(base_filtered, shock_filtered)
        st.plotly_chart(fig_heatmap, use_container_width=True)

    elif analysis_type == "Statistical Summary":
        st.markdown("### 📊 Statistical Summary by Region")

        # Create comprehensive statistics table
        stats_list = []
        for region in all_regions:
            base_region = base_filtered[base_filtered['region'] == region]
            shock_region = shock_filtered[shock_filtered['region'] == region]

            if len(base_region) > 0:
                stats = {
                    'Region': region,
                    'Baseline Price (Mean)': f"${base_region['forecast_price'].mean():.2f}",
                    'Baseline Price (Std)': f"${base_region['forecast_price'].std():.2f}",
                    'Shock Price (Mean)': f"${shock_region['forecast_price'].mean():.2f}",
                    'Price Impact': f"{((shock_region['forecast_price'].mean() / base_region['forecast_price'].mean() - 1) * 100):+.1f}%",
                    'Baseline Demand (Mean)': f"{base_region['forecast_demand'].mean():,.0f} MW",
                    'Shock Demand (Mean)': f"{shock_region['forecast_demand'].mean():,.0f} MW",
                    'Demand Impact': f"{((shock_region['forecast_demand'].mean() / base_region['forecast_demand'].mean() - 1) * 100):+.1f}%"
                }
                stats_list.append(stats)

        stats_df = pd.DataFrame(stats_list)
        st.dataframe(stats_df, use_container_width=True)

        # Download button
        csv_data = stats_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Regional Statistics",
            data=csv_data,
            file_name=f"regional_statistics_{start_date}_to_{end_date}.csv",
            mime="text/csv"
        )

    # Additional insights
    st.markdown("### 💡 Regional Insights")

    # Find highest impact region
    regional_impact = []
    for region in all_regions:
        base_region = base_filtered[base_filtered['region'] == region]
        shock_region = shock_filtered[shock_filtered['region'] == region]

        if len(base_region) > 0 and len(shock_region) > 0:
            price_impact = (shock_region['forecast_price'].mean() / base_region['forecast_price'].mean() - 1) * 100
            regional_impact.append((region, price_impact))

    if regional_impact:
        regional_impact.sort(key=lambda x: abs(x[1]), reverse=True)
        highest_impact_region, highest_impact = regional_impact[0]

        col1, col2 = st.columns(2)

        with col1:
            st.info(f"""
            **🎯 Highest Impact Region:** {highest_impact_region}

            Price impact: {highest_impact:+.1f}%

            This region shows the most significant deviation from baseline forecasts.
            """)

        with col2:
            # Find most stable region
            most_stable = min(regional_impact, key=lambda x: abs(x[1]))
            stable_region, stable_impact = most_stable

            st.success(f"""
            **🎯 Most Stable Region:** {stable_region}

            Price impact: {stable_impact:+.1f}%

            This region maintains the most consistent pricing patterns.
            """)

if __name__ == "__main__":
    main()
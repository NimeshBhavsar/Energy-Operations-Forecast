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
    page_title="Forecast Scenarios | Energy Ops Forecast",
    page_icon="🎯",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .scenario-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(102,126,234,0.3);
    }

    .scenario-comparison {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #6c5ce7;
        margin: 1rem 0;
    }

    .what-if-control {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }

    .impact-metric {
        font-size: 1.8rem;
        font-weight: bold;
        color: #6c5ce7;
    }

    .scenario-selector {
        background: #f8f9ff;
        padding: 1rem;
        border-radius: 8px;
        border: 2px solid #667eea;
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

def create_scenario_comparison_chart(base_df, shock_df, delta_df, selected_region):
    """Create comprehensive scenario comparison."""
    # Filter for selected region
    base_region = base_df[base_df['region'] == selected_region]
    shock_region = shock_df[shock_df['region'] == selected_region]
    delta_region = delta_df[delta_df['region'] == selected_region]

    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=(
            '💰 Price Scenario Comparison',
            '⚡ Demand Scenario Comparison',
            '📊 Delta Impact Analysis'
        ),
        vertical_spacing=0.08,
        specs=[[{"secondary_y": False}], [{"secondary_y": False}], [{"secondary_y": True}]]
    )

    # Price comparison
    fig.add_trace(
        go.Scatter(
            x=base_region['datetime'],
            y=base_region['forecast_price'],
            name='Baseline Price',
            line=dict(color='#3498db', width=3),
            opacity=0.8
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=shock_region['datetime'],
            y=shock_region['forecast_price'],
            name='Shock Scenario Price',
            line=dict(color='#e74c3c', width=3),
            opacity=0.8
        ),
        row=1, col=1
    )

    # Add confidence bands
    price_upper = shock_region['forecast_price'] * 1.1
    price_lower = shock_region['forecast_price'] * 0.9

    fig.add_trace(
        go.Scatter(
            x=shock_region['datetime'],
            y=price_upper,
            fill=None,
            mode='lines',
            line_color='rgba(231,76,60,0)',
            showlegend=False
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=shock_region['datetime'],
            y=price_lower,
            fill='tonexty',
            mode='lines',
            line_color='rgba(231,76,60,0)',
            name='Shock Scenario Range (±10%)',
            fillcolor='rgba(231,76,60,0.2)'
        ),
        row=1, col=1
    )

    # Demand comparison
    fig.add_trace(
        go.Scatter(
            x=base_region['datetime'],
            y=base_region['forecast_demand'],
            name='Baseline Demand',
            line=dict(color='#27ae60', width=3),
            opacity=0.8,
            showlegend=False
        ),
        row=2, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=shock_region['datetime'],
            y=shock_region['forecast_demand'],
            name='Shock Scenario Demand',
            line=dict(color='#f39c12', width=3),
            opacity=0.8,
            showlegend=False
        ),
        row=2, col=1
    )

    # Delta analysis
    fig.add_trace(
        go.Scatter(
            x=delta_region['datetime'],
            y=delta_region['delta_price'],
            name='Price Delta',
            line=dict(color='#9b59b6', width=3),
            fill='tonexty'
        ),
        row=3, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=delta_region['datetime'],
            y=delta_region['delta_demand'] / 10,  # Scale for visibility
            name='Demand Delta (/10)',
            line=dict(color='#e67e22', width=2, dash='dash'),
            yaxis='y7'
        ),
        row=3, col=1
    )

    # Add zero line for deltas
    fig.add_hline(y=0, line_dash="solid", line_color="gray", opacity=0.5, row=3, col=1)

    fig.update_layout(
        height=800,
        template="plotly_white",
        title_text="🎯 Comprehensive Scenario Analysis Dashboard",
        title_x=0.5
    )

    fig.update_xaxes(title_text="Time", row=3, col=1)
    fig.update_yaxes(title_text="Price ($/MWh)", row=1, col=1)
    fig.update_yaxes(title_text="Demand (MW)", row=2, col=1)
    fig.update_yaxes(title_text="Price Delta ($/MWh)", row=3, col=1)
    fig.update_yaxes(title_text="Demand Delta (MW)", secondary_y=True, row=3, col=1)

    return fig

def create_what_if_scenario(base_df, selected_region, price_multiplier, demand_multiplier, volatility_multiplier):
    """Create custom what-if scenario."""
    base_region = base_df[base_df['region'] == selected_region].copy()

    # Apply user-defined multipliers
    base_region['what_if_price'] = base_region['forecast_price'] * price_multiplier
    base_region['what_if_demand'] = base_region['forecast_demand'] * demand_multiplier

    # Add volatility
    np.random.seed(42)
    volatility_factor = np.random.normal(1, (volatility_multiplier - 1) * 0.1, len(base_region))
    base_region['what_if_price'] *= volatility_factor

    # Calculate deltas
    base_region['price_delta'] = base_region['what_if_price'] - base_region['forecast_price']
    base_region['demand_delta'] = base_region['what_if_demand'] - base_region['forecast_demand']

    return base_region

def create_what_if_chart(what_if_data):
    """Create what-if scenario visualization."""
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            '💰 What-If Price Scenario',
            '⚡ What-If Demand Scenario',
            '📊 Price Impact Distribution',
            '💸 Financial Impact Timeline'
        ),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"type": "histogram"}, {"secondary_y": True}]]
    )

    # Price comparison
    fig.add_trace(
        go.Scatter(
            x=what_if_data['datetime'],
            y=what_if_data['forecast_price'],
            name='Original Forecast',
            line=dict(color='#3498db', width=2),
            opacity=0.7
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=what_if_data['datetime'],
            y=what_if_data['what_if_price'],
            name='What-If Scenario',
            line=dict(color='#e74c3c', width=3)
        ),
        row=1, col=1
    )

    # Demand comparison
    fig.add_trace(
        go.Scatter(
            x=what_if_data['datetime'],
            y=what_if_data['forecast_demand'],
            name='Original Demand',
            line=dict(color='#27ae60', width=2),
            opacity=0.7,
            showlegend=False
        ),
        row=1, col=2
    )

    fig.add_trace(
        go.Scatter(
            x=what_if_data['datetime'],
            y=what_if_data['what_if_demand'],
            name='What-If Demand',
            line=dict(color='#f39c12', width=3),
            showlegend=False
        ),
        row=1, col=2
    )

    # Price impact distribution
    fig.add_trace(
        go.Histogram(
            x=what_if_data['price_delta'],
            name='Price Impact Distribution',
            marker_color='#9b59b6',
            opacity=0.7,
            nbinsx=20
        ),
        row=2, col=1
    )

    # Financial impact timeline (assuming 100 MW portfolio)
    portfolio_mw = 100
    financial_impact = what_if_data['price_delta'] * portfolio_mw * 0.5  # 30-min intervals

    fig.add_trace(
        go.Scatter(
            x=what_if_data['datetime'],
            y=financial_impact.cumsum(),
            name='Cumulative Impact ($)',
            line=dict(color='#e67e22', width=3),
            fill='tonexty'
        ),
        row=2, col=2
    )

    fig.add_trace(
        go.Scatter(
            x=what_if_data['datetime'],
            y=financial_impact,
            name='Period Impact ($)',
            line=dict(color='#1abc9c', width=2, dash='dash'),
            yaxis='y8'
        ),
        row=2, col=2
    )

    fig.update_layout(
        height=600,
        template="plotly_white",
        title_text="🔮 What-If Scenario Analysis"
    )

    fig.update_xaxes(title_text="Time", row=1, col=1)
    fig.update_xaxes(title_text="Time", row=1, col=2)
    fig.update_xaxes(title_text="Price Delta ($/MWh)", row=2, col=1)
    fig.update_xaxes(title_text="Time", row=2, col=2)

    fig.update_yaxes(title_text="Price ($/MWh)", row=1, col=1)
    fig.update_yaxes(title_text="Demand (MW)", row=1, col=2)
    fig.update_yaxes(title_text="Frequency", row=2, col=1)
    fig.update_yaxes(title_text="Cumulative Impact ($)", row=2, col=2)
    fig.update_yaxes(title_text="Period Impact ($)", secondary_y=True, row=2, col=2)

    return fig

def create_scenario_risk_matrix(base_df, shock_df):
    """Create risk assessment matrix for scenarios."""
    scenarios_data = []

    for region in base_df['region'].unique():
        base_region = base_df[base_df['region'] == region]
        shock_region = shock_df[shock_df['region'] == region]

        # Calculate risk metrics
        price_volatility = shock_region['forecast_price'].std()
        price_impact = (shock_region['forecast_price'].mean() / base_region['forecast_price'].mean() - 1) * 100
        demand_impact = (shock_region['forecast_demand'].mean() / base_region['forecast_demand'].mean() - 1) * 100
        max_price_spike = shock_region['forecast_price'].max() - base_region['forecast_price'].max()

        scenarios_data.append({
            'region': region,
            'price_volatility': price_volatility,
            'price_impact': price_impact,
            'demand_impact': demand_impact,
            'max_price_spike': max_price_spike
        })

    scenarios_df = pd.DataFrame(scenarios_data)

    fig = go.Figure()

    # Create bubble chart
    fig.add_trace(
        go.Scatter(
            x=scenarios_df['price_impact'],
            y=scenarios_df['demand_impact'],
            mode='markers+text',
            marker=dict(
                size=scenarios_df['price_volatility'] * 2,
                color=scenarios_df['max_price_spike'],
                colorscale='Reds',
                showscale=True,
                colorbar=dict(title="Max Price Spike ($/MWh)"),
                opacity=0.7,
                line=dict(width=2, color='white')
            ),
            text=scenarios_df['region'],
            textposition='middle center',
            textfont=dict(size=12, color='white'),
            hovertemplate='<b>%{text}</b><br>' +
                         'Price Impact: %{x:.1f}%<br>' +
                         'Demand Impact: %{y:.1f}%<br>' +
                         'Volatility: $%{marker.size:.1f}/MWh<br>' +
                         'Max Spike: $%{marker.color:.2f}/MWh<extra></extra>',
            name='Regional Risk'
        )
    )

    # Add quadrant lines
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)

    # Add quadrant labels
    fig.add_annotation(x=15, y=15, text="High Risk<br>Both ↑", showarrow=False,
                      bgcolor="rgba(231,76,60,0.2)", bordercolor="red")
    fig.add_annotation(x=-15, y=15, text="Mixed Risk<br>Price ↓ Demand ↑", showarrow=False,
                      bgcolor="rgba(243,156,18,0.2)", bordercolor="orange")
    fig.add_annotation(x=15, y=-15, text="Mixed Risk<br>Price ↑ Demand ↓", showarrow=False,
                      bgcolor="rgba(243,156,18,0.2)", bordercolor="orange")
    fig.add_annotation(x=-15, y=-15, text="Low Risk<br>Both ↓", showarrow=False,
                      bgcolor="rgba(39,174,96,0.2)", bordercolor="green")

    fig.update_layout(
        title="🎯 Regional Risk Assessment Matrix",
        xaxis_title="Price Impact (%)",
        yaxis_title="Demand Impact (%)",
        template="plotly_white",
        height=500
    )

    return fig

def calculate_scenario_metrics(base_df, shock_df, delta_df, selected_region):
    """Calculate comprehensive scenario metrics."""
    base_region = base_df[base_df['region'] == selected_region]
    shock_region = shock_df[shock_df['region'] == selected_region]
    delta_region = delta_df[delta_df['region'] == selected_region]

    metrics = {}

    # Basic statistics
    metrics['base_avg_price'] = base_region['forecast_price'].mean()
    metrics['shock_avg_price'] = shock_region['forecast_price'].mean()
    metrics['base_avg_demand'] = base_region['forecast_demand'].mean()
    metrics['shock_avg_demand'] = shock_region['forecast_demand'].mean()

    # Impact calculations
    metrics['price_impact_pct'] = ((metrics['shock_avg_price'] / metrics['base_avg_price'] - 1) * 100)
    metrics['demand_impact_pct'] = ((metrics['shock_avg_demand'] / metrics['base_avg_demand'] - 1) * 100)

    # Volatility measures
    metrics['base_price_volatility'] = base_region['forecast_price'].std()
    metrics['shock_price_volatility'] = shock_region['forecast_price'].std()
    metrics['volatility_change'] = ((metrics['shock_price_volatility'] / metrics['base_price_volatility'] - 1) * 100)

    # Extreme values
    metrics['max_price_delta'] = delta_region['delta_price'].max()
    metrics['min_price_delta'] = delta_region['delta_price'].min()
    metrics['max_demand_delta'] = delta_region['delta_demand'].max()
    metrics['min_demand_delta'] = delta_region['delta_demand'].min()

    # Risk metrics
    metrics['var_95_base'] = np.percentile(base_region['forecast_price'], 95)
    metrics['var_95_shock'] = np.percentile(shock_region['forecast_price'], 95)
    metrics['var_impact'] = metrics['var_95_shock'] - metrics['var_95_base']

    # Financial impact (assuming 100 MW portfolio)
    portfolio_mw = 100
    hours = len(delta_region) * 0.5  # 30-min intervals
    metrics['total_cost_impact'] = delta_region['delta_price'].sum() * portfolio_mw * 0.5

    return metrics

# Main application
def main():
    st.markdown("# 🎯 Forecast Scenarios")
    st.markdown("## Interactive scenario analysis and what-if modeling")

    # Load data
    base_df, shock_df, delta_df = load_forecast_data()

    if base_df is None:
        return

    # Sidebar controls
    st.sidebar.markdown("## 🎛️ Scenario Controls")

    # Region selector
    regions = sorted(base_df["region"].unique())
    selected_region = st.sidebar.selectbox("🌍 Select Region", regions, index=0)

    # Analysis mode
    analysis_mode = st.sidebar.selectbox(
        "📊 Analysis Mode",
        ["Scenario Comparison", "What-If Analysis", "Risk Assessment", "Custom Scenario Builder"]
    )

    # Calculate scenario metrics
    metrics = calculate_scenario_metrics(base_df, shock_df, delta_df, selected_region)

    # Scenario overview
    st.markdown("### 📊 Scenario Performance Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="scenario-card">
            <h4>💰 Price Impact</h4>
            <div class="impact-metric">{metrics['price_impact_pct']:+.1f}%</div>
            <p>Baseline: ${metrics['base_avg_price']:.2f}/MWh<br>
            Shock: ${metrics['shock_avg_price']:.2f}/MWh</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="scenario-card">
            <h4>⚡ Demand Impact</h4>
            <div class="impact-metric">{metrics['demand_impact_pct']:+.1f}%</div>
            <p>Baseline: {metrics['base_avg_demand']:,.0f} MW<br>
            Shock: {metrics['shock_avg_demand']:,.0f} MW</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="scenario-card">
            <h4>📈 Volatility Change</h4>
            <div class="impact-metric">{metrics['volatility_change']:+.1f}%</div>
            <p>Baseline: ${metrics['base_price_volatility']:.2f}/MWh<br>
            Shock: ${metrics['shock_price_volatility']:.2f}/MWh</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="scenario-card">
            <h4>💸 Financial Impact</h4>
            <div class="impact-metric">${metrics['total_cost_impact']:,.0f}</div>
            <p>100 MW portfolio<br>
            Over forecast period</p>
        </div>
        """, unsafe_allow_html=True)

    # Main analysis content
    if analysis_mode == "Scenario Comparison":
        st.markdown("### 📊 Baseline vs Shock Scenario Comparison")

        # Detailed comparison chart
        fig_comparison = create_scenario_comparison_chart(base_df, shock_df, delta_df, selected_region)
        st.plotly_chart(fig_comparison, use_container_width=True)

        # Key insights
        st.markdown("### 💡 Scenario Insights")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"""
            <div class="scenario-comparison">
                <h4>🔍 Key Findings</h4>
                <p>• <strong>Maximum Price Increase:</strong> ${metrics['max_price_delta']:+.2f}/MWh<br>
                • <strong>Maximum Price Decrease:</strong> ${metrics['min_price_delta']:+.2f}/MWh<br>
                • <strong>Price Range:</strong> ${metrics['max_price_delta'] - metrics['min_price_delta']:.2f}/MWh<br>
                • <strong>95% VaR Impact:</strong> ${metrics['var_impact']:+.2f}/MWh</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="scenario-comparison">
                <h4>⚡ Demand Analysis</h4>
                <p>• <strong>Maximum Demand Increase:</strong> {metrics['max_demand_delta']:+,.0f} MW<br>
                • <strong>Maximum Demand Decrease:</strong> {metrics['min_demand_delta']:+,.0f} MW<br>
                • <strong>Demand Volatility:</strong> {metrics['demand_impact_pct']:+.1f}% vs baseline<br>
                • <strong>System Stress:</strong> {'High' if abs(metrics['demand_impact_pct']) > 15 else 'Medium' if abs(metrics['demand_impact_pct']) > 5 else 'Low'}</p>
            </div>
            """, unsafe_allow_html=True)

        # Statistical comparison table
        st.markdown("#### 📈 Statistical Summary")

        comparison_data = {
            'Metric': ['Average Price ($/MWh)', 'Max Price ($/MWh)', 'Min Price ($/MWh)', 'Price Std Dev ($/MWh)',
                      'Average Demand (MW)', 'Max Demand (MW)', 'Min Demand (MW)', 'Demand Std Dev (MW)'],
            'Baseline': [
                round(metrics['base_avg_price'], 2),
                round(base_df[base_df['region'] == selected_region]['forecast_price'].max(), 2),
                round(base_df[base_df['region'] == selected_region]['forecast_price'].min(), 2),
                round(metrics['base_price_volatility'], 2),
                int(metrics['base_avg_demand']),
                int(base_df[base_df['region'] == selected_region]['forecast_demand'].max()),
                int(base_df[base_df['region'] == selected_region]['forecast_demand'].min()),
                int(base_df[base_df['region'] == selected_region]['forecast_demand'].std())
            ],
            'Shock Scenario': [
                round(metrics['shock_avg_price'], 2),
                round(shock_df[shock_df['region'] == selected_region]['forecast_price'].max(), 2),
                round(shock_df[shock_df['region'] == selected_region]['forecast_price'].min(), 2),
                round(metrics['shock_price_volatility'], 2),
                int(metrics['shock_avg_demand']),
                int(shock_df[shock_df['region'] == selected_region]['forecast_demand'].max()),
                int(shock_df[shock_df['region'] == selected_region]['forecast_demand'].min()),
                int(shock_df[shock_df['region'] == selected_region]['forecast_demand'].std())
            ],
            'Impact (%)': [
                round(metrics['price_impact_pct'], 1),
                round(((shock_df[shock_df['region'] == selected_region]['forecast_price'].max() / base_df[base_df['region'] == selected_region]['forecast_price'].max() - 1) * 100), 1),
                round(((shock_df[shock_df['region'] == selected_region]['forecast_price'].min() / base_df[base_df['region'] == selected_region]['forecast_price'].min() - 1) * 100), 1),
                round(metrics['volatility_change'], 1),
                round(metrics['demand_impact_pct'], 1),
                round(((shock_df[shock_df['region'] == selected_region]['forecast_demand'].max() / base_df[base_df['region'] == selected_region]['forecast_demand'].max() - 1) * 100), 1),
                round(((shock_df[shock_df['region'] == selected_region]['forecast_demand'].min() / base_df[base_df['region'] == selected_region]['forecast_demand'].min() - 1) * 100), 1),
                round(((shock_df[shock_df['region'] == selected_region]['forecast_demand'].std() / base_df[base_df['region'] == selected_region]['forecast_demand'].std() - 1) * 100), 1)
            ]
        }

        st.dataframe(pd.DataFrame(comparison_data), use_container_width=True)

    elif analysis_mode == "What-If Analysis":
        st.markdown("### 🔮 What-If Scenario Builder")

        # What-if controls
        st.markdown("#### 🎛️ Scenario Parameters")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown('<div class="what-if-control">', unsafe_allow_html=True)
            price_multiplier = st.slider(
                "💰 Price Multiplier",
                min_value=0.5,
                max_value=2.0,
                value=1.0,
                step=0.1,
                help="Multiply baseline prices by this factor"
            )
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="what-if-control">', unsafe_allow_html=True)
            demand_multiplier = st.slider(
                "⚡ Demand Multiplier",
                min_value=0.8,
                max_value=1.5,
                value=1.0,
                step=0.05,
                help="Multiply baseline demand by this factor"
            )
            st.markdown('</div>', unsafe_allow_html=True)

        with col3:
            st.markdown('<div class="what-if-control">', unsafe_allow_html=True)
            volatility_multiplier = st.slider(
                "📊 Volatility Multiplier",
                min_value=0.5,
                max_value=3.0,
                value=1.0,
                step=0.1,
                help="Increase price volatility by this factor"
            )
            st.markdown('</div>', unsafe_allow_html=True)

        # Generate what-if scenario
        what_if_data = create_what_if_scenario(
            base_df, selected_region, price_multiplier, demand_multiplier, volatility_multiplier
        )

        # What-if visualization
        fig_what_if = create_what_if_chart(what_if_data)
        st.plotly_chart(fig_what_if, use_container_width=True)

        # What-if impact summary
        st.markdown("#### 📊 What-If Impact Summary")

        col1, col2 = st.columns(2)

        with col1:
            avg_price_impact = what_if_data['price_delta'].mean()
            max_price_impact = what_if_data['price_delta'].max()
            min_price_impact = what_if_data['price_delta'].min()

            st.info(f"""
            **💰 Price Impact Analysis:**
            - Average Impact: {avg_price_impact:+.2f} $/MWh
            - Maximum Impact: {max_price_impact:+.2f} $/MWh
            - Minimum Impact: {min_price_impact:+.2f} $/MWh
            - Total Range: {max_price_impact - min_price_impact:.2f} $/MWh
            """)

        with col2:
            total_financial_impact = what_if_data['price_delta'].sum() * 100 * 0.5  # 100 MW portfolio
            avg_hourly_impact = total_financial_impact / (len(what_if_data) * 0.5)

            st.warning(f"""
            **💸 Financial Impact (100 MW Portfolio):**
            - Total Impact: ${total_financial_impact:,.0f}
            - Average Hourly: ${avg_hourly_impact:,.0f}/hour
            - Daily Average: ${avg_hourly_impact * 24:,.0f}/day
            - Impact per MWh: ${what_if_data['price_delta'].mean():.2f}/MWh
            """)

    elif analysis_mode == "Risk Assessment":
        st.markdown("### ⚠️ Risk Assessment Matrix")

        # Risk matrix
        fig_risk = create_scenario_risk_matrix(base_df, shock_df)
        st.plotly_chart(fig_risk, use_container_width=True)

        # Risk categories
        st.markdown("#### 🎯 Risk Category Analysis")

        col1, col2, col3 = st.columns(3)

        with col1:
            high_risk_regions = []
            medium_risk_regions = []
            low_risk_regions = []

            for region in regions:
                region_metrics = calculate_scenario_metrics(base_df, shock_df, delta_df, region)
                risk_score = abs(region_metrics['price_impact_pct']) + abs(region_metrics['demand_impact_pct'])

                if risk_score > 30:
                    high_risk_regions.append(region)
                elif risk_score > 15:
                    medium_risk_regions.append(region)
                else:
                    low_risk_regions.append(region)

            st.error(f"""
            **🔴 High Risk Regions ({len(high_risk_regions)}):**
            {', '.join(high_risk_regions) if high_risk_regions else 'None'}

            *Combined price and demand impact > 30%*
            """)

        with col2:
            st.warning(f"""
            **🟡 Medium Risk Regions ({len(medium_risk_regions)}):**
            {', '.join(medium_risk_regions) if medium_risk_regions else 'None'}

            *Combined impact 15-30%*
            """)

        with col3:
            st.success(f"""
            **🟢 Low Risk Regions ({len(low_risk_regions)}):**
            {', '.join(low_risk_regions) if low_risk_regions else 'None'}

            *Combined impact < 15%*
            """)

    elif analysis_mode == "Custom Scenario Builder":
        st.markdown("### 🛠️ Custom Scenario Builder")

        # Scenario building interface
        st.markdown("#### ⚙️ Build Your Custom Scenario")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**📊 Economic Factors**")
            economic_stress = st.selectbox("Economic Stress Level", ["Low", "Medium", "High", "Crisis"])
            fuel_price_change = st.slider("Fuel Price Change (%)", -50, 100, 0)
            carbon_price = st.slider("Carbon Price ($/tonne)", 0, 200, 50)

        with col2:
            st.markdown("**🌤️ Environmental Factors**")
            weather_severity = st.selectbox("Weather Severity", ["Normal", "Mild", "Severe", "Extreme"])
            renewable_availability = st.slider("Renewable Availability (%)", 0, 150, 100)
            demand_growth = st.slider("Demand Growth (%)", -20, 50, 0)

        # Calculate custom scenario impact
        economic_multiplier = {"Low": 1.0, "Medium": 1.2, "High": 1.5, "Crisis": 2.0}[economic_stress]
        weather_multiplier = {"Normal": 1.0, "Mild": 1.1, "Severe": 1.3, "Extreme": 1.6}[weather_severity]
        fuel_impact = fuel_price_change / 100
        renewable_impact = (renewable_availability - 100) / 100

        custom_price_multiplier = economic_multiplier * weather_multiplier * (1 + fuel_impact) * (1 - renewable_impact * 0.3)
        custom_demand_multiplier = (1 + demand_growth / 100) * weather_multiplier

        # Generate custom scenario
        custom_scenario = create_what_if_scenario(
            base_df, selected_region, custom_price_multiplier, custom_demand_multiplier, weather_multiplier
        )

        # Display custom scenario results
        st.markdown("#### 📊 Custom Scenario Results")

        custom_metrics = {
            'price_impact': (custom_scenario['what_if_price'].mean() / custom_scenario['forecast_price'].mean() - 1) * 100,
            'demand_impact': (custom_scenario['what_if_demand'].mean() / custom_scenario['forecast_demand'].mean() - 1) * 100,
            'max_price_delta': custom_scenario['price_delta'].max(),
            'financial_impact': custom_scenario['price_delta'].sum() * 100 * 0.5
        }

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Price Impact", f"{custom_metrics['price_impact']:+.1f}%")
            st.metric("Demand Impact", f"{custom_metrics['demand_impact']:+.1f}%")

        with col2:
            st.metric("Max Price Spike", f"${custom_metrics['max_price_delta']:+.2f}/MWh")
            st.metric("Financial Impact", f"${custom_metrics['financial_impact']:,.0f}")

        with col3:
            risk_level = "🔴 HIGH" if abs(custom_metrics['price_impact']) > 30 else "🟡 MEDIUM" if abs(custom_metrics['price_impact']) > 15 else "🟢 LOW"
            st.markdown(f"""
            **Risk Assessment:**
            {risk_level}

            **Scenario Confidence:**
            {"High" if weather_severity != "Extreme" and economic_stress != "Crisis" else "Medium"}
            """)

        # Custom scenario chart
        fig_custom = create_what_if_chart(custom_scenario)
        st.plotly_chart(fig_custom, use_container_width=True)

    # Export functionality
    st.markdown("### 📥 Export Scenario Analysis")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 Export Scenario Data", use_container_width=True):
            # Prepare export data
            export_data = base_df[base_df['region'] == selected_region].copy()
            export_data = export_data.merge(
                shock_df[shock_df['region'] == selected_region][['datetime', 'forecast_price', 'forecast_demand']],
                on='datetime',
                suffixes=('_baseline', '_shock')
            )
            export_data = export_data.merge(
                delta_df[delta_df['region'] == selected_region],
                on=['datetime', 'region']
            )

            csv_data = export_data.to_csv(index=False)
            st.download_button(
                "💾 Download CSV",
                csv_data,
                f"scenario_analysis_{selected_region}.csv",
                "text/csv"
            )

    with col2:
        if st.button("📈 Export Metrics Summary", use_container_width=True):
            metrics_summary = pd.DataFrame([metrics]).T
            metrics_summary.columns = ['Value']

            summary_csv = metrics_summary.to_csv()
            st.download_button(
                "💾 Download Metrics",
                summary_csv,
                f"scenario_metrics_{selected_region}.csv",
                "text/csv"
            )

    with col3:
        if st.button("🎯 Generate Report", use_container_width=True):
            st.info("📋 Comprehensive scenario report generation coming soon!")

if __name__ == "__main__":
    main()
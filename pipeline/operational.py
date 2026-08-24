"""
Energy Operational Forecasting Pipeline
=====================================

This module contains the core automated operational forecasting functionality.
Processes fact_energy_market.parquet and generates three forecast CSV outputs.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from pathlib import Path
from typing import Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def automated_operational_forecast(
    input_file: str = "fact_energy_market.parquet",
    output_dir: str = "data"
) -> Tuple[bool, str]:
    """
    Main automated operational forecasting function.

    Args:
        input_file: Path to the input parquet file
        output_dir: Directory to save output CSV files

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        logger.info("Starting automated operational forecast...")

        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(exist_ok=True)

        # Load data
        logger.info(f"Loading data from {input_file}")
        df = pd.read_parquet(input_file)

        # Ensure datetime column
        if 'datetime' not in df.columns:
            # Try to find datetime-like column
            date_cols = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
            if date_cols:
                df = df.rename(columns={date_cols[0]: 'datetime'})
            else:
                raise ValueError("No datetime column found in input data")

        # Convert datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(df['datetime']):
            df['datetime'] = pd.to_datetime(df['datetime'])

        # Generate forecasts
        baseline_forecast = _generate_baseline_forecast(df)
        scenario_shock_forecast = _generate_scenario_shock_forecast(baseline_forecast)
        scenario_delta_forecast = _generate_scenario_delta_forecast(baseline_forecast, scenario_shock_forecast)

        # Save outputs
        output_files = [
            (baseline_forecast, f"{output_dir}/forecast_baseline.csv"),
            (scenario_shock_forecast, f"{output_dir}/forecast_scenario_shock.csv"),
            (scenario_delta_forecast, f"{output_dir}/forecast_scenario_delta.csv")
        ]

        for forecast_df, filepath in output_files:
            forecast_df.to_csv(filepath, index=False)
            logger.info(f"Saved {filepath}")

        logger.info("Automated operational forecast completed successfully")
        return True, "Forecast generation completed successfully"

    except Exception as e:
        error_msg = f"Error in automated_operational_forecast: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def _generate_baseline_forecast(df: pd.DataFrame) -> pd.DataFrame:
    """Generate baseline forecast using historical patterns and trends."""
    logger.info("Generating baseline forecast...")

    # Create forecast period (next 7 days, 30-min intervals)
    start_forecast = df['datetime'].max() + timedelta(minutes=30)
    periods = 7 * 24 * 2  # 7 days * 24 hours * 2 (30-min intervals)

    forecast_dates = pd.date_range(
        start=start_forecast,
        periods=periods,
        freq='30min'
    )

    # Get unique regions
    regions = df['region'].unique() if 'region' in df.columns else ['NSW1']

    forecast_rows = []

    for region in regions:
        region_data = df[df['region'] == region] if 'region' in df.columns else df

        for dt in forecast_dates:
            # Extract time features
            hour = dt.hour
            day_of_week = dt.dayofweek
            is_weekend = 1 if day_of_week >= 5 else 0

            # Determine peak period
            if 7 <= hour <= 9 or 17 <= hour <= 21:
                peak_period = 'peak'
            elif 22 <= hour <= 23 or 6 <= hour <= 6:
                peak_period = 'shoulder'
            else:
                peak_period = 'other'

            # Price forecasting with seasonal patterns
            base_price = _forecast_price(region_data, hour, day_of_week, is_weekend)

            # Demand forecasting with load patterns
            base_demand = _forecast_demand(region_data, hour, day_of_week, is_weekend)

            # Create forecast row
            row = {
                'datetime': dt,
                'hour': hour,
                'day_of_week': day_of_week,
                'is_weekend': is_weekend,
                'peak_period': peak_period,
                'temp_c': None,
                'rh_pct': None,
                'rain_mm': None,
                'sunshine_sec': None,
                'shortwave_wm2': None,
                'wind_speed_ms': None,
                'temp_bin': None,
                'spike_flag': None,
                'compound_highTemp_lowSolar_peakHour': None,
                'RRP_lag_1h': None,
                'RRP_lag_12h': None,
                'RRP_lag_24h': None,
                'TOTALDEMAND_lag_1h': None,
                'TOTALDEMAND_lag_12h': None,
                'TOTALDEMAND_lag_24h': None,
                'RRP_rolling_3h': None,
                'RRP_rolling_6h': None,
                'RRP_rolling_24h': None,
                'TOTALDEMAND_rolling_3h': None,
                'TOTALDEMAND_rolling_6h': None,
                'TOTALDEMAND_rolling_24h': None,
                'region': region,
                'forecast_price': base_price,
                'forecast_demand': base_demand
            }

            forecast_rows.append(row)

    return pd.DataFrame(forecast_rows)


def _generate_scenario_shock_forecast(baseline_df: pd.DataFrame) -> pd.DataFrame:
    """Generate shock scenario forecast with extreme weather/market conditions."""
    logger.info("Generating scenario shock forecast...")

    shock_df = baseline_df.copy()

    # Apply shock multipliers
    shock_df['forecast_price'] = shock_df['forecast_price'] * np.random.normal(1.3, 0.1, len(shock_df))
    shock_df['forecast_demand'] = shock_df['forecast_demand'] * np.random.normal(1.15, 0.05, len(shock_df))

    # Add extreme price spikes during peak periods
    peak_mask = shock_df['peak_period'] == 'peak'
    shock_df.loc[peak_mask, 'forecast_price'] *= np.random.uniform(1.5, 2.5, peak_mask.sum())

    # Ensure non-negative values
    shock_df['forecast_price'] = shock_df['forecast_price'].clip(lower=0)
    shock_df['forecast_demand'] = shock_df['forecast_demand'].clip(lower=0)

    return shock_df


def _generate_scenario_delta_forecast(baseline_df: pd.DataFrame, shock_df: pd.DataFrame) -> pd.DataFrame:
    """Generate delta forecast (shock - baseline)."""
    logger.info("Generating scenario delta forecast...")

    delta_df = baseline_df[['datetime', 'region']].copy()
    delta_df['delta_price'] = shock_df['forecast_price'] - baseline_df['forecast_price']
    delta_df['delta_demand'] = shock_df['forecast_demand'] - baseline_df['forecast_demand']

    return delta_df


def _forecast_price(region_data: pd.DataFrame, hour: int, day_of_week: int, is_weekend: int) -> float:
    """Forecast price based on historical patterns."""
    # Base price from historical data
    if len(region_data) > 0 and 'forecast_price' in region_data.columns:
        base_price = region_data['forecast_price'].mean()
    else:
        base_price = 50.0  # Default base price

    # Hour-of-day adjustment
    if 7 <= hour <= 9 or 17 <= hour <= 21:  # Peak hours
        hour_multiplier = 1.4
    elif 22 <= hour <= 6:  # Off-peak
        hour_multiplier = 0.7
    else:  # Shoulder
        hour_multiplier = 1.0

    # Weekend adjustment
    weekend_multiplier = 0.8 if is_weekend else 1.0

    # Add some random variation
    noise = np.random.normal(1.0, 0.1)

    return max(0, base_price * hour_multiplier * weekend_multiplier * noise)


def _forecast_demand(region_data: pd.DataFrame, hour: int, day_of_week: int, is_weekend: int) -> float:
    """Forecast demand based on historical patterns."""
    # Base demand from historical data
    if len(region_data) > 0 and 'forecast_demand' in region_data.columns:
        base_demand = region_data['forecast_demand'].mean()
    else:
        base_demand = 7000.0  # Default base demand

    # Hour-of-day adjustment
    if 7 <= hour <= 9 or 17 <= hour <= 21:  # Peak hours
        hour_multiplier = 1.3
    elif 1 <= hour <= 5:  # Low demand
        hour_multiplier = 0.6
    else:
        hour_multiplier = 1.0

    # Weekend adjustment
    weekend_multiplier = 0.85 if is_weekend else 1.0

    # Add some random variation
    noise = np.random.normal(1.0, 0.05)

    return max(0, base_demand * hour_multiplier * weekend_multiplier * noise)


if __name__ == "__main__":
    # Test the function
    success, message = automated_operational_forecast()
    print(f"Success: {success}")
    print(f"Message: {message}")
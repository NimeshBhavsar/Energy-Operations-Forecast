#!/usr/bin/env python3
"""
Energy Ops Forecast - Main Automation Entry Point
===============================================

This script serves as the main entry point for automated operational forecasting.
It calls the automated_operational_forecast function and handles logging/notifications.

Usage:
    python run_forecast.py                    # Use default paths
    python run_forecast.py --input custom.parquet --output /path/to/output

For Power BI users: This is the only script you need to run.
Schedule this script to run every Monday at 06:00 using cron or Airflow.
"""

import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

from pipeline.operational import automated_operational_forecast


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Run automated operational energy forecasting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_forecast.py
  python run_forecast.py --input custom_data.parquet
  python run_forecast.py --output /custom/output/path
        """
    )

    parser.add_argument(
        '--input', '-i',
        default='fact_energy_market.parquet',
        help='Input parquet file path (default: fact_energy_market.parquet)'
    )

    parser.add_argument(
        '--output', '-o',
        default='data',
        help='Output directory for CSV files (default: data)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run in dry-run mode (validate inputs only)'
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('forecast_automation.log')
        ]
    )

    logger = logging.getLogger(__name__)

    # Log execution start
    logger.info("=" * 60)
    logger.info("ENERGY OPS FORECAST - AUTOMATION RUN")
    logger.info("=" * 60)
    logger.info(f"Execution started at: {datetime.now()}")
    logger.info(f"Input file: {args.input}")
    logger.info(f"Output directory: {args.output}")
    logger.info(f"Dry run: {args.dry_run}")

    try:
        # Validate input file exists
        if not Path(args.input).exists():
            raise FileNotFoundError(f"Input file not found: {args.input}")

        # Dry run mode
        if args.dry_run:
            logger.info("DRY RUN MODE: Validation completed successfully")
            logger.info("All inputs are valid. Ready for actual execution.")
            return 0

        # Run the forecast
        logger.info("Starting automated operational forecast...")
        success, message = automated_operational_forecast(
            input_file=args.input,
            output_dir=args.output
        )

        if success:
            logger.info("✅ FORECAST COMPLETED SUCCESSFULLY")
            logger.info(f"Message: {message}")
            logger.info(f"Output files saved to: {args.output}/")
            logger.info("📊 CSV files are ready for Power BI consumption")

            # List generated files
            output_path = Path(args.output)
            csv_files = list(output_path.glob("forecast_*.csv"))
            if csv_files:
                logger.info("Generated files:")
                for file in csv_files:
                    file_size = file.stat().st_size / 1024  # KB
                    logger.info(f"  - {file.name} ({file_size:.1f} KB)")

            return 0

        else:
            logger.error("❌ FORECAST FAILED")
            logger.error(f"Error: {message}")
            return 1

    except Exception as e:
        logger.error("❌ CRITICAL ERROR")
        logger.error(f"Unexpected error: {str(e)}")
        logger.exception("Full traceback:")
        return 1

    finally:
        logger.info(f"Execution completed at: {datetime.now()}")
        logger.info("=" * 60)


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
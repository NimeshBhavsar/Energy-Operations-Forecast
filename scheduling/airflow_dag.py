"""
Energy Ops Forecast - Airflow DAG
==================================

This DAG runs the energy operational forecasting pipeline every Monday at 6 AM.
It includes data validation, forecast execution, and notification tasks.

Requirements:
- Apache Airflow 2.0+
- Energy ops forecast project deployed in Airflow environment
- Email configuration for notifications (optional)

Installation:
1. Copy this file to your Airflow DAGs folder
2. Update the PROJECT_PATH variable below
3. Configure email settings if needed
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.operators.email import EmailOperator
from airflow.models import Variable
import os
import logging

# Configuration
PROJECT_PATH = Variable.get("energy_forecast_project_path", "/opt/airflow/projects/energy-ops-forecast")
NOTIFICATION_EMAIL = Variable.get("energy_forecast_email", "admin@company.com")

# DAG configuration
default_args = {
    'owner': 'energy-ops-team',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=15),
    'email': [NOTIFICATION_EMAIL]
}

dag = DAG(
    'energy_ops_forecast',
    default_args=default_args,
    description='Weekly energy operational forecasting pipeline',
    schedule_interval='0 6 * * 1',  # Every Monday at 6 AM
    catchup=False,
    max_active_runs=1,
    tags=['energy', 'forecasting', 'operations']
)


def validate_input_data(**context):
    """Validate that input data exists and is recent."""
    import pandas as pd
    from pathlib import Path

    input_file = Path(PROJECT_PATH) / "fact_energy_market.parquet"

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Check file age (should be updated within last 7 days)
    file_age = datetime.now() - datetime.fromtimestamp(input_file.stat().st_mtime)
    if file_age.days > 7:
        logging.warning(f"Input file is {file_age.days} days old. Consider updating.")

    # Basic data validation
    df = pd.read_parquet(input_file)
    if len(df) == 0:
        raise ValueError("Input file is empty")

    logging.info(f"Input validation passed. Records: {len(df)}")
    return True


def check_forecast_outputs(**context):
    """Verify that all expected output files were generated."""
    from pathlib import Path

    output_dir = Path(PROJECT_PATH) / "data"
    expected_files = [
        "forecast_baseline.csv",
        "forecast_scenario_shock.csv",
        "forecast_scenario_delta.csv"
    ]

    missing_files = []
    for filename in expected_files:
        filepath = output_dir / filename
        if not filepath.exists():
            missing_files.append(filename)

    if missing_files:
        raise FileNotFoundError(f"Missing output files: {missing_files}")

    # Check file sizes (should not be empty)
    for filename in expected_files:
        filepath = output_dir / filename
        if filepath.stat().st_size == 0:
            raise ValueError(f"Output file is empty: {filename}")

    logging.info("All forecast outputs validated successfully")
    return True


# Task 1: Validate input data
validate_input = PythonOperator(
    task_id='validate_input_data',
    python_callable=validate_input_data,
    dag=dag
)

# Task 2: Run forecast
run_forecast = BashOperator(
    task_id='run_forecast',
    bash_command=f"""
    cd {PROJECT_PATH}
    python run_forecast.py --verbose
    """,
    dag=dag
)

# Task 3: Validate outputs
validate_outputs = PythonOperator(
    task_id='validate_forecast_outputs',
    python_callable=check_forecast_outputs,
    dag=dag
)

# Task 4: Success notification (optional)
success_notification = EmailOperator(
    task_id='send_success_notification',
    to=[NOTIFICATION_EMAIL],
    subject='Energy Ops Forecast - Success',
    html_content="""
    <h3>Energy Operational Forecast Completed Successfully</h3>
    <p><strong>Execution Date:</strong> {{ ds }}</p>
    <p><strong>DAG:</strong> {{ dag.dag_id }}</p>
    <p><strong>Status:</strong> ✅ Success</p>
    <p>All forecast files have been generated and are ready for consumption.</p>

    <h4>Generated Files:</h4>
    <ul>
        <li>forecast_baseline.csv</li>
        <li>forecast_scenario_shock.csv</li>
        <li>forecast_scenario_delta.csv</li>
    </ul>

    <p>These files are available in the data/ directory and ready for Power BI refresh.</p>
    """,
    dag=dag,
    trigger_rule='all_success'
)

# Task 5: Cleanup old files (optional)
cleanup_old_files = BashOperator(
    task_id='cleanup_old_files',
    bash_command=f"""
    cd {PROJECT_PATH}
    # Remove log files older than 30 days
    find logs/ -name "*.log" -type f -mtime +30 -delete 2>/dev/null || true
    # Archive old forecast files (optional)
    # mkdir -p archive/$(date +%Y%m%d)
    # cp data/forecast_*.csv archive/$(date +%Y%m%d)/ 2>/dev/null || true
    echo "Cleanup completed"
    """,
    dag=dag
)

# Define task dependencies
validate_input >> run_forecast >> validate_outputs >> [success_notification, cleanup_old_files]

# Optional: Add failure handling
def failure_callback(context):
    """Handle DAG failures with custom notifications."""
    logging.error(f"DAG {context['dag'].dag_id} failed on {context['ds']}")
    # Add custom failure handling here (Slack, Teams, etc.)


# Add failure callback to DAG
dag.on_failure_callback = failure_callback
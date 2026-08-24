#!/usr/bin/env python3
"""
Automated Email Forecast Script
==============================

This script runs forecast generation and sends email automatically.
Designed to be called by cron without any UI interaction.
"""

import sys
import os
from pathlib import Path
import smtplib
from email.message import EmailMessage
from datetime import datetime
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from pipeline.operational import automated_operational_forecast

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / 'logs' / 'automated_email.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_secret(key, default=None):
    """Get secret from environment variables (for cron)."""
    return os.getenv(key, default)

def get_smtp_config():
    """Get SMTP configuration from environment variables."""
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
            return False, "SMTP configuration missing. Please set SMTP_HOST, SMTP_USER, and SMTP_PASS environment variables."

        # Create email message
        msg = EmailMessage()
        msg['Subject'] = f'⚡ Weekly Energy Ops Forecast - {datetime.now().strftime("%Y-%m-%d")}'
        msg['From'] = smtp_user
        msg['To'] = recipient_email

        # Email body
        body = f"""
Energy Operations Forecast - Weekly Automated Report
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

📊 This automated report contains the latest 7-day energy forecast outputs:

Attachments:
• forecast_baseline.csv - Base case operational forecast
• forecast_scenario_shock.csv - Extreme scenario forecast
• forecast_scenario_delta.csv - Impact analysis (shock - baseline)

Files are ready for Power BI consumption and further analysis.

---
🤖 Generated automatically by Energy Ops Forecast System
Next report: Next Monday at 11:00 AM
"""
        msg.set_content(body)

        # Attach CSV files
        for file_path in csv_files:
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                    file_name = os.path.basename(file_path)
                    msg.add_attachment(file_data, maintype='text', subtype='csv', filename=file_name)
                logger.info(f"Attached {file_name} ({len(file_data)} bytes)")

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

def main():
    """Main automation function."""
    logger.info("🚀 Starting weekly automated email forecast")

    try:
        # Set paths relative to project root
        input_file = str(project_root / "fact_energy_market.parquet")
        output_dir = str(project_root / "data")

        # Run forecast
        logger.info("📊 Generating forecast...")
        success, message = automated_operational_forecast(
            input_file=input_file,
            output_dir=output_dir
        )

        if not success:
            logger.error(f"❌ Forecast failed: {message}")
            return 1

        logger.info(f"✅ Forecast generated: {message}")

        # Send email
        csv_files = [
            str(project_root / "data" / "forecast_baseline.csv"),
            str(project_root / "data" / "forecast_scenario_shock.csv"),
            str(project_root / "data" / "forecast_scenario_delta.csv")
        ]

        logger.info("📧 Sending email...")
        email_success, email_message = send_forecast_email(csv_files)

        if email_success:
            logger.info(f"✅ {email_message}")
            logger.info("🎉 Weekly automated forecast completed successfully")
            return 0
        else:
            logger.error(f"❌ Email failed: {email_message}")
            return 1

    except Exception as e:
        logger.error(f"❌ Critical error: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
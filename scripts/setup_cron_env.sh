#!/bin/bash
# Cron Environment Setup for Energy Ops Forecast
# ============================================
# This script sets up environment variables for cron automation

# Set project root directory (resolved relative to this script, no hardcoded username)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Initialize pyenv for cron environment
export PATH="$HOME/.pyenv/bin:$HOME/.pyenv/shims:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
export PYENV_ROOT="$HOME/.pyenv"

# Initialize pyenv
if command -v pyenv 1>/dev/null 2>&1; then
    eval "$(pyenv init -)"
fi

# SMTP Configuration (from your Streamlit secrets)
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="nimeshbhavsar006@gmail.com"
# Set SMTP_PASS in your shell/secrets before running this script, e.g.:
#   export SMTP_PASS="your-16-char-gmail-app-password"
export SMTP_PASS="${SMTP_PASS:?SMTP_PASS is not set. Export your Gmail app password before running this script.}"
export SMTP_USE_TLS="true"

# Change to project directory
cd "$PROJECT_ROOT"

# Create logs directory if it doesn't exist
mkdir -p logs

# Run the automated email forecast
python3 scripts/automated_email_forecast.py

# Log completion
echo "$(date): Weekly automated forecast completed" >> logs/cron_execution.log
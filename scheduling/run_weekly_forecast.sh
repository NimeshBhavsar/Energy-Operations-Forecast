#!/bin/bash
# Energy Ops Forecast - Weekly Execution Script
# =============================================
#
# This script is called by cron every Monday at 6 AM.
# It runs the forecast and logs the results.

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$PROJECT_DIR/logs"
VENV_PATH="$PROJECT_DIR/venv"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
LOG_FILE="$LOG_DIR/forecast_$TIMESTAMP.log"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Start execution
log "=========================================="
log "Energy Ops Forecast - Weekly Execution"
log "=========================================="
log "Project directory: $PROJECT_DIR"
log "Log file: $LOG_FILE"

# Change to project directory
cd "$PROJECT_DIR" || {
    log "ERROR: Cannot change to project directory: $PROJECT_DIR"
    exit 1
}

# Activate virtual environment if it exists
if [ -d "$VENV_PATH" ]; then
    log "Activating virtual environment..."
    source "$VENV_PATH/bin/activate" || {
        log "ERROR: Cannot activate virtual environment"
        exit 1
    }
else
    log "WARNING: Virtual environment not found at $VENV_PATH"
    log "Using system Python..."
fi

# Check if input file exists
if [ ! -f "fact_energy_market.parquet" ]; then
    log "ERROR: Input file 'fact_energy_market.parquet' not found"
    exit 1
fi

# Run the forecast
log "Starting forecast execution..."
python run_forecast.py --verbose 2>&1 | tee -a "$LOG_FILE"
EXIT_CODE=${PIPESTATUS[0]}

# Check execution result
if [ $EXIT_CODE -eq 0 ]; then
    log "✅ Forecast completed successfully"

    # Optional: Send success notification
    # You can uncomment and customize these lines:
    # echo "Energy forecast completed successfully" | mail -s "Forecast Success" admin@company.com
    # curl -X POST "https://your-webhook-url.com/forecast-success"

else
    log "❌ Forecast failed with exit code: $EXIT_CODE"

    # Optional: Send failure notification
    # You can uncomment and customize these lines:
    # echo "Energy forecast failed. Check logs at $LOG_FILE" | mail -s "Forecast FAILED" admin@company.com
    # curl -X POST "https://your-webhook-url.com/forecast-failed" -d "log_file=$LOG_FILE"
fi

# Cleanup old log files (keep last 30 days)
log "Cleaning up old log files..."
find "$LOG_DIR" -name "forecast_*.log" -type f -mtime +30 -delete 2>/dev/null

log "Execution completed at $(date)"
log "=========================================="

exit $EXIT_CODE
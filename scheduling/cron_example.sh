#!/bin/bash
# Energy Ops Forecast - Cron Scheduling Example
# ==============================================
#
# This script shows how to set up automated scheduling using cron.
# The forecast will run every Monday at 06:00 AM.

# Instructions:
# 1. Edit your crontab: crontab -e
# 2. Add the line below (adjust paths as needed):
#
# 0 6 * * 1 /path/to/energy-ops-forecast/scheduling/run_weekly_forecast.sh
#
# Schedule breakdown:
# 0     - minute (0)
# 6     - hour (6 AM)
# *     - day of month (any)
# *     - month (any)
# 1     - day of week (Monday, 0=Sunday, 1=Monday, etc.)

# Alternative schedules:
# Daily at 6 AM:        0 6 * * *
# Twice daily:          0 6,18 * * *
# Every 4 hours:        0 */4 * * *
# Business days only:   0 6 * * 1-5

echo "Setting up cron job for Energy Ops Forecast..."
echo ""
echo "To install this cron job:"
echo "1. Make this script executable: chmod +x scheduling/run_weekly_forecast.sh"
echo "2. Edit your crontab: crontab -e"
echo "3. Add this line:"
echo "   0 6 * * 1 $(pwd)/scheduling/run_weekly_forecast.sh"
echo ""
echo "To view existing cron jobs: crontab -l"
echo "To remove cron jobs: crontab -r"
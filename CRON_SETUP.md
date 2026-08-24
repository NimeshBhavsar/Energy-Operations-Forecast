# ⚡ Automated Weekly Forecast - Cron Setup

## Quick Setup Instructions

### 1. Add to Crontab
```bash
crontab -e
```

Add this line for **Monday 11:00 AM** execution:
```bash
0 11 * * 1 /path/to/energy-ops-forecast/scripts/setup_cron_env.sh >> /path/to/energy-ops-forecast/logs/cron_output.log 2>&1
```

### 2. Verify Cron Setup
```bash
crontab -l
```

### 3. Monitor Execution
Check logs after first run:
```bash
tail -f /path/to/energy-ops-forecast/logs/cron_output.log
tail -f /path/to/energy-ops-forecast/logs/automated_email.log
tail -f /path/to/energy-ops-forecast/logs/cron_execution.log
```

## System Components

- **`scripts/automated_email_forecast.py`** - Main automation script
- **`scripts/setup_cron_env.sh`** - Cron environment setup with pyenv
- **Email sent to:** `nimeshbhavsar006@gmail.com`
- **Attachments:** forecast_baseline.csv, forecast_scenario_shock.csv, forecast_scenario_delta.csv

## Test Manual Execution
```bash
cd /path/to/energy-ops-forecast
bash scripts/setup_cron_env.sh
```

## Cron Schedule Format
```
# ┌───────────── minute (0 - 59)
# │ ┌───────────── hour (0 - 23)
# │ │ ┌───────────── day of the month (1 - 31)
# │ │ │ ┌───────────── month (1 - 12)
# │ │ │ │ ┌───────────── day of the week (0 - 6) (Sunday to Saturday)
# │ │ │ │ │
# * * * * *
  0 11 * * 1  # Every Monday at 11:00 AM
```

## Success Confirmation
After setup, you'll receive automated emails every Monday at 11:00 AM with the latest energy forecast data ready for Power BI consumption.
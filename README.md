# ⚡ Energy Operations Forecast

> Short-term price and demand forecasting for the Australian National Electricity Market (NEM), with scenario stress-testing, an executive Streamlit dashboard, and automated report delivery.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-FF4B4B?logo=streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-5.15%2B-3F4F75?logo=plotly&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.0%2B-150458?logo=pandas&logoColor=white)

---

## Table of Contents

- [Overview](#overview)
- [Why Short-Term Forecasting Matters](#why-short-term-forecasting-matters)
- [Dashboard](#dashboard)
- [The Data](#the-data)
- [How the Forecast Works](#how-the-forecast-works)
- [Scenario Model](#scenario-model)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Automated Weekly Reports](#automated-weekly-reports)
- [Power BI Integration](#power-bi-integration)
- [Authentication](#authentication)
- [Limitations](#limitations)
- [Roadmap](#roadmap)

---

## Overview

An end-to-end operational forecasting pipeline for electricity market operations. It takes historical half-hourly market data, produces a 7-day forward forecast of price and demand across three NEM regions, stress-tests that forecast against an extreme scenario, and publishes the results three ways:

1. **An interactive Streamlit dashboard** — five pages covering executive summary, regional comparison, price spikes, weather impact, and scenario analysis.
2. **CSV outputs** — baseline, shock, and delta files shaped for Power BI ingestion.
3. **Automated email reports** — the same CSVs delivered on a cron schedule.

The emphasis is on the **operational plumbing**: a reproducible pipeline, scenario comparison, scheduled delivery, and a decision-ready front end. The forecasting model itself is deliberately simple and swappable — see [How the Forecast Works](#how-the-forecast-works).

## Why Short-Term Forecasting Matters

In the NEM, spot prices are set every five minutes and settled half-hourly, and they can move by orders of magnitude within a single trading day. Participants with spot exposure — retailers, large industrial loads, and generators — need a forward view of both price and demand to make hedging, bidding, and load-shifting decisions before the interval arrives.

Two properties of the market make this hard:

- **Volatility is concentrated.** A small number of intervals account for a disproportionate share of total cost. Price spikes cluster around high-temperature, high-demand, low-renewable-output periods.
- **Regions diverge.** Interconnector constraints mean NSW, QLD, and VIC can price very differently at the same moment, so a single national view hides the picture.

This project is built around those two facts: the shock scenario models the concentrated-volatility case, and every view can be filtered by region.

> **Note:** The dashboard's Financial Impact Calculator estimates cost exposure from a portfolio size **you enter**, applied to the modelled price delta. It is an illustrative sizing tool, not a claim about realised returns.

## Dashboard

| Page | What it shows |
|---|---|
| **Home** | Executive summary — headline KPIs, risk assessment, 7-day price/demand overview, financial impact calculator |
| **Regional Analysis** | Side-by-side comparison across NSW1, QLD1, VIC1, including inter-regional spreads |
| **Price and Spikes** | Distribution of forecast prices and identification of spike intervals |
| **Weather Impact** | Relationship between weather drivers (temperature, solar, wind) and price/demand |
| **Forecast Scenarios** | Baseline vs shock comparison and delta analysis |

All pages share a region selector and a forecast-period date filter.

## The Data

Input is a single Parquet file, `fact_energy_market.parquet`:

| Property | Value |
|---|---|
| Records | 9,651 |
| Regions | `NSW1` (New South Wales), `QLD1` (Queensland), `VIC1` (Victoria) |
| Interval | 30 minutes |
| Coverage | 2025-07-06 → 2025-09-11 (~9 weeks) |

**Column groups:**

- **Market** — `RRP` (Regional Reference Price, $/MWh), `TOTALDEMAND` (MW)
- **Temporal** — `datetime`, `hour`, `day_of_week`, `is_weekend`, `peak_period`
- **Weather** — `temp_c`, `rh_pct`, `rain_mm`, `sunshine_sec`, `shortwave_wm2`, `wind_speed_ms`
- **Engineered** — lags (`RRP_lag_1h/12h/24h`, `TOTALDEMAND_lag_*`), rolling means (`*_rolling_3h/6h/24h`), `temp_bin`, `spike_flag`, and a `compound_highTemp_lowSolar_peakHour` interaction flag

The engineered lag and rolling features are present in the dataset and available for modelling, but the current baseline generator does not consume them — see below.

## How the Forecast Works

**Be aware of what this is.** The baseline forecast in `pipeline/operational.py` is a **heuristic profile model**, not a trained statistical or machine-learning model. For each region it takes the historical mean, then applies:

- a **time-of-day multiplier** (peak 07:00–09:00 and 17:00–21:00; off-peak overnight; shoulder otherwise),
- a **weekend multiplier**,
- a **Gaussian noise term** for variation.

```
forecast = historical_regional_mean × hour_multiplier × weekend_multiplier × noise
```

This produces a plausible, correctly-shaped 7-day half-hourly profile (1,008 rows per scenario: 336 intervals × 3 regions) that exercises the full pipeline end to end. It is **not** a validated predictive model, and no accuracy metrics are computed anywhere in this repository.

The design intent is that `_forecast_price()` and `_forecast_demand()` are the seams where a real model drops in. The lag and rolling features already in the dataset exist for exactly that purpose. See [Roadmap](#roadmap).

## Scenario Model

Three outputs are produced on every run:

| Output | Description |
|---|---|
| `forecast_baseline.csv` | Base-case forward profile |
| `forecast_scenario_shock.csv` | Stressed case — price scaled ~1.3×, demand ~1.15×, with an additional 1.5–2.5× multiplier applied to peak intervals |
| `forecast_scenario_delta.csv` | Interval-by-interval difference (shock − baseline), for impact analysis |

The delta file is what drives the risk assessment and financial impact views in the dashboard.

## Project Structure

```
.
├── app/                            # Streamlit dashboard
│   ├── Home.py                     # Executive summary + run/email controls
│   ├── auth.py                     # Google OAuth2 (currently in demo mode)
│   └── pages/                      # Regional, spikes, weather, scenarios
├── pipeline/
│   └── operational.py              # Forecast generation (baseline/shock/delta)
├── scripts/
│   ├── automated_email_forecast.py # Run forecast + email, for cron
│   └── setup_cron_env.sh           # Loads env vars for the cron job
├── scheduling/
│   ├── airflow_dag.py              # Airflow DAG example
│   ├── cron_example.sh
│   └── run_weekly_forecast.sh
├── data/                           # Generated CSV outputs
├── fact_energy_market.parquet      # Input dataset
└── run_forecast.py                 # CLI entry point
```

## Quick Start

```bash
git clone https://github.com/<your-username>/energy-ops-forecast.git
cd energy-ops-forecast

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows, activate with `.venv\Scripts\activate` instead.

Generate the forecast CSVs, then launch the dashboard:

```bash
python run_forecast.py
streamlit run app/Home.py
```

The dashboard opens at `http://localhost:8501`.

**`run_forecast.py` options:**

| Flag | Purpose |
|---|---|
| `--input` | Input parquet path (default `fact_energy_market.parquet`) |
| `--output-dir` | Output directory for CSVs (default `data`) |
| `--verbose` | Verbose logging |
| `--dry-run` | Validate inputs without writing outputs |

## Configuration

Email delivery needs SMTP credentials. Provide them either as environment variables or via Streamlit secrets — the app checks secrets first, then falls back to the environment.

**Option A — `.streamlit/secrets.toml`** (copy the provided `.streamlit/secrets.toml.example`):

```toml
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = "587"
SMTP_USER = "your-email@gmail.com"
SMTP_PASS = "your-app-password"
SMTP_USE_TLS = "true"
```

**Option B — `.env`** (used by the cron script):

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
SMTP_USE_TLS=true
```

For Gmail, `SMTP_PASS` must be a **16-character App Password**, not your account password. Enable 2-Factor Authentication, then generate one under **Google Account → Security → App passwords**.

> Both `.env` and `.streamlit/secrets.toml` are gitignored. Never commit credentials.

## Automated Weekly Reports

`scripts/automated_email_forecast.py` regenerates the forecast and emails the three CSVs in a single step — intended to run unattended.

```bash
mkdir -p logs
crontab -e
```

```cron
# Every Monday at 06:00
0 6 * * 1 cd /path/to/energy-ops-forecast && python scripts/automated_email_forecast.py
```

The `logs/` directory must exist before the first run — the script opens a log file there on import.

Use `scripts/setup_cron_env.sh` if your cron environment needs the variables loaded from `.env` first. See [CRON_SETUP.md](CRON_SETUP.md) for details, and [scheduling/airflow_dag.py](scheduling/airflow_dag.py) for an Airflow alternative.

The dashboard's **Run Forecast & Email** button triggers the same forecast-and-send flow interactively.

## Power BI Integration

The three CSVs in `data/` are written flat and typed for direct import:

| Column | Type |
|---|---|
| `datetime` | timestamp (30-min intervals) |
| `region` | text (`NSW1` / `QLD1` / `VIC1`) |
| `forecast_price` | decimal ($/MWh) |
| `forecast_demand` | decimal (MW) |

The delta file carries `delta_price` and `delta_demand` in place of the forecast columns. Point a scheduled Power BI refresh at the `data/` directory to pick up each new run.

## Authentication

`app/auth.py` contains a full Google OAuth2 implementation — authorization-code flow with PKCE, state verification, and token exchange.

**It is currently bypassed.** `require_login()` short-circuits to a demo user so the dashboard can be evaluated without credentials. The original gated implementation is preserved as `require_login_original()`.

To enable real authentication, swap the call in `app/Home.py` to `require_login_original()` and set:

```toml
GOOGLE_CLIENT_ID = "..."
GOOGLE_CLIENT_SECRET = "..."
OAUTH_REDIRECT_URI = "http://localhost:8501"
```

Create the credentials in the [Google Cloud Console](https://console.cloud.google.com/) as an **OAuth 2.0 Client ID** of type *Web application*, with both the JavaScript origin and the redirect URI set to your app URL.

## Roadmap

- Replace the heuristic generator with a trained model (gradient boosting on the existing lag/rolling features is the natural first step) behind the same `_forecast_price()` / `_forecast_demand()` interface.
- Add a backtesting harness with MAE/RMSE, and pinball loss for probabilistic forecasts.
- Fit shock scenarios to historical spike distributions rather than fixed multipliers.
- Ingest live AEMO dispatch data and a weather API for rolling re-forecasts.
- Add spike-probability classification using the existing `spike_flag` and compound-condition features.

---

*Built as a demonstration of an end-to-end energy operations forecasting pipeline — data to dashboard to scheduled delivery.*

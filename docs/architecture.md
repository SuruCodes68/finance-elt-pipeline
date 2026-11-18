# Architecture

## ELT vs ETL — why ELT here

**ETL** transforms data *before* loading it: the transform code owns the
cleaned data, and the raw source is usually discarded. That is hard to
audit and hard to re-run when a business rule changes.

**ELT** loads raw data first, then transforms it inside the warehouse:

- `staging.raw_prices` / `staging.raw_fundamentals` are the immutable
  source of truth — exactly as the API returned them, plus `loaded_at`.
- Transformations are version-controlled dbt SQL (`dbt/models/`), so any
  mart can be rebuilt from raw with `dbt run --full-refresh`.
- New questions don't require re-extracting: add a dbt model, not a new
  extraction job.

The trade-off: the warehouse must do the transformation work, and raw
tables need retention/governance (see below). For analytics workloads
with dbt + Postgres/Snowflake + Power BI, that trade-off is the standard
choice — and it is what the target job descriptions ask for
(data pipelines, data modeling, data quality/governance).

## Lineage

```
Yahoo Finance (yfinance) ─┐
FMP API (optional)        ├─► src/extract_*.py ─► src/validate.py
Polygon API (optional)    ┘                              │
                                                         ▼
                                          PostgreSQL: staging.raw_prices
                                                        staging.raw_fundamentals
                                                         │
                                                         ▼ dbt
                                          stg_prices / stg_fundamentals
                                                         │
                                                         ▼
                                          int_daily_returns (LAG close)
                                                         │
                                              ┌──────────┴──────────┐
                                              ▼                     ▼
                                   dim_ticker            fct_daily_prices
                                   fct_portfolio_risk
                                              │
                                              ▼
                                   Power BI (Overview / Risk / Ticker Deep Dive)
```

`src/risk.py` computes the same metrics as `fct_portfolio_risk.sql`
(volatility, Sharpe, max drawdown, inverse-volatility weights) in Python,
so the pipeline's printed summary and the mart agree by construction.
Power BI DAX measures in `powerbi/README.md` mirror them a third time —
keep the three in sync when changing a definition (252 trading days,
risk-free rate 4%).

## Data quality approach

Three layers, same rules, increasing strictness:

1. **Python validation (`src/validate.py`)** — fails fast at load time:
   required columns, no null `ticker`/`date`/`close`, `close > 0`,
   `high >= low`, no duplicate `(ticker, date)`.
2. **dbt tests (`dbt/models/**/schema.yml`)** — `unique`, `not_null`,
   `relationships` (fact → `dim_ticker`), `accepted_range` for
   `close > 0` and `daily_return` in [-0.5, 0.5]. Run with `dbt test`.
3. **Governance (manual, v2)** — `staging` is append-only raw;
   only dbt writes to `marts`. No hand-edits to mart tables.
   `loaded_at` on every staging row gives a basic audit trail.

Known limits: the sample CSV is synthetic demo data (15 days, 3 tickers)
and includes calendar days, not trading days only. Live data from Yahoo
Finance is trading days only. Validation does not yet check for missing
trading days or stale data — add a freshness check in v2.

## Scheduling idea (v2)

The pipeline is currently run manually:

```bash
python -m src.run_pipeline --tickers AAPL,MSFT,NVDA --start-date 2024-01-01
cd dbt && dbt run && dbt test
```

**v2 — Airflow:** one DAG with tasks `extract → load → validate → dbt run → dbt test`,
scheduled daily after market close (e.g. 21:00 UTC), with retries and
Slack/email alerts on validation failure. Airflow connections would hold
`DATABASE_URL` / API keys, not code.

**v2 — lightweight alternative:** a cron job running the same two commands,
plus `dbt test` failing the job (non-zero exit) so failures are visible.
This is the fastest path to “automated” on a single machine.

**v2 — warehouse:** the same dbt project runs on Snowflake/BigQuery by
changing only `dbt/profiles.yml` and `DATABASE_URL`; no model SQL changes
are needed for the standard models used here.

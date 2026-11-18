# dbt — transformations (staging → intermediate → marts)

```bash
cd dbt
dbt deps        # no external packages yet; safe to skip
dbt test        # runs the tests in schema.yml files
dbt run         # builds staging -> intermediate -> marts
dbt docs generate && dbt docs serve   # lineage + documentation
```

## Model layers

| Layer | Models | Purpose |
|---|---|---|
| staging | `stg_prices`, `stg_fundamentals` | Clean + cast raw `staging.*` tables, no business logic |
| intermediate | `int_daily_returns` | Daily returns per ticker (LAG over close) |
| marts | `dim_ticker`, `fct_daily_prices`, `fct_portfolio_risk` | Star-schema tables consumed by Power BI |

## Tests

`schema.yml` files add `unique`, `not_null`, `relationships`, and
`accepted_range` tests — e.g. `close > 0` in `stg_prices`, and
`daily_return` within [-0.5, 0.5] in `int_daily_returns`. These mirror the
Python validation in `src/validate.py`, so bad data is caught twice:
once at load, once in dbt.

Set `DBT_PROFILES_DIR` or copy `profiles.yml.example` to
`~/.dbt/profiles.yml` before running dbt. Requires a running Postgres
(see the repo root `docker-compose.yml`).

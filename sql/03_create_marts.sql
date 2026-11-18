-- Mart tables are created/managed by dbt (see dbt/models/marts/).
-- These DDL statements document the expected shape for Power BI.
-- Do not hand-edit mart data; rebuild with `cd dbt && dbt run`.

-- dim_ticker: one row per ticker (see dbt/models/marts/dim_ticker.sql)
-- fct_daily_prices: one row per ticker per day, with returns (see fct_daily_prices.sql)
-- fct_portfolio_risk: one row per ticker with risk metrics + weights (see fct_portfolio_risk.sql)
SELECT 1; -- placeholder so the init script is valid SQL

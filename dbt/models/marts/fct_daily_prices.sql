{{ config(materialized='table') }}

-- Fact: one row per ticker per day, with daily return for Power BI time series.
select
    ticker,
    date,
    open,
    high,
    low,
    close,
    adj_close,
    volume,
    prev_close,
    daily_return
from {{ ref('int_daily_returns') }}

{{ config(materialized='view') }}

-- Daily simple returns using LAG() over each ticker's close prices.
select
    ticker,
    date,
    close,
    lag(close) over (partition by ticker order by date) as prev_close,
    case
        when lag(close) over (partition by ticker order by date) is null
            then null
        else close / lag(close) over (partition by ticker order by date) - 1
    end as daily_return,
    volume
from {{ ref('stg_prices') }}

{{ config(materialized='view') }}

-- Clean raw prices: cast types, drop rows with no close, keep raw values intact.
select
    upper(ticker) as ticker,
    cast(date as date) as date,
    cast(open as numeric) as open,
    cast(high as numeric) as high,
    cast(low as numeric) as low,
    cast(close as numeric) as close,
    cast(adj_close as numeric) as adj_close,
    cast(volume as bigint) as volume,
    loaded_at
from {{ source('staging', 'raw_prices') }}
where close is not null
  and close > 0

{{ config(materialized='view') }}

select
    upper(ticker) as ticker,
    company_name,
    sector,
    industry,
    cast(market_cap as numeric) as market_cap,
    cast(beta as numeric) as beta,
    cast(price as numeric) as price,
    currency,
    loaded_at
from {{ source('staging', 'raw_fundamentals') }}
where ticker is not null

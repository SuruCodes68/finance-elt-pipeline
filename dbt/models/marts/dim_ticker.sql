{{ config(materialized='table') }}

-- Dimension: one row per ticker, enriched with fundamentals when available.
select
    p.ticker,
    f.company_name,
    f.sector,
    f.industry,
    f.beta,
    f.market_cap,
    f.currency,
    min(p.date) as first_price_date,
    max(p.date) as last_price_date,
    count(*) as n_price_days
from {{ ref('stg_prices') }} as p
left join {{ ref('stg_fundamentals') }} as f
    on p.ticker = f.ticker
group by p.ticker, f.company_name, f.sector, f.industry, f.beta, f.market_cap, f.currency

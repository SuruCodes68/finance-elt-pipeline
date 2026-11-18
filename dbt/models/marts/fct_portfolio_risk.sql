{{ config(materialized='table') }}

-- Fact: one row per ticker with risk metrics and inverse-volatility weights.
-- Volatility / Sharpe / drawdown here mirror src/risk.py definitions.
with returns as (
    select ticker, daily_return
    from {{ ref('int_daily_returns') }}
    where daily_return is not null
),
stats as (
    select
        ticker,
        count(*) as n_days,
        avg(daily_return) as mean_daily_return,
        stddev(daily_return) as std_daily_return,
        min(daily_return) as min_daily_return,
        max(daily_return) as max_daily_return
    from returns
    group by ticker
),
vol as (
    select
        ticker,
        n_days,
        -- Annualised volatility: std * sqrt(252)
        std_daily_return * sqrt(252) as volatility,
        -- Annualised Sharpe, risk-free rate 4%: (mean - rf/252) / std * sqrt(252)
        case
            when std_daily_return = 0 or std_daily_return is null then 0
            else (mean_daily_return - 0.04 / 252) / std_daily_return * sqrt(252)
        end as sharpe_ratio,
        min_daily_return,
        max_daily_return
    from stats
),
weights as (
    select
        ticker,
        case
            when volatility = 0 or volatility is null then 0
            else 1.0 / volatility
        end as inverse_vol
    from vol
)
select
    v.ticker,
    v.n_days,
    v.volatility,
    v.sharpe_ratio,
    v.min_daily_return,
    v.max_daily_return,
    w.inverse_vol / nullif(sum(w.inverse_vol) over (), 0) as risk_weight
from vol as v
join weights as w on v.ticker = w.ticker

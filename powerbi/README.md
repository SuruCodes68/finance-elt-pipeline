# Power BI dashboard — spec

Connect Power BI Desktop to the dbt marts in Postgres:
**Get Data → PostgreSQL → server `localhost`, database `finance`**, then load
`marts.dim_ticker`, `marts.fct_daily_prices`, `marts.fct_portfolio_risk`.

## Relationships (star schema)

- `dim_ticker[ticker]` (1) → `fct_daily_prices[ticker]` (many)
- `dim_ticker[ticker]` (1) → `fct_portfolio_risk[ticker]` (many)
- `fct_daily_prices[date]` is the date field — mark it as a date table / use a calendar table for time intelligence.

## Pages

### 1. Overview
| Visual | Fields |
|---|---|
| KPI cards | Total Return, Volatility, Sharpe Ratio, Max Drawdown (from measures below) |
| Line chart — close price over time | Axis: `fct_daily_prices[date]`; Values: `fct_daily_prices[close]`; Legend: `dim_ticker[ticker]` |
| Bar chart — total return by ticker | Axis: `dim_ticker[ticker]`; Values: Total Return measure |
| Slicer | `dim_ticker[sector]`, `fct_daily_prices[date]` (date range) |

### 2. Risk
| Visual | Fields |
|---|---|
| Table | `dim_ticker[ticker]`, `fct_portfolio_risk[volatility]`, `fct_portfolio_risk[sharpe_ratio]`, `fct_portfolio_risk[risk_weight]` |
| Donut — portfolio weights | Legend: `dim_ticker[ticker]`; Values: `fct_portfolio_risk[risk_weight]` |
| Bar chart — volatility by ticker | Axis: `dim_ticker[ticker]`; Values: `fct_portfolio_risk[volatility]` |
| Line chart — daily returns | Axis: `fct_daily_prices[date]`; Values: `fct_daily_prices[daily_return]`; Legend: `dim_ticker[ticker]` |

### 3. Ticker Deep Dive
| Visual | Fields |
|---|---|
| Slicer (single-select) | `dim_ticker[ticker]` |
| Candlestick / line chart | `fct_daily_prices[date]`, `open`, `high`, `low`, `close` |
| Card — company info | `dim_ticker[company_name]`, `dim_ticker[sector]`, `dim_ticker[industry]`, `dim_ticker[beta]`, `dim_ticker[market_cap]` |
| Table — recent daily prices | `fct_daily_prices[date]`, `close`, `daily_return`, `volume` (sorted by date desc) |

## DAX measures

Create these in the `fct_daily_prices` / `fct_portfolio_risk` model.
They mirror `src/risk.py` (252 trading days/year, risk-free rate 4%).

```dax
Total Return =
VAR FirstClose =
    CALCULATE ( MIN ( fct_daily_prices[close] ), ALLSELECTED ( fct_daily_prices[date] ) )
VAR LastClose =
    CALCULATE ( MAX ( fct_daily_prices[close] ), ALLSELECTED ( fct_daily_prices[date] ) )
RETURN DIVIDE ( LastClose - FirstClose, FirstClose )

Volatility =
STDEV.P ( fct_daily_prices[daily_return] ) * SQRT ( 252 )

Sharpe Ratio =
VAR MeanReturn = AVERAGE ( fct_daily_prices[daily_return] )
VAR Vol = STDEV.P ( fct_daily_prices[daily_return] )
RETURN DIVIDE ( MeanReturn - 0.04 / 252, Vol ) * SQRT ( 252 )

Max Drawdown =
-- Implement as a measure over a running-max helper, or use the Python/dbt
-- summary in fct_portfolio_risk for the headline card and show the
-- drawdown series in the line chart. See docs/architecture.md.
VAR CurrentClose = MAX ( fct_daily_prices[close] )
VAR RunningMax =
    CALCULATE ( MAX ( fct_daily_prices[close] ), FILTER ( ALLSELECTED ( fct_daily_prices ), fct_daily_prices[date] <= MAX ( fct_daily_prices[date] ) ) )
RETURN DIVIDE ( CurrentClose - RunningMax, RunningMax )

Avg Daily Return = AVERAGE ( fct_daily_prices[daily_return] )
```

> Note: the sample data (`data/sample/sample_prices.csv`, 15 days × 3 tickers)
> is for demoing the pipeline — for a meaningful dashboard, run the live
> pipeline with `--start-date 2024-01-01` first, then refresh Power BI.

"""Risk analytics: returns, volatility, Sharpe ratio, drawdown, weights.

Pure pandas/numpy functions so they are easy to unit-test and to reuse
inside dbt-adjacent Python jobs, notebooks, and the Power BI DAX layer
(which mirrors these definitions — see ``powerbi/README.md``).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252


def daily_returns(prices: pd.Series) -> pd.Series:
    """Simple daily returns, ``price_t / price_{t-1} - 1``.

    The first observation has no prior price, so it is dropped.
    """
    returns = prices.sort_index().pct_change().dropna()
    returns.name = "daily_return"
    return returns


def annualised_volatility(returns: pd.Series) -> float:
    """Annualised volatility = std(daily returns) * sqrt(252)."""
    if len(returns) < 2:
        return 0.0
    return float(returns.std(ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR))


def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.04) -> float:
    """Annualised Sharpe ratio.

    ``(mean daily return - daily risk-free rate) / std(daily return) * sqrt(252)``.
    Returns 0.0 when volatility is zero or there is no data.
    """
    if len(returns) < 2:
        return 0.0
    vol = returns.std(ddof=1)
    if vol == 0 or pd.isna(vol):
        return 0.0
    excess_daily = returns.mean() - risk_free_rate / TRADING_DAYS_PER_YEAR
    return float(excess_daily / vol * np.sqrt(TRADING_DAYS_PER_YEAR))


def max_drawdown(prices: pd.Series) -> float:
    """Maximum drawdown as a negative decimal (e.g. -0.12 = -12%).

    Drawdown at each point is ``price / running_max - 1``; the worst value
    is returned. Returns 0.0 for an empty or single-point series.
    """
    if len(prices) < 2:
        return 0.0
    series = prices.sort_index()
    running_max = series.cummax()
    drawdown = series / running_max - 1.0
    return float(drawdown.min())


def total_return(prices: pd.Series) -> float:
    """Total return over the whole series: ``last / first - 1``."""
    if len(prices) < 2:
        return 0.0
    series = prices.sort_index()
    return float(series.iloc[-1] / series.iloc[0] - 1.0)


def inverse_volatility_weights(volatilities: dict[str, float]) -> dict[str, float]:
    """Simple risk-weighted portfolio weights: weight ∝ 1 / volatility.

    Tickers with zero/negative volatility get zero weight. Weights sum to 1.
    This is the same logic used in ``dbt/models/marts/fct_portfolio_risk.sql``.
    """
    inverse = {
        ticker: (1.0 / vol if vol and vol > 0 else 0.0)
        for ticker, vol in volatilities.items()
    }
    total = sum(inverse.values())
    if total == 0:
        n = len(volatilities)
        return {ticker: (1.0 / n if n else 0.0) for ticker in volatilities}
    return {ticker: value / total for ticker, value in inverse.items()}


def summarise_ticker(
    prices: pd.Series, risk_free_rate: float = 0.04
) -> dict[str, float]:
    """One-row risk summary for a single ticker's close-price series."""
    returns = daily_returns(prices)
    return {
        "total_return": total_return(prices),
        "volatility": annualised_volatility(returns),
        "sharpe_ratio": sharpe_ratio(returns, risk_free_rate),
        "max_drawdown": max_drawdown(prices),
        "n_days": float(len(prices)),
    }

"""Unit tests for src/risk.py — runnable with: python -m pytest tests/ -v

Also runnable without pytest: python tests/test_risk.py
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.risk import (  # noqa: E402
    annualised_volatility,
    daily_returns,
    inverse_volatility_weights,
    max_drawdown,
    sharpe_ratio,
    summarise_ticker,
    total_return,
)


def test_daily_returns():
    prices = pd.Series([100.0, 110.0, 99.0])
    returns = daily_returns(prices)
    assert len(returns) == 2
    assert abs(returns.iloc[0] - 0.10) < 1e-9
    assert abs(returns.iloc[1] - (-0.10)) < 1e-9


def test_total_return():
    assert abs(total_return(pd.Series([100.0, 150.0])) - 0.50) < 1e-9
    assert total_return(pd.Series([100.0])) == 0.0


def test_max_drawdown():
    # Peak 100 -> trough 80 = -20%; recovery to 90 still -10% from peak.
    assert abs(max_drawdown(pd.Series([100.0, 110.0, 88.0, 99.0])) - (-0.20)) < 1e-9
    assert max_drawdown(pd.Series([100.0, 110.0, 120.0])) == 0.0


def test_volatility_and_sharpe_are_finite():
    prices = pd.Series([100.0, 102.0, 101.0, 105.0, 103.0, 107.0, 106.0, 110.0])
    returns = daily_returns(prices)
    assert annualised_volatility(returns) > 0
    assert sharpe_ratio(returns) != 0.0


def test_inverse_volatility_weights_sum_to_one():
    weights = inverse_volatility_weights({"AAPL": 0.20, "MSFT": 0.10, "NVDA": 0.40})
    assert abs(sum(weights.values()) - 1.0) < 1e-9
    # Lowest-volatility ticker (MSFT) gets the largest weight.
    assert weights["MSFT"] > weights["AAPL"] > weights["NVDA"]


def test_inverse_volatility_weights_zero_volatility():
    weights = inverse_volatility_weights({"AAPL": 0.0, "MSFT": 0.20})
    assert weights["AAPL"] == 0.0
    assert weights["MSFT"] == 1.0


def test_summarise_ticker():
    prices = pd.Series([100.0, 102.0, 101.0, 105.0, 103.0, 107.0])
    summary = summarise_ticker(prices)
    assert set(summary) == {
        "total_return",
        "volatility",
        "sharpe_ratio",
        "max_drawdown",
        "n_days",
    }
    assert summary["n_days"] == 6.0
    assert abs(summary["total_return"] - 0.07) < 1e-9


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASSED {name}")
    print("All risk tests passed.")

"""Extract daily prices from Yahoo Finance (yfinance, no API key)."""
from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)

COLUMNS = ["ticker", "date", "open", "high", "low", "close", "adj_close", "volume"]


def extract_yahoo(
    tickers: list[str], start_date: str, end_date: str | None = None
) -> pd.DataFrame:
    """Download daily OHLCV data for ``tickers`` from Yahoo Finance.

    Returns a tidy DataFrame with one row per ticker per trading day.
    Raises ImportError with a clear message if ``yfinance`` is not installed.
    """
    try:
        import yfinance as yf
    except ImportError as exc:  # pragma: no cover - import-time failure
        raise ImportError(
            "yfinance is not installed. Run: pip install -r requirements.txt"
        ) from exc

    frames: list[pd.DataFrame] = []
    for ticker in tickers:
        logger.info("Downloading %s from Yahoo Finance (from %s)", ticker, start_date)
        data = yf.download(
            ticker, start=start_date, end=end_date, progress=False, auto_adjust=False
        )
        if data.empty:
            logger.warning("No Yahoo Finance data returned for %s", ticker)
            continue
        # yfinance >= 0.2.31 can return MultiIndex columns for one ticker.
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        data = data.reset_index()
        data["ticker"] = ticker
        data = data.rename(
            columns={
                "Date": "date",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Adj Close": "adj_close",
                "Volume": "volume",
            }
        )
        frames.append(data[COLUMNS])

    if not frames:
        logger.warning("Yahoo Finance returned no data for any ticker.")
        return pd.DataFrame(columns=COLUMNS)
    return pd.concat(frames, ignore_index=True)

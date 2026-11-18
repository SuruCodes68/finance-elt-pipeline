"""Extract aggregates from Polygon.io — optional.

Skipped gracefully when ``POLYGON_API_KEY`` is not set. Never hardcode
a key: set it in ``.env`` (see ``.env.example``).
"""
from __future__ import annotations

import logging

import pandas as pd
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.polygon.io/v2/aggs/ticker"


def extract_polygon(
    ticker: str, start_date: str, end_date: str, api_key: str | None
) -> pd.DataFrame:
    """Fetch daily aggregates for one ticker, or an empty frame if no key."""
    if not api_key:
        logger.info(
            "POLYGON_API_KEY not set — skipping Polygon aggregates for %s", ticker
        )
        return pd.DataFrame()
    url = f"{BASE_URL}/{ticker}/range/1/day/{start_date}/{end_date}"
    try:
        resp = requests.get(
            url, params={"apiKey": api_key, "limit": 50000}, timeout=30
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Polygon request failed for %s: %s", ticker, exc)
        return pd.DataFrame()
    payload = resp.json()
    results = payload.get("results") or []
    if not results:
        logger.warning("Polygon returned no aggregates for %s", ticker)
        return pd.DataFrame()
    df = pd.DataFrame(results)
    df["ticker"] = ticker
    df["date"] = pd.to_datetime(df["t"], unit="ms").dt.date
    return df.rename(
        columns={"o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"}
    )[["ticker", "date", "open", "high", "low", "close", "volume"]]

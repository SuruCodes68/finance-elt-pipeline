"""Extract fundamentals from Financial Modeling Prep (FMP) — optional.

Skipped gracefully when ``FMP_API_KEY`` is not set. Never hardcode a key:
set it in ``.env`` (see ``.env.example``).
"""
from __future__ import annotations

import logging

import pandas as pd
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://financialmodelingprep.com/api/v3"


def extract_fmp_profile(ticker: str, api_key: str | None) -> pd.DataFrame:
    """Fetch a company profile for one ticker, or an empty frame if no key."""
    if not api_key:
        logger.info("FMP_API_KEY not set — skipping FMP fundamentals for %s", ticker)
        return pd.DataFrame()
    url = f"{BASE_URL}/profile/{ticker}"
    try:
        resp = requests.get(url, params={"apikey": api_key}, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("FMP request failed for %s: %s", ticker, exc)
        return pd.DataFrame()
    rows = resp.json()
    if not rows:
        logger.warning("FMP returned no profile for %s", ticker)
        return pd.DataFrame()
    profile = rows[0]
    return pd.DataFrame(
        [
            {
                "ticker": ticker,
                "company_name": profile.get("companyName"),
                "sector": profile.get("sector"),
                "industry": profile.get("industry"),
                "market_cap": profile.get("mktCap"),
                "beta": profile.get("beta"),
                "price": profile.get("price"),
                "currency": profile.get("currency"),
            }
        ]
    )


def extract_fmp_profiles(tickers: list[str], api_key: str | None) -> pd.DataFrame:
    """Fetch profiles for all tickers; empty frame when no key is set."""
    if not api_key:
        logger.info("FMP_API_KEY not set — skipping FMP extraction entirely.")
        return pd.DataFrame()
    frames = [extract_fmp_profile(t, api_key) for t in tickers]
    frames = [f for f in frames if not f.empty]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

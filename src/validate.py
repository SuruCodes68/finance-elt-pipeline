"""Data quality / validation checks for extracted price data.

These are the Python-side mirror of the dbt tests in
``dbt/models/staging/schema.yml`` — same rules, earlier in the pipeline,
so bad data fails fast instead of silently reaching the marts.
"""
from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ["ticker", "date", "open", "high", "low", "close", "volume"]


def validate_prices(df: pd.DataFrame) -> dict[str, int | list[str]]:
    """Run checks and return a summary dict; raise on hard failures.

    Checks: required columns present, no null tickers/dates/closes,
    close > 0, high >= low, no duplicate (ticker, date) rows.
    Returns ``{"rows": n, "failures": [...]}``; raises ValueError if any
    hard check fails.
    """
    failures: list[str] = []

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        failures.append(f"missing columns: {missing}")

    if df.empty:
        failures.append("empty dataframe")
        return {"rows": 0, "failures": failures}

    if df["ticker"].isna().any():
        failures.append("null ticker values")
    if df["date"].isna().any():
        failures.append("null date values")
    if df["close"].isna().any():
        failures.append("null close values")
    if (df["close"] <= 0).any():
        failures.append("close <= 0 found")
    if (df["high"] < df["low"]).any():
        failures.append("high < low found")

    dupes = int(df.duplicated(subset=["ticker", "date"]).sum())
    if dupes:
        failures.append(f"{dupes} duplicate (ticker, date) rows")

    if failures:
        for failure in failures:
            logger.error("Validation failed: %s", failure)
        raise ValueError("Data validation failed: " + "; ".join(failures))

    logger.info(
        "Validation passed: %d rows, %d tickers, %s to %s",
        len(df),
        df["ticker"].nunique(),
        df["date"].min(),
        df["date"].max(),
    )
    return {"rows": len(df), "failures": []}

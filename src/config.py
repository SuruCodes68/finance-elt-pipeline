"""Configuration for the finance ELT pipeline.

Loads settings from environment variables (see ``.env.example``).
No secrets are hardcoded here. API keys are optional: Yahoo Finance
needs no key, while FMP and Polygon are skipped gracefully when their
keys are absent.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

try:
    from dotenv import load_dotenv  # type: ignore
except ImportError:  # dotenv is optional; env vars still work without it
    def load_dotenv(*args, **kwargs):  # type: ignore
        return False

load_dotenv()

DEFAULT_TICKERS: list[str] = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "SPY"]
DEFAULT_START_DATE = "2024-01-01"


@dataclass(frozen=True)
class Settings:
    """Runtime settings, resolved from the environment."""

    database_url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL", "postgresql://finance:finance@localhost:5432/finance"
        )
    )
    tickers: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            t.strip().upper()
            for t in os.getenv("TICKERS", ",".join(DEFAULT_TICKERS)).split(",")
            if t.strip()
        )
    )
    start_date: str = os.getenv("START_DATE", DEFAULT_START_DATE)
    fmp_api_key: str | None = os.getenv("FMP_API_KEY") or None
    polygon_api_key: str | None = os.getenv("POLYGON_API_KEY") or None
    # Risk-free rate used for the Sharpe ratio (annualised, decimal).
    risk_free_rate: float = float(os.getenv("RISK_FREE_RATE", "0.04"))

    @property
    def has_fmp(self) -> bool:
        return bool(self.fmp_api_key)

    @property
    def has_polygon(self) -> bool:
        return bool(self.polygon_api_key)


SETTINGS = Settings()

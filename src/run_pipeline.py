"""CLI entry point for the finance ELT pipeline.

Usage:
    # Offline demo — no network, no Postgres, no API keys needed:
    python -m src.run_pipeline --sample

    # Live run (Yahoo Finance, no key; FMP/Polygon skipped without keys):
    python -m src.run_pipeline --tickers AAPL,MSFT,NVDA --start-date 2024-01-01

    # Load into Postgres instead of the SQLite demo file:
    python -m src.run_pipeline --sample --db-url postgresql://finance:finance@localhost:5432/finance

ELT flow: extract (Yahoo/FMP/Polygon) -> load raw to staging ->
validate -> compute risk summaries -> (dbt transforms to marts, see dbt/).
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

# Allow running as `python src/run_pipeline.py` from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import SETTINGS  # noqa: E402
from src.extract_fmp import extract_fmp_profiles  # noqa: E402
from src.extract_yahoo import extract_yahoo  # noqa: E402
from src.load_postgres import load_to_postgres, load_to_sqlite  # noqa: E402
from src.risk import (  # noqa: E402
    inverse_volatility_weights,
    summarise_ticker,
)
from src.validate import validate_prices  # noqa: E402

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

SAMPLE_PATH = Path(__file__).resolve().parent.parent / "data" / "sample" / "sample_prices.csv"


def load_sample() -> pd.DataFrame:
    """Load the bundled sample prices (offline, no network required)."""
    df = pd.read_csv(SAMPLE_PATH, parse_dates=["date"])
    logger.info("Loaded sample data: %d rows from %s", len(df), SAMPLE_PATH)
    return df


def print_risk_summary(prices: pd.DataFrame) -> dict[str, dict[str, float]]:
    """Compute and print a per-ticker risk summary; return it for tests."""
    summaries: dict[str, dict[str, float]] = {}
    vols: dict[str, float] = {}
    for ticker, group in prices.groupby("ticker"):
        series = group.sort_values("date").set_index("date")["close"]
        summary = summarise_ticker(series, SETTINGS.risk_free_rate)
        summaries[str(ticker)] = summary
        vols[str(ticker)] = summary["volatility"]

    weights = inverse_volatility_weights(vols)
    print("\n=== Risk summary (per ticker) ===")
    print(f"{'Ticker':<8}{'Return':>10}{'Vol':>10}{'Sharpe':>10}{'Max DD':>10}")
    for ticker, s in sorted(summaries.items()):
        print(
            f"{ticker:<8}{s['total_return']:>10.2%}{s['volatility']:>10.2%}"
            f"{s['sharpe_ratio']:>10.2f}{s['max_drawdown']:>10.2%}"
        )
    print("\n=== Risk-weighted portfolio (inverse volatility) ===")
    for ticker, weight in sorted(weights.items(), key=lambda kv: -kv[1]):
        print(f"  {ticker:<8} {weight:>7.2%}")
    return summaries


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Finance ELT pipeline")
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Run offline on data/sample/sample_prices.csv (no network/Postgres).",
    )
    parser.add_argument(
        "--tickers",
        default=",".join(SETTINGS.tickers),
        help="Comma-separated tickers, e.g. AAPL,MSFT,NVDA",
    )
    parser.add_argument("--start-date", default=SETTINGS.start_date)
    parser.add_argument("--end-date", default=None)
    parser.add_argument(
        "--db-url",
        default=None,
        help="Postgres URL to load into; if omitted, --sample uses SQLite.",
    )
    args = parser.parse_args(argv)

    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]

    if args.sample:
        prices = load_sample()
    else:
        prices = extract_yahoo(tickers, args.start_date, args.end_date)
        fundamentals = extract_fmp_profiles(tickers, SETTINGS.fmp_api_key)
        if not fundamentals.empty:
            logger.info("FMP fundamentals loaded for %d tickers", len(fundamentals))
        if prices.empty:
            logger.error("No prices extracted — nothing to load.")
            return 1

    validate_prices(prices)

    loaded_to_db = False
    if args.db_url:
        load_to_postgres(prices, "raw_prices", args.db_url, schema="staging")
        loaded_to_db = True
    elif args.sample:
        try:
            load_to_sqlite(prices, "raw_prices")
            loaded_to_db = True
        except ImportError:
            # sqlalchemy not installed (e.g. pandas-only env): the risk
            # summary below still runs; install requirements for the load.
            logger.warning(
                "sqlalchemy not installed — skipping SQLite load. "
                "Run: pip install -r requirements.txt"
            )
    else:
        logger.info("No --db-url given — skipping load (validation + risk only).")

    print_risk_summary(prices)
    print("\nPipeline complete.")
    if args.sample:
        if loaded_to_db:
            print("Sample mode: data loaded to SQLite file finance_sample.db")
        else:
            print("Sample mode: SQLite load skipped (sqlalchemy not installed).")
        print("Next: docker compose up -d, then run with --db-url, then: cd dbt && dbt run")
    else:
        print("Next: run dbt to build staging -> intermediate -> marts (see dbt/README.md)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

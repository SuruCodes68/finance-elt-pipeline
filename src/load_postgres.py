"""Load extracted data into PostgreSQL (staging = raw, as extracted).

ELT, not ETL: raw data lands in ``staging.*`` untouched, and all
transformation happens downstream in dbt. A SQLite fallback is provided
for local demos (``--sample``) so the pipeline runs without Postgres.
"""
from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def get_engine(database_url: str):
    """Create a SQLAlchemy engine for any supported URL (imported lazily)."""
    from sqlalchemy import create_engine

    return create_engine(database_url)


def load_to_postgres(
    df: pd.DataFrame,
    table: str,
    database_url: str,
    schema: str = "staging",
    if_exists: str = "append",
) -> int:
    """Append ``df`` to ``schema.table`` in Postgres. Returns rows written."""
    if df.empty:
        logger.warning("Empty DataFrame — nothing to load into %s.%s", schema, table)
        return 0
    engine = get_engine(database_url)
    rows = len(df)
    df.to_sql(table, engine, schema=schema, if_exists=if_exists, index=False)
    logger.info("Loaded %d rows into %s.%s", rows, schema, table)
    return rows


def load_to_sqlite(
    df: pd.DataFrame, table: str, sqlite_path: str = "finance_sample.db"
) -> int:
    """Load ``df`` into a local SQLite file (demo / --sample mode)."""
    if df.empty:
        logger.warning("Empty DataFrame — nothing to load into SQLite %s", table)
        return 0
    engine = get_engine(f"sqlite:///{sqlite_path}")
    rows = len(df)
    df.to_sql(table, engine, if_exists="replace", index=False)
    logger.info("Loaded %d rows into SQLite %s (%s)", rows, table, sqlite_path)
    return rows

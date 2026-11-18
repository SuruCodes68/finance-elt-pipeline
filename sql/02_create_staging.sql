-- Staging tables hold data exactly as extracted (ELT: load raw first).
-- dbt staging models read from these tables and apply cleaning/tests.
CREATE TABLE IF NOT EXISTS staging.raw_prices (
    ticker     TEXT        NOT NULL,
    date       DATE        NOT NULL,
    open       NUMERIC(14, 4),
    high       NUMERIC(14, 4),
    low        NUMERIC(14, 4),
    close      NUMERIC(14, 4) NOT NULL,
    adj_close  NUMERIC(14, 4),
    volume     BIGINT,
    loaded_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (ticker, date)
);

CREATE TABLE IF NOT EXISTS staging.raw_fundamentals (
    ticker       TEXT PRIMARY KEY,
    company_name TEXT,
    sector       TEXT,
    industry     TEXT,
    market_cap   NUMERIC(20, 2),
    beta         NUMERIC(8, 4),
    price        NUMERIC(14, 4),
    currency     TEXT,
    loaded_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

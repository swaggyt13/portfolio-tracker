CREATE DATABASE portfolio;
\c portfolio;

CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    account_id VARCHAR(32) NOT NULL,
    symbol VARCHAR(32) NOT NULL,
    exchange VARCHAR(32),
    currency VARCHAR(8),
    quantity NUMERIC(18, 4) NOT NULL,
    avg_price NUMERIC(18, 4) NOT NULL,
    market_price NUMERIC(18, 4),
    market_value NUMERIC(18, 4),
    unrealized_pnl NUMERIC(18, 4),
    pnl_percent NUMERIC(10, 4),
    asset_class VARCHAR(16),
    bought_at TIMESTAMP,
    last_updated TIMESTAMP NOT NULL DEFAULT NOW(),
    first_seen TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (account_id, symbol)
);

ALTER TABLE positions ADD COLUMN IF NOT EXISTS bought_at TIMESTAMP;
ALTER TABLE positions ADD COLUMN IF NOT EXISTS previous_close NUMERIC(18, 4);
ALTER TABLE position_history ADD COLUMN IF NOT EXISTS previous_close NUMERIC(18, 4);

CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol);

CREATE TABLE IF NOT EXISTS position_history (
    id BIGSERIAL PRIMARY KEY,
    snapshot_at TIMESTAMP NOT NULL DEFAULT NOW(),
    account_id VARCHAR(32) NOT NULL,
    symbol VARCHAR(32) NOT NULL,
    quantity NUMERIC(18, 4) NOT NULL,
    avg_price NUMERIC(18, 4) NOT NULL,
    market_price NUMERIC(18, 4),
    market_value NUMERIC(18, 4),
    unrealized_pnl NUMERIC(18, 4),
    pnl_percent NUMERIC(10, 4)
);

CREATE INDEX IF NOT EXISTS idx_history_symbol_time ON position_history(symbol, snapshot_at DESC);

CREATE TABLE IF NOT EXISTS metadata (
    symbol VARCHAR(32) PRIMARY KEY,
    tag VARCHAR(8),
    sector VARCHAR(64),
    eps_guidance VARCHAR(32),
    notes TEXT,
    next_earnings_date DATE,
    earnings_reported BOOLEAN NOT NULL DEFAULT FALSE,
    exchange_override VARCHAR(16),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

ALTER TABLE metadata ADD COLUMN IF NOT EXISTS sector VARCHAR(64);
ALTER TABLE metadata ADD COLUMN IF NOT EXISTS eps_guidance VARCHAR(32);
ALTER TABLE metadata ADD COLUMN IF NOT EXISTS earnings_reported BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE metadata ADD COLUMN IF NOT EXISTS company_name TEXT;
ALTER TABLE metadata ADD COLUMN IF NOT EXISTS industry VARCHAR(64);
ALTER TABLE metadata ADD COLUMN IF NOT EXISTS enriched_at TIMESTAMP;

CREATE TABLE IF NOT EXISTS trades (
    id BIGSERIAL PRIMARY KEY,
    account_id VARCHAR(32) NOT NULL,
    symbol VARCHAR(32) NOT NULL,
    side VARCHAR(8) NOT NULL,
    quantity NUMERIC(18, 4) NOT NULL,
    price NUMERIC(18, 4) NOT NULL,
    executed_at TIMESTAMP NOT NULL,
    ibkr_exec_id VARCHAR(64) UNIQUE
);

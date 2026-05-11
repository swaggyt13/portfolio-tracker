"""Sync IBKR positions into the database and append a history snapshot."""
from __future__ import annotations

import logging
import time
from datetime import datetime
from decimal import Decimal
from typing import List

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.database import session_scope
from app.ibkr.client import IBKRClient, IBPosition
from app.models import Position, PositionHistory
from app.schemas import SyncResult

logger = logging.getLogger(__name__)


def run_sync() -> SyncResult:
    """Connect to IBKR, fetch positions, persist current snapshot, append history."""
    started = time.monotonic()
    errors: List[str] = []
    positions: List[IBPosition] = []
    accounts: List[str] = []

    try:
        with IBKRClient() as client:
            accounts = client.list_accounts()
            positions = client.fetch_positions()
    except Exception as exc:
        logger.exception("Sync failed during IBKR fetch")
        errors.append(f"ibkr: {exc}")

    if positions:
        # Yahoo lookup for previous_close so the dashboard can compute today's
        # change. Best effort: if Yahoo is throttling us, skip silently.
        try:
            _attach_previous_close(positions)
        except Exception as exc:
            logger.warning("previous_close fetch skipped: %s", exc)

        try:
            with session_scope() as db:
                _upsert_positions(db, positions)
                _append_history(db, positions)
        except Exception as exc:
            logger.exception("Sync failed during DB write")
            errors.append(f"db: {exc}")

        # Enrich metadata using the IBKR contract details we already pulled
        # alongside the positions. No external API; runs in its own session
        # so an enrichment hiccup can't poison the position upsert above.
        try:
            from app.services.enrichment import apply_ibkr_metadata
            with session_scope() as db:
                apply_ibkr_metadata(db, positions)
        except Exception as exc:
            logger.warning("IBKR metadata enrichment skipped: %s", exc)

    duration_ms = int((time.monotonic() - started) * 1000)
    return SyncResult(
        success=not errors,
        accounts_synced=len(accounts),
        positions_synced=len(positions),
        errors=errors,
        duration_ms=duration_ms,
    )


def _upsert_positions(db, positions: List[IBPosition]) -> None:
    """Upsert current snapshot keyed on (account_id, symbol).

    On conflict we update everything except first_seen so we preserve the original
    open date for the holding period calculation.
    """
    now = datetime.utcnow()
    rows = []
    for p in positions:
        pnl_pct = _pnl_pct(p.market_price, p.avg_price)
        rows.append(
            {
                "account_id": p.account_id,
                "symbol": p.symbol,
                "exchange": p.exchange,
                "currency": p.currency,
                "quantity": p.quantity,
                "avg_price": p.avg_price,
                "market_price": p.market_price,
                "market_value": p.market_value,
                "unrealized_pnl": p.unrealized_pnl,
                "pnl_percent": pnl_pct,
                "asset_class": p.asset_class,
                "bought_at": p.bought_at,
                "previous_close": p.previous_close,
                "last_updated": now,
                "first_seen": now,
            }
        )

    if not rows:
        return

    stmt = pg_insert(Position.__table__).values(rows)
    update_cols = {
        col.name: stmt.excluded[col.name]
        for col in Position.__table__.columns
        if col.name not in ("id", "first_seen", "account_id", "symbol", "bought_at")
    }
    # Only fill bought_at if it's still null. Once set, never overwrite,
    # because IBKR's execution window is short and a fresh sync may return
    # nothing for an older holding.
    from sqlalchemy import func as sa_func
    update_cols["bought_at"] = sa_func.coalesce(
        Position.__table__.c.bought_at, stmt.excluded.bought_at
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["account_id", "symbol"],
        set_=update_cols,
    )
    db.execute(stmt)

    # Remove positions that have closed: present in DB but not in this fetch.
    keys_now = {(p.account_id, p.symbol) for p in positions}
    existing = db.execute(select(Position.account_id, Position.symbol)).all()
    to_delete = [(a, s) for a, s in existing if (a, s) not in keys_now]
    if to_delete:
        for account_id, symbol in to_delete:
            db.execute(
                Position.__table__.delete().where(
                    (Position.account_id == account_id) & (Position.symbol == symbol)
                )
            )
        logger.info("Closed %d position(s) since last sync", len(to_delete))


def _append_history(db, positions: List[IBPosition]) -> None:
    now = datetime.utcnow()
    for p in positions:
        pnl_pct = _pnl_pct(p.market_price, p.avg_price)
        db.add(
            PositionHistory(
                snapshot_at=now,
                account_id=p.account_id,
                symbol=p.symbol,
                quantity=p.quantity,
                avg_price=p.avg_price,
                market_price=p.market_price,
                market_value=p.market_value,
                unrealized_pnl=p.unrealized_pnl,
                pnl_percent=pnl_pct,
                previous_close=p.previous_close,
            )
        )


def _attach_previous_close(positions: List[IBPosition]) -> None:
    """Fill in IBPosition.previous_close from Yahoo via the curl_cffi session.
    Mutates positions in place. Errors are swallowed since this column is
    nice to have but not load bearing.
    """
    try:
        from app.services.enrichment import _get_yahoo_session
        import yfinance as yf
    except Exception:
        return
    session = _get_yahoo_session()
    if session is None:
        return
    for p in positions:
        try:
            ticker = yf.Ticker(p.symbol, session=session)
            info = ticker.info or {}
            pc = info.get("regularMarketPreviousClose")
            if pc is None:
                pc = info.get("previousClose")
            if pc is None:
                continue
            f = float(pc)
            if f != f or f <= 0:
                continue
            p.previous_close = Decimal(str(f))
        except Exception as exc:
            logger.debug("previous_close lookup failed for %s: %s", p.symbol, exc)
            continue


def _pnl_pct(market_price, avg_price) -> Decimal | None:
    if market_price is None or avg_price is None:
        return None
    if Decimal(avg_price) == 0:
        return None
    return ((Decimal(market_price) - Decimal(avg_price)) / Decimal(avg_price)) * Decimal(100)

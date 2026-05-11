"""IBKR client wrapper using ib_insync.

Why ib_insync over the raw REST API: it handles the IBKR async event loop,
sequence numbering, and reconnects for us, while exposing a clean Python API.
We open a fresh connection per sync run so a stale socket never blocks the
scheduler. If you prefer the Client Portal REST API, replace this file with
an httpx based client that hits /v1/api/portfolio/{accountId}/positions/{page}.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional

import nest_asyncio
from ib_insync import IB, Stock, Contract, util

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ib_insync uses asyncio. APScheduler runs jobs in threads, so we patch
# the loop to allow nested run calls when needed.
nest_asyncio.apply()


@dataclass
class IBPosition:
    account_id: str
    symbol: str
    exchange: Optional[str]
    currency: Optional[str]
    quantity: Decimal
    avg_price: Decimal
    market_price: Optional[Decimal]
    market_value: Optional[Decimal]
    unrealized_pnl: Optional[Decimal]
    asset_class: Optional[str]
    bought_at: Optional[object] = None  # datetime, kept Optional to avoid import cycle
    # Filled in by reqContractDetails. Free, no subscription needed for stocks.
    long_name: Optional[str] = None
    industry: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    # Filled in by Yahoo for the daily P&L column.
    previous_close: Optional[Decimal] = None


class IBKRClient:
    """Thin wrapper that connects, fetches, and disconnects cleanly."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        client_id: Optional[int] = None,
        timeout: Optional[int] = None,
        readonly: Optional[bool] = None,
    ) -> None:
        self.host = host or settings.ibkr_host
        self.port = port or settings.ibkr_port
        self.client_id = client_id or settings.ibkr_client_id
        self.timeout = timeout or settings.ibkr_timeout
        self.readonly = settings.ibkr_readonly if readonly is None else readonly
        self.ib = IB()

    def __enter__(self) -> "IBKRClient":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.disconnect()

    def connect(self) -> None:
        try:
            self.ib.connect(
                host=self.host,
                port=self.port,
                clientId=self.client_id,
                timeout=self.timeout,
                readonly=self.readonly,
            )
            logger.info("Connected to IBKR at %s:%s", self.host, self.port)
        except Exception as exc:
            logger.exception("IBKR connect failed: %s", exc)
            raise

    def disconnect(self) -> None:
        if self.ib.isConnected():
            self.ib.disconnect()
            logger.info("Disconnected from IBKR")

    def is_connected(self) -> bool:
        return self.ib.isConnected()

    def list_accounts(self) -> List[str]:
        """Equivalent to /portfolio/accounts."""
        accounts = list(self.ib.managedAccounts())
        logger.info("Found %d account(s)", len(accounts))
        return accounts

    def fetch_positions(self) -> List[IBPosition]:
        """Fetch positions across all managed accounts.

        We use ib.portfolio() instead of ib.positions() + reqTickers() because
        portfolio items already include marketPrice, marketValue, and
        unrealizedPNL, computed by IBKR using delayed data when a live market
        data subscription is missing. This avoids both the subscription errors
        (Error 10089) and the NaN price values that come with reqTickers.
        """
        # ib_insync subscribes to account updates on connect and emits the
        # PortfolioItem events shortly after. Sleep briefly so portfolio() has
        # something to return.
        self.ib.sleep(1.0)

        portfolio_items = list(self.ib.portfolio())

        # Multi account setups need an explicit subscription per account.
        if not portfolio_items:
            for account in self.ib.managedAccounts():
                try:
                    self.ib.reqAccountUpdates(True, account)
                except Exception as exc:
                    logger.warning("reqAccountUpdates failed for %s: %s", account, exc)
            self.ib.sleep(1.5)
            for account in self.ib.managedAccounts():
                portfolio_items.extend(self.ib.portfolio(account))

        if not portfolio_items:
            logger.info("No portfolio items returned by IBKR")
            return []

        # Pull executions so we can find the earliest BUY date per symbol.
        bought_map = self._fetch_first_buy_dates()

        # Pull contract details once per unique conId. IBKR's reqContractDetails
        # returns longName, industry, category, subcategory for free with no
        # market data subscription required for stocks.
        details_map = self._fetch_contract_details(
            [item.contract for item in portfolio_items if item.position]
        )

        results: List[IBPosition] = []
        for item in portfolio_items:
            if not item.position:
                continue

            qty = Decimal(str(item.position))
            avg_price = _safe_decimal(item.averageCost) or Decimal(0)
            market_price = _safe_decimal(item.marketPrice)
            market_value = _safe_decimal(item.marketValue)
            unrealized = _safe_decimal(item.unrealizedPNL)

            cd = details_map.get(item.contract.conId, {})
            results.append(
                IBPosition(
                    account_id=item.account,
                    symbol=item.contract.symbol,
                    exchange=item.contract.primaryExchange or item.contract.exchange,
                    currency=item.contract.currency,
                    quantity=qty,
                    avg_price=avg_price,
                    market_price=market_price,
                    market_value=market_value,
                    unrealized_pnl=unrealized,
                    asset_class=item.contract.secType,
                    bought_at=bought_map.get((item.account, item.contract.symbol)),
                    long_name=cd.get("long_name"),
                    industry=cd.get("industry"),
                    category=cd.get("category"),
                    subcategory=cd.get("subcategory"),
                )
            )

        logger.info("Fetched %d open position(s)", len(results))
        return results

    def _fetch_contract_details(self, contracts) -> dict:
        """Map conId -> {long_name, industry, category, subcategory}."""
        out: dict = {}
        for contract in contracts:
            try:
                cds = self.ib.reqContractDetails(contract)
            except Exception as exc:
                logger.warning("reqContractDetails failed for %s: %s", contract.symbol, exc)
                continue
            if not cds:
                continue
            cd = cds[0]
            out[contract.conId] = {
                "long_name": getattr(cd, "longName", None) or None,
                "industry": getattr(cd, "industry", None) or None,
                "category": getattr(cd, "category", None) or None,
                "subcategory": getattr(cd, "subcategory", None) or None,
            }
            # IBKR limits ~10 contract detail requests per second. Six positions
            # is fine; we still pace defensively for larger portfolios.
            self.ib.sleep(0.05)
        return out

    def _fetch_first_buy_dates(self) -> dict:
        """Return a {(account, symbol): earliest_buy_datetime} map from
        ib.fills(). IBKR limits the executions window so older trades are
        not always present; callers should treat this as best effort.
        """
        out = {}
        try:
            fills = list(self.ib.fills())
        except Exception as exc:
            logger.warning("ib.fills() failed: %s", exc)
            return out

        for fill in fills:
            try:
                ex = fill.execution
                if ex.side != "BOT":
                    continue
                key = (ex.acctNumber, fill.contract.symbol)
                ts = ex.time
                # Strip tz so it slots into a naive DB column cleanly.
                if ts is not None and ts.tzinfo is not None:
                    ts = ts.replace(tzinfo=None)
                if key not in out or (ts and ts < out[key]):
                    out[key] = ts
            except Exception:
                continue
        return out


def _safe_decimal(value) -> Optional[Decimal]:
    """Convert any number to Decimal, returning None for None, NaN, or
    IBKR's -1 sentinel value used to signal unavailable data."""
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if f != f:  # NaN
        return None
    if f == -1.0:
        return None
    return Decimal(str(f))


def _is_nan(value) -> bool:
    try:
        return value != value  # NaN trick
    except Exception:
        return False


def fetch_positions_safe() -> List[IBPosition]:
    """Convenience wrapper used by the scheduler. Connects, fetches, disconnects."""
    client = IBKRClient()
    try:
        client.connect()
        return client.fetch_positions()
    finally:
        client.disconnect()

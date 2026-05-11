"""Pydantic schemas for request and response validation."""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PositionRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_id: str
    symbol: str
    exchange: Optional[str] = None
    currency: Optional[str] = None
    quantity: Decimal
    avg_price: Decimal
    market_price: Optional[Decimal] = None
    market_value: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None
    pnl_percent: Optional[Decimal] = None
    asset_class: Optional[str] = None
    bought_at: Optional[datetime] = None
    previous_close: Optional[Decimal] = None
    day_change_pct: Optional[Decimal] = None
    day_change_dollar: Optional[Decimal] = None
    last_updated: datetime
    first_seen: datetime
    holding_days: Optional[int] = None

    # joined metadata
    tag: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    company_name: Optional[str] = None
    eps_guidance: Optional[str] = None
    notes: Optional[str] = None
    next_earnings_date: Optional[date] = None
    earnings_reported: bool = False
    exchange_override: Optional[str] = None


class PortfolioSummary(BaseModel):
    total_market_value: Decimal
    total_cost_basis: Decimal
    total_unrealized_pnl: Decimal
    total_return_pct: Decimal
    position_count: int
    win_count: int
    loss_count: int
    win_rate_pct: Decimal
    top_performer_symbol: Optional[str] = None
    top_performer_pnl_pct: Optional[Decimal] = None
    worst_performer_symbol: Optional[str] = None
    worst_performer_pnl_pct: Optional[Decimal] = None
    last_synced_at: Optional[datetime] = None


class HistoryPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    snapshot_at: datetime
    market_price: Optional[Decimal] = None
    market_value: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None
    pnl_percent: Optional[Decimal] = None


class MetadataUpdate(BaseModel):
    tag: Optional[str] = Field(default=None, max_length=8)
    sector: Optional[str] = Field(default=None, max_length=64)
    eps_guidance: Optional[str] = Field(default=None, max_length=32)
    notes: Optional[str] = None
    next_earnings_date: Optional[date] = None
    earnings_reported: Optional[bool] = None
    exchange_override: Optional[str] = Field(default=None, max_length=16)


class MetadataOut(MetadataUpdate):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    updated_at: datetime


class SyncResult(BaseModel):
    success: bool
    accounts_synced: int
    positions_synced: int
    errors: List[str] = []
    duration_ms: int


class HealthResponse(BaseModel):
    status: str
    database: str
    ibkr: str

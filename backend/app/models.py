"""SQLAlchemy ORM models. Mirrors init_db.sql."""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Position(Base):
    __tablename__ = "positions"
    __table_args__ = (UniqueConstraint("account_id", "symbol", name="uq_positions_account_symbol"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[str] = mapped_column(String(32), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    exchange: Mapped[Optional[str]] = mapped_column(String(32))
    currency: Mapped[Optional[str]] = mapped_column(String(8))
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    avg_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    market_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    market_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    unrealized_pnl: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    pnl_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    asset_class: Mapped[Optional[str]] = mapped_column(String(16))
    bought_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    previous_close: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    first_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PositionHistory(Base):
    __tablename__ = "position_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    account_id: Mapped[str] = mapped_column(String(32), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    avg_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    market_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    market_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    unrealized_pnl: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    pnl_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    previous_close: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))


class Metadata(Base):
    __tablename__ = "metadata"

    symbol: Mapped[str] = mapped_column(String(32), primary_key=True)
    tag: Mapped[Optional[str]] = mapped_column(String(8))
    sector: Mapped[Optional[str]] = mapped_column(String(64))
    industry: Mapped[Optional[str]] = mapped_column(String(64))
    company_name: Mapped[Optional[str]] = mapped_column(Text)
    eps_guidance: Mapped[Optional[str]] = mapped_column(String(32))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    next_earnings_date: Mapped[Optional[date]] = mapped_column(Date)
    earnings_reported: Mapped[bool] = mapped_column(Boolean, default=False)
    exchange_override: Mapped[Optional[str]] = mapped_column(String(16))
    enriched_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    account_id: Mapped[str] = mapped_column(String(32), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    executed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ibkr_exec_id: Mapped[Optional[str]] = mapped_column(String(64), unique=True)

"""Positions endpoint with metadata join and holding period calculation."""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Metadata, Position
from app.schemas import PositionRow

router = APIRouter(prefix="/api/positions", tags=["positions"])


@router.get("", response_model=List[PositionRow])
def list_positions(db: Session = Depends(get_db)) -> List[PositionRow]:
    rows = db.execute(
        select(Position, Metadata).outerjoin(Metadata, Metadata.symbol == Position.symbol)
    ).all()

    out: List[PositionRow] = []
    now = datetime.utcnow()
    for position, meta in rows:
        holding_days = (now - position.first_seen).days if position.first_seen else None

        # Daily P&L = today vs yesterday's close. Skip if either field is
        # missing or zero, otherwise compute pct and dollar values.
        day_change_pct: Optional[Decimal] = None
        day_change_dollar: Optional[Decimal] = None
        if (
            position.market_price is not None
            and position.previous_close is not None
            and position.previous_close > 0
        ):
            diff = Decimal(position.market_price) - Decimal(position.previous_close)
            day_change_pct = diff / Decimal(position.previous_close) * Decimal(100)
            day_change_dollar = diff * Decimal(position.quantity or 0)
        out.append(
            PositionRow(
                account_id=position.account_id,
                symbol=position.symbol,
                exchange=position.exchange,
                currency=position.currency,
                quantity=position.quantity,
                avg_price=position.avg_price,
                market_price=position.market_price,
                market_value=position.market_value,
                unrealized_pnl=position.unrealized_pnl,
                pnl_percent=position.pnl_percent,
                asset_class=position.asset_class,
                bought_at=position.bought_at,
                previous_close=position.previous_close,
                day_change_pct=day_change_pct,
                day_change_dollar=day_change_dollar,
                last_updated=position.last_updated,
                first_seen=position.first_seen,
                holding_days=holding_days,
                tag=meta.tag if meta else None,
                sector=meta.sector if meta else None,
                industry=meta.industry if meta else None,
                company_name=meta.company_name if meta else None,
                eps_guidance=meta.eps_guidance if meta else None,
                notes=meta.notes if meta else None,
                next_earnings_date=meta.next_earnings_date if meta else None,
                earnings_reported=meta.earnings_reported if meta else False,
                exchange_override=meta.exchange_override if meta else None,
            )
        )
    # Sort by pnl_percent desc to put winners on top by default.
    out.sort(key=lambda r: r.pnl_percent or 0, reverse=True)
    return out

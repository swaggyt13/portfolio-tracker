"""Portfolio level aggregations."""
from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Position
from app.schemas import PortfolioSummary


def compute_summary(db: Session) -> PortfolioSummary:
    rows: List[Position] = db.execute(select(Position)).scalars().all()

    if not rows:
        return PortfolioSummary(
            total_market_value=Decimal(0),
            total_cost_basis=Decimal(0),
            total_unrealized_pnl=Decimal(0),
            total_return_pct=Decimal(0),
            position_count=0,
            win_count=0,
            loss_count=0,
            win_rate_pct=Decimal(0),
        )

    total_mv = Decimal(0)
    total_cb = Decimal(0)
    total_pnl = Decimal(0)
    wins = 0
    losses = 0
    top_sym: Optional[str] = None
    top_pct: Optional[Decimal] = None
    worst_sym: Optional[str] = None
    worst_pct: Optional[Decimal] = None
    last_updated = None

    for r in rows:
        cost = (r.avg_price or Decimal(0)) * (r.quantity or Decimal(0))
        mv = r.market_value if r.market_value is not None else cost
        pnl = r.unrealized_pnl if r.unrealized_pnl is not None else Decimal(0)
        total_cb += cost
        total_mv += mv
        total_pnl += pnl

        if r.pnl_percent is not None:
            if r.pnl_percent > 0:
                wins += 1
            elif r.pnl_percent < 0:
                losses += 1
            if top_pct is None or r.pnl_percent > top_pct:
                top_pct = r.pnl_percent
                top_sym = r.symbol
            if worst_pct is None or r.pnl_percent < worst_pct:
                worst_pct = r.pnl_percent
                worst_sym = r.symbol

        if last_updated is None or (r.last_updated and r.last_updated > last_updated):
            last_updated = r.last_updated

    decided = wins + losses
    win_rate = (Decimal(wins) / Decimal(decided) * Decimal(100)) if decided else Decimal(0)
    total_return_pct = (total_pnl / total_cb * Decimal(100)) if total_cb else Decimal(0)

    return PortfolioSummary(
        total_market_value=total_mv,
        total_cost_basis=total_cb,
        total_unrealized_pnl=total_pnl,
        total_return_pct=total_return_pct,
        position_count=len(rows),
        win_count=wins,
        loss_count=losses,
        win_rate_pct=win_rate,
        top_performer_symbol=top_sym,
        top_performer_pnl_pct=top_pct,
        worst_performer_symbol=worst_sym,
        worst_performer_pnl_pct=worst_pct,
        last_synced_at=last_updated,
    )

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import PositionHistory
from app.schemas import HistoryPoint

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("/{symbol}", response_model=List[HistoryPoint])
def history_for_symbol(
    symbol: str,
    limit: int = Query(default=500, ge=1, le=5000),
    db: Session = Depends(get_db),
) -> List[HistoryPoint]:
    rows = (
        db.execute(
            select(PositionHistory)
            .where(PositionHistory.symbol == symbol.upper())
            .order_by(PositionHistory.snapshot_at.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )
    # Return chronological order so charts render left to right.
    return list(reversed(rows))

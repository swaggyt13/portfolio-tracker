"""Manual sync and enrichment triggers."""
import asyncio

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import SyncResult
from app.services.enrichment import enrich_current_positions
from app.services.sync import run_sync

router = APIRouter(prefix="/api/sync", tags=["sync"])


@router.post("", response_model=SyncResult)
async def trigger_sync() -> SyncResult:
    # ib_insync uses asyncio internally; run in a thread to keep our loop clean.
    return await asyncio.to_thread(run_sync)


@router.post("/enrich")
async def trigger_enrichment(db: Session = Depends(get_db)):
    """Force a yfinance enrichment of every current position.
    Useful after adding a new ticker or when EPS guidance looks stale.
    """
    count = await asyncio.to_thread(enrich_current_positions, db)
    return {"refreshed": count}

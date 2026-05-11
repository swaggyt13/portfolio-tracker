"""Manual annotation layer: tag, notes, earnings date, exchange override."""
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Metadata
from app.schemas import MetadataOut, MetadataUpdate

router = APIRouter(prefix="/api/metadata", tags=["metadata"])


@router.get("", response_model=List[MetadataOut])
def list_metadata(db: Session = Depends(get_db)) -> List[MetadataOut]:
    return db.execute(select(Metadata)).scalars().all()


@router.get("/{symbol}", response_model=MetadataOut)
def get_metadata(symbol: str, db: Session = Depends(get_db)) -> MetadataOut:
    record = db.get(Metadata, symbol.upper())
    if not record:
        raise HTTPException(status_code=404, detail="Metadata not found")
    return record


@router.put("/{symbol}", response_model=MetadataOut)
def upsert_metadata(
    symbol: str,
    payload: MetadataUpdate,
    db: Session = Depends(get_db),
) -> MetadataOut:
    symbol = symbol.upper()
    record = db.get(Metadata, symbol)
    if record is None:
        record = Metadata(symbol=symbol)
        db.add(record)

    if payload.tag is not None:
        record.tag = payload.tag.upper() or None
    if payload.sector is not None:
        record.sector = payload.sector or None
    if payload.eps_guidance is not None:
        record.eps_guidance = payload.eps_guidance or None
    if payload.notes is not None:
        record.notes = payload.notes
    if payload.next_earnings_date is not None:
        record.next_earnings_date = payload.next_earnings_date
    if payload.earnings_reported is not None:
        record.earnings_reported = payload.earnings_reported
    if payload.exchange_override is not None:
        record.exchange_override = payload.exchange_override.upper() or None
    record.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(record)
    return record

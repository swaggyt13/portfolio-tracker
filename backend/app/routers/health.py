from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.ibkr.client import IBKRClient
from app.schemas import HealthResponse

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"error: {exc}"

    ibkr_status = "ok"
    try:
        client = IBKRClient()
        client.connect()
        client.disconnect()
    except Exception as exc:
        ibkr_status = f"error: {exc}"

    return HealthResponse(
        status="ok" if db_status == "ok" and ibkr_status == "ok" else "degraded",
        database=db_status,
        ibkr=ibkr_status,
    )

"""APScheduler job that calls the sync service on a fixed interval.

We use the BackgroundScheduler so it lives alongside the FastAPI loop without
hijacking it. The sync function itself is synchronous and connects to IBKR
inline, which keeps the event loop free for HTTP traffic.
"""
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.services.sync import run_sync

logger = logging.getLogger(__name__)


def build_scheduler() -> BackgroundScheduler:
    settings = get_settings()
    scheduler = BackgroundScheduler(daemon=True, timezone="UTC")
    scheduler.add_job(
        _safe_sync,
        trigger=IntervalTrigger(minutes=settings.sync_interval_minutes),
        id="ibkr_sync",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    return scheduler


def _safe_sync() -> None:
    try:
        result = run_sync()
        logger.info(
            "Scheduled sync done: positions=%d errors=%s duration_ms=%d",
            result.positions_synced,
            result.errors,
            result.duration_ms,
        )
    except Exception:
        logger.exception("Scheduled sync raised")

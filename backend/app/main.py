"""FastAPI entrypoint. Wires routers, CORS, scheduler, and startup tasks."""
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import Base, engine
from app.routers import health, history, metadata, portfolio, positions, sync
from app.scheduler import build_scheduler
from app.services.sync import run_sync

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("portfolio")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    # Make sure tables exist. In production we use Alembic; for local dev
    # this avoids a separate step.
    Base.metadata.create_all(bind=engine)

    scheduler = build_scheduler()
    scheduler.start()
    logger.info("Scheduler started (interval=%dm)", settings.sync_interval_minutes)

    if settings.sync_on_startup:
        try:
            import asyncio

            asyncio.create_task(asyncio.to_thread(run_sync))
            logger.info("Initial sync queued")
        except Exception:
            logger.exception("Initial sync failed to queue")

    try:
        yield
    finally:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Portfolio Tracker",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(positions.router)
    app.include_router(portfolio.router)
    app.include_router(history.router)
    app.include_router(metadata.router)
    app.include_router(sync.router)
    app.include_router(health.router)

    # Serve the built frontend (npm run build) at the root path so the user
    # only needs one URL to open the dashboard. If the dist folder is not
    # present yet, skip mounting and rely on the Vite dev server.
    project_root = Path(__file__).resolve().parents[2]
    frontend_dist = project_root / "frontend" / "dist"
    if frontend_dist.is_dir():
        assets_dir = frontend_dist / "assets"
        if assets_dir.is_dir():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

        @app.get("/")
        def root_index():
            return FileResponse(str(frontend_dist / "index.html"))

        @app.get("/{path:path}")
        def spa_fallback(path: str):
            # Never shadow API paths or FastAPI's own docs/openapi handlers,
            # otherwise POST /api/... gets a misleading 405 because Starlette
            # sees a GET registered for the path.
            if path.startswith("api/") or path in ("docs", "redoc", "openapi.json"):
                from fastapi import HTTPException
                raise HTTPException(status_code=404)
            # Serve any asset file directly, otherwise return index.html so
            # client side routing keeps working.
            candidate = frontend_dist / path
            if candidate.is_file():
                return FileResponse(str(candidate))
            return FileResponse(str(frontend_dist / "index.html"))

    return app


app = create_app()

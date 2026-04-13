"""FastAPI entry point for station-excel-fetcher service."""

from __future__ import annotations

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text

from .config import config
from .scheduler.excel_fetch_scheduler import ExcelFetchScheduler

# ── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s %(levelname)-8s %(name)-25s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(config.SERVICE_NAME)

# ── Scheduler (lifecycle-managed) ──────────────────────────────────────────────

_scheduler: AsyncIOScheduler | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scheduler

    logger.info(f"Starting {config.SERVICE_NAME}...")

    # Create DB table if not exists
    try:
        from .infrastructure.persistence.database import engine
        from .infrastructure.persistence.models import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("[STARTUP] DB tables ensured")
    except Exception as exc:
        logger.warning(f"[STARTUP] Table creation failed (may already exist): {exc}")

    # Run startup fetch if configured
    if config.FETCH_ON_STARTUP:
        logger.info("[STARTUP] FETCH_ON_STARTUP=true — running initial fetch")
        scheduler = ExcelFetchScheduler()
        try:
            await scheduler.trigger_manual_fetch()
        except Exception as exc:
            logger.error(f"[STARTUP] Initial fetch failed: {exc}")

    # Start daily scheduler
    _scheduler = ExcelFetchScheduler()
    _scheduler.start()

    yield

    # Shutdown
    if _scheduler:
        _scheduler.stop()
    logger.info(f"{config.SERVICE_NAME} stopped")


app = FastAPI(
    title=config.SERVICE_NAME,
    description="Fetch EnviSoft air quality data → Excel → MySQL",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schemas ──────────────────────────────────────────────────────────────────

class ManualFetchRequest(BaseModel):
    from_date: str | None = None
    to_date: str | None = None


class ManualFetchResponse(BaseModel):
    status: str
    from_date: str
    to_date: str
    message: str | None = None


class HealthResponse(BaseModel):
    service: str
    status: str
    stations_count: int
    last_fetch: str | None = None


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    # Check MySQL connectivity
    db_ok = False
    try:
        from .infrastructure.persistence.database import engine
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception as exc:
        logger.warning(f"DB health check failed: {exc}")

    # Get last fetch info
    last_fetch = None
    try:
        from .infrastructure.persistence.reading_repository import ReadingRepository
        repo = ReadingRepository()
        # Find most recent record
        yesterday = (datetime.utcnow().date() - timedelta(days=1)).strftime("%Y-%m-%d")
        count = await repo.count_by_date_range(
            from_date=datetime.fromisoformat(f"{yesterday}T00:00:00"),
            to_date=datetime.fromisoformat(f"{yesterday}T23:59:59"),
        )
        if count > 0:
            last_fetch = yesterday
    except Exception:
        pass

    return HealthResponse(
        service=config.SERVICE_NAME,
        status="healthy" if db_ok else "degraded",
        stations_count=len(config.TARGET_STATIONS),
        last_fetch=last_fetch,
    )


@app.post("/fetch", response_model=ManualFetchResponse)
async def trigger_fetch(req: ManualFetchRequest):
    """Trigger an on-demand data fetch.

    If from_date/to_date are not provided, fetches yesterday's data.
    """
    if config.FETCH_ON_STARTUP:
        # Scheduler already running
        pass

    scheduler = ExcelFetchScheduler()
    yesterday = (datetime.utcnow().date() - timedelta(days=1)).strftime("%Y-%m-%d")
    from_d = req.from_date or yesterday
    to_d = req.to_date or yesterday

    logger.info(f"[API] Manual fetch: {from_d} → {to_d}")

    try:
        result = await scheduler.trigger_manual_fetch(
            from_date=from_d,
            to_date=to_d,
        )
    except Exception as exc:
        logger.exception("[API] Manual fetch failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

    if result["status"] == "ok":
        return ManualFetchResponse(
            status="ok",
            from_date=from_d,
            to_date=to_d,
            message="Fetch completed successfully",
        )
    else:
        return ManualFetchResponse(
            status="error",
            from_date=from_d,
            to_date=to_d,
            message=result.get("message", "Unknown error"),
        )


@app.get("/stations")
async def list_stations():
    """List configured target stations."""
    return {
        "count": len(config.TARGET_STATIONS),
        "stations": config.TARGET_STATIONS,
    }


@app.get("/records")
async def get_records(
    from_date: str | None = None,
    to_date: str | None = None,
    station_id: str | None = None,
    limit: int = 100,
):
    """Query stored readings (for debugging/verification)."""
    from datetime import datetime as dt

    try:
        from .infrastructure.persistence.database import AsyncSessionLocal
        from .infrastructure.persistence.models import EnvisoftHourlyReadingModel
        from sqlalchemy import and_, select, text

        async with AsyncSessionLocal() as session:
            query = select(EnvisoftHourlyReadingModel).order_by(
                EnvisoftHourlyReadingModel.measured_at.desc()
            )

            filters = []
            if from_date:
                filters.append(
                    EnvisoftHourlyReadingModel.measured_at >= dt.fromisoformat(f"{from_date}T00:00:00")
                )
            if to_date:
                filters.append(
                    EnvisoftHourlyReadingModel.measured_at <= dt.fromisoformat(f"{to_date}T23:59:59")
                )
            if station_id:
                filters.append(
                    EnvisoftHourlyReadingModel.station_id == station_id
                )

            if filters:
                query = query.where(and_(*filters))

            query = query.limit(limit)

            result = await session.execute(query)
            rows = result.scalars().all()

        return {
            "count": len(rows),
            "records": [
                {
                    "station_id": r.station_id,
                    "station_name": r.station_name,
                    "measured_at": r.measured_at.isoformat() if r.measured_at else None,
                    "pm25": r.pm25,
                    "pm10": r.pm10,
                    "no2": r.no2,
                    "so2": r.so2,
                    "co": r.co,
                    "o3": r.o3,
                    "aqi": r.aqi,
                    "temperature": r.temperature,
                    "humidity": r.humidity,
                    "wind_speed": r.wind_speed,
                    "wind_direction": r.wind_direction,
                }
                for r in rows
            ],
        }
    except Exception as exc:
        logger.exception("Failed to query records")
        raise HTTPException(status_code=500, detail=str(exc))


# ── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=config.SERVICE_PORT,
        reload=False,
        log_level=config.LOG_LEVEL.lower(),
    )

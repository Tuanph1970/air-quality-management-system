"""FastAPI routes for station ingestion service."""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter()


def get_ingestion_service():
    """Get station ingestion service instance.

    This is a placeholder - in production, use dependency injection
    with proper service initialization.
    """
    from src.core.config import config
    from src.infrastructure.external.station_api_client import StationAPIClient
    from src.infrastructure.persistence.models import get_session
    from src.infrastructure.persistence.station_repository_impl import StationRepositoryImpl
    from src.application.station_ingestion_service import StationIngestionService

    session = get_session(config.DATABASE_URL)
    repository = StationRepositoryImpl(session)
    api_client = StationAPIClient()
    return StationIngestionService(repository, api_client)


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@router.get("/stations", response_model=List[Dict[str, Any]])
async def get_stations(
    service=Depends(get_ingestion_service),
):
    """Get all monitoring stations.

    Returns list of all stations with their basic information.
    """
    try:
        stations = await service.get_stations_with_latest_reading()
        return stations
    except Exception as e:
        logger.error(f"Error getting stations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stations/{station_code}", response_model=Dict[str, Any])
async def get_station(
    station_code: str,
    service=Depends(get_ingestion_service),
):
    """Get a specific station by code.

    Args:
        station_code: Station code (e.g., "LSOS_KHIKHO")
    """
    try:
        stations = await service.get_stations_with_latest_reading()
        station = next((s for s in stations if s["station_code"] == station_code), None)

        if not station:
            raise HTTPException(status_code=404, detail="Station not found")

        return station
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting station: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stations/{station_code}/readings", response_model=List[Dict[str, Any]])
async def get_station_readings(
    station_code: str,
    from_time: Optional[str] = Query(None, description="Start time (ISO format)"),
    to_time: Optional[str] = Query(None, description="End time (ISO format)"),
    service=Depends(get_ingestion_service),
):
    """Get readings for a specific station.

    Args:
        station_code: Station code
        from_time: Start time in ISO format (defaults to 24 hours ago)
        to_time: End time in ISO format (defaults to now)
    """
    try:
        # Parse time range
        if from_time:
            from_dt = datetime.fromisoformat(from_time.replace("Z", "+00:00"))
        else:
            from_dt = datetime.utcnow() - timedelta(hours=24)

        if to_time:
            to_dt = datetime.fromisoformat(to_time.replace("Z", "+00:00"))
        else:
            to_dt = datetime.utcnow()

        # Get readings
        repository = service.repository
        readings = await repository.get_readings_by_station(station_code, from_dt, to_dt)

        return [
            {
                "id": r.id,
                "station_code": r.station_code,
                "reading_time": r.reading_time.isoformat(),
                "aqi": r.aqi,
                "pm25": r.pm25,
                "pm10": r.pm10,
                "co": r.co,
                "so2": r.so2,
                "no2": r.no2,
                "o3": r.o3,
                "temperature": r.temperature,
                "humidity": r.humidity,
            }
            for r in readings
        ]
    except Exception as e:
        logger.error(f"Error getting readings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/readings/timeseries", response_model=List[Dict[str, Any]])
async def get_all_readings_timeseries(
    from_time: Optional[str] = Query(None, description="Start time (ISO format)"),
    to_time: Optional[str] = Query(None, description="End time (ISO format)"),
    service=Depends(get_ingestion_service),
):
    """Get readings for all stations (for time series chart).

    Args:
        from_time: Start time in ISO format (defaults to 24 hours ago)
        to_time: End time in ISO format (defaults to now)
    """
    try:
        # Parse time range
        if from_time:
            from_dt = datetime.fromisoformat(from_time.replace("Z", "+00:00"))
        else:
            from_dt = datetime.utcnow() - timedelta(hours=24)

        if to_time:
            to_dt = datetime.fromisoformat(to_time.replace("Z", "+00:00"))
        else:
            to_dt = datetime.utcnow()

        # Get readings
        repository = service.repository
        readings = await repository.get_readings_all_stations(from_dt, to_dt)

        return [
            {
                "id": r.id,
                "station_code": r.station_code,
                "reading_time": r.reading_time.isoformat(),
                "aqi": r.aqi,
                "pm25": r.pm25,
                "pm10": r.pm10,
                "co": r.co,
                "so2": r.so2,
                "no2": r.no2,
                "o3": r.o3,
                "temperature": r.temperature,
                "humidity": r.humidity,
            }
            for r in readings
        ]
    except Exception as e:
        logger.error(f"Error getting timeseries readings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/stations", response_model=Dict[str, Any])
async def sync_stations(service=Depends(get_ingestion_service)):
    """Manually trigger station synchronization."""
    try:
        total, new = await service.sync_stations()
        return {"success": True, "total_stations": total, "new_stations": new}
    except Exception as e:
        logger.error(f"Error syncing stations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/aqi", response_model=Dict[str, Any])
async def sync_aqi_data(
    hours: int = Query(24, description="Number of hours to sync"),
    service=Depends(get_ingestion_service),
):
    """Manually trigger AQI data synchronization.

    Args:
        hours: Number of hours to sync back from now
    """
    try:
        from_time = datetime.utcnow() - timedelta(hours=hours)
        count = await service.sync_aqi_data(from_time=from_time)
        return {"success": True, "readings_synced": count}
    except Exception as e:
        logger.error(f"Error syncing AQI data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

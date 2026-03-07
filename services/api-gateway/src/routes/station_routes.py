"""Station service routes — proxy requests to station-service."""
from __future__ import annotations

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from ..utils.service_client import ServiceClient
from ..config import settings

router = APIRouter(prefix="/api/v1/stations", tags=["stations"])


@router.get("")
async def list_stations(request: Request):
    """List all air quality stations."""
    client = ServiceClient(settings.STATION_SERVICE_URL)
    return await client.forward_request(request)


@router.post("")
async def create_station(request: Request):
    """Create a new air quality station."""
    client = ServiceClient(settings.STATION_SERVICE_URL)
    return await client.forward_request(request)


@router.get("/{station_id:path}")
async def get_station(request: Request, station_id: str):
    """Get station by ID or code."""
    client = ServiceClient(settings.STATION_SERVICE_URL)
    return await client.forward_request(request, f"/api/v1/stations/{station_id}")


@router.put("/{station_id:path}")
async def update_station(request: Request, station_id: str):
    """Update station."""
    client = ServiceClient(settings.STATION_SERVICE_URL)
    return await client.forward_request(request, f"/api/v1/stations/{station_id}")


@router.delete("/{station_id:path}")
async def delete_station(request: Request, station_id: str):
    """Delete station."""
    client = ServiceClient(settings.STATION_SERVICE_URL)
    return await client.forward_request(request, f"/api/v1/stations/{station_id}")


@router.post("/{station_id:path}/configure-api")
async def configure_station_api(request: Request, station_id: str):
    """Configure station API endpoint."""
    client = ServiceClient(settings.STATION_SERVICE_URL)
    return await client.forward_request(request, f"/api/v1/stations/{station_id}/configure-api")


@router.post("/{station_id:path}/activate")
async def activate_station(request: Request, station_id: str):
    """Activate station."""
    client = ServiceClient(settings.STATION_SERVICE_URL)
    return await client.forward_request(request, f"/api/v1/stations/{station_id}/activate")


@router.post("/{station_id:path}/deactivate")
async def deactivate_station(request: Request, station_id: str):
    """Deactivate station."""
    client = ServiceClient(settings.STATION_SERVICE_URL)
    return await client.forward_request(request, f"/api/v1/stations/{station_id}/deactivate")


@router.post("/{station_id:path}/record-readings")
async def record_station_readings(request: Request, station_id: str):
    """Record station readings."""
    client = ServiceClient(settings.STATION_SERVICE_URL)
    return await client.forward_request(request, f"/api/v1/stations/{station_id}/record-readings")


@router.get("/{station_id:path}/readings")
async def get_station_readings(request: Request, station_id: str):
    """Get station readings."""
    client = ServiceClient(settings.STATION_SERVICE_URL)
    return await client.forward_request(request, f"/api/v1/stations/{station_id}/readings")


@router.get("/{station_id:path}/readings/latest")
async def get_latest_station_readings(request: Request, station_id: str):
    """Get latest station readings."""
    client = ServiceClient(settings.STATION_SERVICE_URL)
    return await client.forward_request(request, f"/api/v1/stations/{station_id}/readings/latest")


@router.get("/nearby")
async def find_nearby_stations(request: Request):
    """Find nearby stations."""
    client = ServiceClient(settings.STATION_SERVICE_URL)
    return await client.forward_request(request, "/api/v1/stations/nearby")

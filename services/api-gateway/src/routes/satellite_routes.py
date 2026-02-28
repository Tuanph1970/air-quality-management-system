"""API Gateway routes for Remote Sensing Service.

Proxies requests to the remote-sensing-service for satellite data,
data sources, and Excel import endpoints.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from fastapi.responses import JSONResponse

from ..config import settings
from ..utils.service_client import ServiceClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/satellite", tags=["satellite"])

client = ServiceClient(
    base_url=settings.REMOTE_SENSING_SERVICE_URL,
    service_name="remote-sensing-service",
)


# =============================================================================
# Satellite Data Endpoints
# =============================================================================


@router.get("/data")
async def get_satellite_data(request: Request):
    """Get satellite data with optional filters."""
    response = await client.get(
        "/api/v1/satellite/data",
        params=dict(request.query_params),
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.get("/data/latest")
async def get_latest_satellite_data(request: Request):
    """Get the latest satellite data."""
    response = await client.get(
        "/api/v1/satellite/data/latest",
        params=dict(request.query_params),
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.get("/data/{data_id}")
async def get_satellite_data_by_id(data_id: str):
    """Get satellite data by ID."""
    response = await client.get(f"/api/v1/satellite/data/{data_id}")
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.post("/data/fetch")
async def trigger_satellite_fetch(request: Request):
    """Trigger a satellite data fetch."""
    body = await request.json()
    response = await client.post("/api/v1/satellite/data/fetch", json=body)
    return JSONResponse(content=response.json(), status_code=response.status_code)


# =============================================================================
# Data Sources Endpoints
# =============================================================================


@router.get("/sources")
async def list_data_sources():
    """List all configured satellite data sources."""
    response = await client.get("/api/v1/satellite/sources")
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.get("/sources/{source_id}")
async def get_data_source(source_id: str):
    """Get data source details."""
    response = await client.get(f"/api/v1/satellite/sources/{source_id}")
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.post("/sources/{source_id}/toggle")
async def toggle_data_source(source_id: str, request: Request):
    """Enable or disable a data source."""
    body = await request.json()
    response = await client.post(
        f"/api/v1/satellite/sources/{source_id}/toggle",
        json=body,
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


# =============================================================================
# Excel Import Endpoint
# =============================================================================


@router.post("/import/excel")
async def import_excel(file: UploadFile = File(...)):
    """Import satellite data from an Excel file.

    Forwards the uploaded file to remote-sensing-service for processing.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    content_type = (
        file.content_type
        or "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    file_content = await file.read()
    response = await client.post_file(
        "/api/v1/satellite/import/excel",
        file_content=file_content,
        filename=file.filename,
        content_type=content_type,
        field_name="file",
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


# =============================================================================
# Satellite Health / Status
# =============================================================================


@router.get("/health")
async def satellite_service_health():
    """Check remote sensing service health."""
    try:
        response = await client.get("/health")
        return JSONResponse(content=response.json(), status_code=response.status_code)
    except Exception as e:
        logger.warning("Remote sensing service health check failed: %s", e)
        return JSONResponse(
            content={"status": "unavailable", "error": str(e)},
            status_code=503,
        )

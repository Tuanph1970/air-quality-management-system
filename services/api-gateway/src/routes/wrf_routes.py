"""API Gateway routes for WRF Service.

Proxies requests to the wrf-service for weather forecasting and WRF model simulation.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from ..config import settings
from ..utils.service_client import ServiceClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/wrf", tags=["wrf"])

client = ServiceClient(
    base_url=settings.WRF_SERVICE_URL,
    service_name="wrf-service",
)


# =============================================================================
# WRF Simulation Endpoints
# =============================================================================


@router.get("/simulations")
async def list_simulations(request: Request):
    """List all WRF simulations with optional filtering."""
    response = await client.get(
        "/api/v1/wrf/simulations",
        params=dict(request.query_params),
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.get("/simulations/{simulation_id}")
async def get_simulation(simulation_id: str):
    """Get details of a specific simulation."""
    response = await client.get(f"/api/v1/wrf/simulations/{simulation_id}")
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.post("/simulations")
async def create_simulation(request: Request):
    """Create a new WRF simulation."""
    body = await request.json()
    response = await client.post("/api/v1/wrf/simulations", json=body)
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.post("/simulations/{simulation_id}/start")
async def start_simulation(simulation_id: str):
    """Start a WRF simulation."""
    response = await client.post(f"/api/v1/wrf/simulations/{simulation_id}/start")
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.post("/simulations/{simulation_id}/cancel")
async def cancel_simulation(simulation_id: str):
    """Cancel a running simulation."""
    response = await client.post(f"/api/v1/wrf/simulations/{simulation_id}/cancel")
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.delete("/simulations/{simulation_id}")
async def delete_simulation(simulation_id: str):
    """Delete a simulation."""
    response = await client.delete(f"/api/v1/wrf/simulations/{simulation_id}")
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.get("/simulations/{simulation_id}/status")
async def get_simulation_status(simulation_id: str):
    """Get current status of a simulation."""
    response = await client.get(f"/api/v1/wrf/simulations/{simulation_id}/status")
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.get("/simulations/{simulation_id}/forecast/{variable}")
async def get_forecast_data(simulation_id: str, variable: str, request: Request):
    """Get forecast data for a specific variable."""
    response = await client.get(
        f"/api/v1/wrf/simulations/{simulation_id}/forecast/{variable}",
        params=dict(request.query_params),
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


# =============================================================================
# WRF Configuration Endpoints
# =============================================================================


@router.get("/recommend-config")
async def get_recommended_config(request: Request):
    """Get recommended WRF configuration for a region."""
    response = await client.get(
        "/api/v1/wrf/recommend-config",
        params=dict(request.query_params),
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


# =============================================================================
# WRF Health Check
# =============================================================================


@router.get("/health")
async def wrf_service_health():
    """Check WRF service health."""
    try:
        response = await client.get("/health")
        return JSONResponse(content=response.json(), status_code=response.status_code)
    except Exception as e:
        logger.warning("WRF service health check failed: %s", e)
        return JSONResponse(
            content={"status": "unavailable", "error": str(e)},
            status_code=503,
        )

"""FastAPI routes for WRF Service."""
import logging
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import APIRouter, Depends, FastAPI, Query
from fastapi.responses import JSONResponse

from ...config import settings
from ...infrastructure.persistence.database import get_db_manager
from .dependencies import get_wrf_controller
from .schemas import (
    WRFSimulationCreateSchema,
    WRFSimulationDetailSchema,
    WRFSimulationListSchema,
    WRFStatusSchema,
    WRFRecommendedConfigSchema,
    WRFForecastDataSchema,
    APIResponseSchema,
)
from .wrf_controller import WRFController

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    logger.info("Starting %s...", settings.SERVICE_NAME)
    try:
        db_mgr = get_db_manager(settings.DATABASE_URL)
        await db_mgr.create_tables()
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error("Database initialization failed: %s", e)
        raise
    yield
    logger.info("Shutting down %s...", settings.SERVICE_NAME)


router = APIRouter(prefix="/api/v1/wrf", tags=["WRF Simulations"])


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "port": settings.SERVICE_PORT,
    }


@router.post("/simulations", response_model=WRFSimulationDetailSchema)
async def create_simulation(
    schema: WRFSimulationCreateSchema,
    controller: WRFController = Depends(get_wrf_controller),
):
    """Create a new WRF simulation."""
    return await controller.create_simulation(schema)


@router.get("/simulations", response_model=WRFSimulationListSchema)
async def list_simulations(
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return"),
    controller: WRFController = Depends(get_wrf_controller),
):
    """List all WRF simulations with optional filtering."""
    return await controller.list_simulations(status=status, skip=skip, limit=limit)


@router.get("/simulations/{simulation_id}", response_model=WRFSimulationDetailSchema)
async def get_simulation(
    simulation_id: str,
    controller: WRFController = Depends(get_wrf_controller),
):
    """Get details of a specific simulation."""
    return await controller.get_simulation(simulation_id)


@router.post("/simulations/{simulation_id}/start", response_model=APIResponseSchema)
async def start_simulation(
    simulation_id: str,
    controller: WRFController = Depends(get_wrf_controller),
):
    """Start a WRF simulation."""
    return await controller.start_simulation(simulation_id)


@router.post("/simulations/{simulation_id}/cancel", response_model=APIResponseSchema)
async def cancel_simulation(
    simulation_id: str,
    controller: WRFController = Depends(get_wrf_controller),
):
    """Cancel a running simulation."""
    return await controller.cancel_simulation(simulation_id)


@router.delete("/simulations/{simulation_id}", response_model=APIResponseSchema)
async def delete_simulation(
    simulation_id: str,
    controller: WRFController = Depends(get_wrf_controller),
):
    """Delete a simulation."""
    return await controller.delete_simulation(simulation_id)


@router.get("/simulations/{simulation_id}/status", response_model=WRFStatusSchema)
async def get_simulation_status(
    simulation_id: str,
    controller: WRFController = Depends(get_wrf_controller),
):
    """Get current status of a simulation."""
    return await controller.get_status(simulation_id)


@router.get("/recommend-config", response_model=WRFRecommendedConfigSchema)
async def recommend_config(
    center_lat: float = Query(..., description="Center latitude of region"),
    center_lon: float = Query(..., description="Center longitude of region"),
    region_radius_km: float = Query(..., description="Radius of region in km"),
    available_memory_gb: float = Query(
        16.0, description="Available memory in GB"
    ),
    max_runtime_hours: float = Query(4.0, description="Max runtime in hours"),
    controller: WRFController = Depends(get_wrf_controller),
):
    """Get recommended WRF configuration for a region."""
    return await controller.get_recommended_config(
        center_lat=center_lat,
        center_lon=center_lon,
        region_radius_km=region_radius_km,
        available_memory_gb=available_memory_gb,
        max_runtime_hours=max_runtime_hours,
    )


@router.get(
    "/simulations/{simulation_id}/forecast/{variable}",
    response_model=WRFForecastDataSchema,
)
async def get_forecast_data(
    simulation_id: str,
    variable: str,
    level: str = Query("surface", description="Atmospheric level"),
    controller: WRFController = Depends(get_wrf_controller),
):
    """Get forecast data for a specific variable."""
    return await controller.get_forecast_data(
        simulation_id=simulation_id,
        variable=variable,
        level=level,
    )


app = FastAPI(
    title="WRF Service",
    description="WRF Weather Simulation Service for Air Quality Management",
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(router)

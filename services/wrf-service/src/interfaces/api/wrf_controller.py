"""WRF Controller - handles API requests."""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException

from ...application.services.wrf_application_service import (
    WRFApplicationService,
)
from ...domain.entities.wrf_simulation import SimulationStatus
from .schemas import (
    WRFSimulationCreateSchema,
    WRFSimulationDetailSchema,
    WRFSimulationListSchema,
    WRFSimulationResponseSchema,
    WRFStatusSchema,
    WRFRecommendedConfigSchema,
    WRFForecastDataSchema,
    APIResponseSchema,
)

logger = logging.getLogger(__name__)


class WRFController:
    """Controller for WRF simulation API endpoints."""

    def __init__(self, application_service: WRFApplicationService):
        self.service = application_service

    async def create_simulation(
        self, schema: WRFSimulationCreateSchema
    ) -> WRFSimulationDetailSchema:
        """Create a new WRF simulation."""
        try:
            simulation = await self.service.create_simulation(
                name=schema.name,
                north=schema.north,
                south=schema.south,
                east=schema.east,
                west=schema.west,
                horizontal_resolution_km=schema.horizontal_resolution_km,
                vertical_levels=schema.vertical_levels,
                simulation_hours=schema.simulation_hours,
                output_interval_hours=schema.output_interval_hours,
                start_date=schema.start_date,
                physics_options={
                    "microphysics": schema.microphysics,
                    "longwave_radiation": schema.longwave_radiation,
                    "shortwave_radiation": schema.shortwave_radiation,
                    "land_surface": schema.land_surface,
                    "pbl_scheme": schema.pbl_scheme,
                },
            )

            return WRFSimulationDetailSchema(
                id=str(simulation.id),
                name=simulation.name,
                status=simulation.status.value,
                progress_percent=simulation.progress_percent,
                error_message=simulation.error_message,
                config=simulation.config.to_dict(),
                output_file_path=simulation.output_file_path,
                wrf_output_files=simulation.wrf_output_files,
                created_at=simulation.created_at,
                started_at=simulation.started_at,
                completed_at=simulation.completed_at,
                elapsed_seconds=simulation.elapsed_seconds,
                estimated_remaining_seconds=simulation.estimated_remaining_seconds,
            )

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.exception(f"Failed to create simulation: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to create simulation: {str(e)}"
            )

    async def get_simulation(self, simulation_id: str) -> WRFSimulationDetailSchema:
        """Get a simulation by ID."""
        try:
            sim_uuid = UUID(simulation_id)
            simulation = await self.service.get_simulation(sim_uuid)

            if not simulation:
                raise HTTPException(
                    status_code=404, detail=f"Simulation {simulation_id} not found"
                )

            return WRFSimulationDetailSchema(
                id=str(simulation.id),
                name=simulation.name,
                status=simulation.status.value,
                progress_percent=simulation.progress_percent,
                error_message=simulation.error_message,
                config=simulation.config.to_dict(),
                output_file_path=simulation.output_file_path,
                wrf_output_files=simulation.wrf_output_files,
                created_at=simulation.created_at,
                started_at=simulation.started_at,
                completed_at=simulation.completed_at,
                elapsed_seconds=simulation.elapsed_seconds,
                estimated_remaining_seconds=simulation.estimated_remaining_seconds,
            )

        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid simulation ID: {simulation_id}"
            )

    async def list_simulations(
        self,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> WRFSimulationListSchema:
        """List simulations with optional filtering."""
        try:
            filter_status = None
            if status:
                try:
                    filter_status = SimulationStatus(status)
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid status: {status}. Valid values: {[s.value for s in SimulationStatus]}",
                    )

            simulations = await self.service.list_simulations(
                status=filter_status,
                skip=skip,
                limit=limit,
            )

            # Get total count (simplified - would need separate count query)
            total = len(simulations)

            return WRFSimulationListSchema(
                simulations=[
                    WRFSimulationResponseSchema(
                        id=str(s.id),
                        name=s.name,
                        status=s.status.value,
                        progress_percent=s.progress_percent,
                        error_message=s.error_message,
                        created_at=s.created_at,
                        started_at=s.started_at,
                        completed_at=s.completed_at,
                        elapsed_seconds=s.elapsed_seconds,
                        estimated_remaining_seconds=s.estimated_remaining_seconds,
                    )
                    for s in simulations
                ],
                total=total,
                skip=skip,
                limit=limit,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Failed to list simulations: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to list simulations: {str(e)}"
            )

    async def start_simulation(self, simulation_id: str) -> APIResponseSchema:
        """Start a WRF simulation."""
        try:
            sim_uuid = UUID(simulation_id)
            await self.service.start_simulation(sim_uuid)

            return APIResponseSchema(
                success=True,
                message=f"Simulation {simulation_id} started successfully",
                data={"simulation_id": simulation_id},
            )

        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid simulation ID: {simulation_id}"
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.exception(f"Failed to start simulation: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to start simulation: {str(e)}"
            )

    async def cancel_simulation(self, simulation_id: str) -> APIResponseSchema:
        """Cancel a running simulation."""
        try:
            sim_uuid = UUID(simulation_id)
            await self.service.cancel_simulation(sim_uuid)

            return APIResponseSchema(
                success=True,
                message=f"Simulation {simulation_id} cancelled successfully",
                data={"simulation_id": simulation_id},
            )

        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid simulation ID: {simulation_id}"
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.exception(f"Failed to cancel simulation: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to cancel simulation: {str(e)}"
            )

    async def delete_simulation(self, simulation_id: str) -> APIResponseSchema:
        """Delete a simulation."""
        try:
            sim_uuid = UUID(simulation_id)
            success = await self.service.delete_simulation(sim_uuid)

            if not success:
                raise HTTPException(
                    status_code=404, detail=f"Simulation {simulation_id} not found"
                )

            return APIResponseSchema(
                success=True,
                message=f"Simulation {simulation_id} deleted successfully",
            )

        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid simulation ID: {simulation_id}"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Failed to delete simulation: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to delete simulation: {str(e)}"
            )

    async def get_status(self, simulation_id: str) -> WRFStatusSchema:
        """Get simulation status."""
        try:
            sim_uuid = UUID(simulation_id)
            status = await self.service.get_simulation_status(sim_uuid)

            if not status:
                raise HTTPException(
                    status_code=404, detail=f"Simulation {simulation_id} not found"
                )

            return WRFStatusSchema(**status)

        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid simulation ID: {simulation_id}"
            )

    async def get_recommended_config(
        self,
        center_lat: float,
        center_lon: float,
        region_radius_km: float,
        available_memory_gb: float = 16.0,
        max_runtime_hours: float = 4.0,
    ) -> WRFRecommendedConfigSchema:
        """Get recommended configuration for a region."""
        try:
            result = await self.service.get_recommended_config(
                center_lat=center_lat,
                center_lon=center_lon,
                region_radius_km=region_radius_km,
                available_memory_gb=available_memory_gb,
                max_runtime_hours=max_runtime_hours,
            )

            return WRFRecommendedConfigSchema(**result)

        except Exception as e:
            logger.exception(f"Failed to get recommended config: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to get recommended config: {str(e)}"
            )

    async def get_forecast_data(
        self,
        simulation_id: str,
        variable: str,
        level: str = "surface",
    ) -> WRFForecastDataSchema:
        """Get forecast data for a variable."""
        try:
            sim_uuid = UUID(simulation_id)
            # This would be implemented to actually read data from WRF output
            data = {
                "simulation_id": simulation_id,
                "variable": variable,
                "level": level,
                "bounding_box": {},
                "time_range": {"start": None, "end": None},
                "output_files": [],
            }

            return WRFForecastDataSchema(**data)

        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid simulation ID: {simulation_id}"
            )
        except Exception as e:
            logger.exception(f"Failed to get forecast data: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to get forecast data: {str(e)}"
            )

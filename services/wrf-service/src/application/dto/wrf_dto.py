"""Data Transfer Objects for WRF Service."""
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID


@dataclass
class WRFSimulationDTO:
    """DTO for WRF simulation summary."""

    id: UUID
    name: str
    status: str
    progress_percent: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "status": self.status,
            "progress_percent": self.progress_percent,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class WRFSimulationDetailDTO:
    """DTO for detailed WRF simulation information."""

    id: UUID
    name: str
    status: str
    progress_percent: int
    error_message: Optional[str]
    config: Dict[str, Any]
    output_file_path: Optional[str]
    wrf_output_files: List[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    elapsed_seconds: Optional[float]
    estimated_remaining_seconds: Optional[float]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "status": self.status,
            "progress_percent": self.progress_percent,
            "error_message": self.error_message,
            "config": self.config,
            "output_file_path": self.output_file_path,
            "wrf_output_files": self.wrf_output_files,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "elapsed_seconds": self.elapsed_seconds,
            "estimated_remaining_seconds": self.estimated_remaining_seconds,
        }


@dataclass
class WRFSimulationCreateRequest:
    """Request DTO for creating a WRF simulation."""

    name: str
    north: float
    south: float
    east: float
    west: float
    horizontal_resolution_km: float
    vertical_levels: int
    simulation_hours: int
    output_interval_hours: int = 1
    start_date: Optional[str] = None
    microphysics: str = "wsmd6"
    longwave_radiation: str = "rrtm"
    shortwave_radiation: str = "dudhia"
    land_surface: str = "noah"
    pbl_scheme: str = "ysu"


@dataclass
class WRFSimulationResponse:
    """Response DTO for WRF simulation operations."""

    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
        }

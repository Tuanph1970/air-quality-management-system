"""Satellite data Data Transfer Object."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from ...domain.entities.satellite_data import SatelliteData


@dataclass
class SatelliteDataDTO:
    """Read-only projection of a SatelliteData entity."""

    id: UUID
    source: str
    data_type: str
    observation_time: datetime
    fetch_time: datetime
    bbox: Dict
    grid_cell_count: int
    average_value: float
    quality_flag: str
    metadata: Dict = field(default_factory=dict)
    file_path: Optional[str] = None

    @classmethod
    def from_entity(cls, entity: SatelliteData) -> "SatelliteDataDTO":
        return cls(
            id=entity.id,
            source=entity.source.value,
            data_type=entity.data_type,
            observation_time=entity.observation_time,
            fetch_time=entity.fetch_time,
            bbox=entity.bbox.to_dict(),
            grid_cell_count=len(entity.grid_cells),
            average_value=entity.get_average_value(),
            quality_flag=entity.quality_flag.value,
            metadata=entity.metadata,
            file_path=entity.file_path,
        )

    def to_dict(self) -> Dict:
        return {
            "id": str(self.id),
            "source": self.source,
            "data_type": self.data_type,
            "observation_time": self.observation_time.isoformat(),
            "fetch_time": self.fetch_time.isoformat(),
            "bbox": self.bbox,
            "grid_cell_count": self.grid_cell_count,
            "average_value": round(self.average_value, 4),
            "quality_flag": self.quality_flag,
            "metadata": self.metadata,
        }

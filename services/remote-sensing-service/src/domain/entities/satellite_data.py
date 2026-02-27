"""Satellite observation data entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from ..value_objects.satellite_source import SatelliteSource
from ..value_objects.geo_polygon import GeoPolygon
from ..value_objects.grid_cell import GridCell
from ..value_objects.quality_flag import QualityFlag


@dataclass
class SatelliteData:
    """Entity: Satellite observation data."""

    id: UUID
    source: SatelliteSource
    data_type: str  # 'AOD', 'NO2', 'PM25', 'PM10', 'O3', 'SO2', 'CO'
    observation_time: datetime
    fetch_time: datetime
    bbox: GeoPolygon
    grid_cells: List[GridCell]
    quality_flag: QualityFlag
    metadata: Dict = field(default_factory=dict)
    file_path: Optional[str] = None

    _events: list = field(default_factory=list, repr=False)

    @classmethod
    def create(
        cls,
        source: SatelliteSource,
        data_type: str,
        observation_time: datetime,
        bbox: GeoPolygon,
        grid_cells: List[GridCell],
        quality_flag: QualityFlag = QualityFlag.GOOD,
        metadata: Dict = None,
    ) -> "SatelliteData":
        """Factory method to create SatelliteData."""
        from shared.events.satellite_events import SatelliteDataFetched

        data = cls(
            id=uuid4(),
            source=source,
            data_type=data_type,
            observation_time=observation_time,
            fetch_time=datetime.utcnow(),
            bbox=bbox,
            grid_cells=grid_cells,
            quality_flag=quality_flag,
            metadata=metadata or {},
        )

        data._events.append(
            SatelliteDataFetched(
                event_id=uuid4(),
                occurred_at=datetime.utcnow(),
                source=source.value,
                data_type=data_type,
                observation_time=observation_time,
                bbox=bbox.to_dict(),
                record_count=len(grid_cells),
            )
        )

        return data

    def get_value_at(self, lat: float, lon: float) -> Optional[float]:
        """Get interpolated value at specific location."""
        nearest = min(
            self.grid_cells,
            key=lambda c: ((c.lat - lat) ** 2 + (c.lon - lon) ** 2) ** 0.5,
            default=None,
        )
        return nearest.value if nearest else None

    def get_average_value(self) -> float:
        """Get average value across all grid cells."""
        if not self.grid_cells:
            return 0.0
        return sum(c.value for c in self.grid_cells) / len(self.grid_cells)

    def collect_events(self) -> list:
        """Collect and clear domain events."""
        events = self._events.copy()
        self._events.clear()
        return events

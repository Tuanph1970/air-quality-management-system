"""Fused data entity — combines sensor, satellite, and Excel data."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from ..value_objects.geo_polygon import GeoPolygon


@dataclass
class FusedDataPoint:
    """A single fused data point combining multiple sources."""

    lat: float
    lon: float
    fused_value: float
    confidence: float
    sources: List[str]  # e.g. ['sensor', 'satellite', 'excel']
    source_values: Dict[str, float] = field(default_factory=dict)


@dataclass
class FusedData:
    """Entity: Result of data fusion across multiple sources."""

    id: UUID
    sources_used: List[str]
    bbox: GeoPolygon
    time_range_start: datetime
    time_range_end: datetime
    data_points: List[FusedDataPoint]
    average_confidence: float
    created_at: datetime
    pollutant: str = ""
    metadata: Dict = field(default_factory=dict)

    _events: list = field(default_factory=list, repr=False)

    @classmethod
    def create(
        cls,
        sources_used: List[str],
        bbox: GeoPolygon,
        time_range_start: datetime,
        time_range_end: datetime,
        data_points: List[FusedDataPoint],
        pollutant: str = "",
        metadata: Dict = None,
    ) -> "FusedData":
        """Factory method to create FusedData."""
        from shared.events.fusion_events import DataFusionCompleted

        avg_confidence = (
            sum(dp.confidence for dp in data_points) / len(data_points)
            if data_points
            else 0.0
        )

        fused = cls(
            id=uuid4(),
            sources_used=sources_used,
            bbox=bbox,
            time_range_start=time_range_start,
            time_range_end=time_range_end,
            data_points=data_points,
            average_confidence=avg_confidence,
            created_at=datetime.utcnow(),
            pollutant=pollutant,
            metadata=metadata or {},
        )

        fused._events.append(
            DataFusionCompleted(
                event_id=uuid4(),
                occurred_at=datetime.utcnow(),
                fusion_id=fused.id,
                sources_used=sources_used,
                location_count=len(data_points),
                time_range_start=time_range_start,
                time_range_end=time_range_end,
                average_confidence=avg_confidence,
            )
        )

        return fused

    def get_value_at(self, lat: float, lon: float) -> Optional[FusedDataPoint]:
        """Get nearest fused data point to a location."""
        nearest = min(
            self.data_points,
            key=lambda dp: ((dp.lat - lat) ** 2 + (dp.lon - lon) ** 2) ** 0.5,
            default=None,
        )
        return nearest

    def collect_events(self) -> list:
        """Collect and clear domain events."""
        events = self._events.copy()
        self._events.clear()
        return events

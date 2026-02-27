"""Fused data Data Transfer Object."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from ...domain.entities.fused_data import FusedData, FusedDataPoint


@dataclass
class FusedDataPointDTO:
    """Read-only projection of a single fused data point."""

    lat: float
    lon: float
    fused_value: float
    confidence: float
    sources: List[str]
    source_values: Dict[str, float] = field(default_factory=dict)


@dataclass
class FusedDataDTO:
    """Read-only projection of a FusedData entity."""

    id: UUID
    sources_used: List[str]
    bbox: Dict
    time_range_start: datetime
    time_range_end: datetime
    data_point_count: int
    average_confidence: float
    pollutant: str
    created_at: datetime
    data_points: List[FusedDataPointDTO] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

    @classmethod
    def from_entity(
        cls, entity: FusedData, include_points: bool = False
    ) -> "FusedDataDTO":
        points: List[FusedDataPointDTO] = []
        if include_points:
            points = [
                FusedDataPointDTO(
                    lat=dp.lat,
                    lon=dp.lon,
                    fused_value=dp.fused_value,
                    confidence=dp.confidence,
                    sources=dp.sources[:],
                    source_values=dict(dp.source_values),
                )
                for dp in entity.data_points
            ]

        return cls(
            id=entity.id,
            sources_used=entity.sources_used[:],
            bbox=entity.bbox.to_dict(),
            time_range_start=entity.time_range_start,
            time_range_end=entity.time_range_end,
            data_point_count=len(entity.data_points),
            average_confidence=entity.average_confidence,
            pollutant=entity.pollutant,
            created_at=entity.created_at,
            data_points=points,
            metadata=entity.metadata,
        )

    def to_dict(self) -> Dict:
        result = {
            "id": str(self.id),
            "sources_used": self.sources_used,
            "bbox": self.bbox,
            "time_range_start": self.time_range_start.isoformat(),
            "time_range_end": self.time_range_end.isoformat(),
            "data_point_count": self.data_point_count,
            "average_confidence": round(self.average_confidence, 4),
            "pollutant": self.pollutant,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }
        if self.data_points:
            result["data_points"] = [
                {
                    "lat": dp.lat,
                    "lon": dp.lon,
                    "fused_value": round(dp.fused_value, 4),
                    "confidence": round(dp.confidence, 4),
                    "sources": dp.sources,
                    "source_values": {
                        k: round(v, 4) for k, v in dp.source_values.items()
                    },
                }
                for dp in self.data_points
            ]
        return result

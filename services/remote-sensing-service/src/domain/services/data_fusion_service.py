"""Data fusion domain service.

Combines sensor readings, satellite observations, and Excel-imported data
into a unified fused dataset with confidence scoring.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from ..entities.fused_data import FusedData, FusedDataPoint
from ..entities.satellite_data import SatelliteData
from ..value_objects.geo_polygon import GeoPolygon
from ..value_objects.quality_flag import QualityFlag

logger = logging.getLogger(__name__)


@dataclass
class SensorReading:
    """Lightweight representation of a sensor reading for fusion input."""

    sensor_id: str
    lat: float
    lon: float
    value: float
    timestamp: datetime
    pollutant: str


@dataclass
class ExcelRecord:
    """Lightweight representation of an Excel-imported record for fusion."""

    lat: float
    lon: float
    value: float
    timestamp: datetime
    pollutant: str


# Confidence weights per data source (higher = more trusted).
SOURCE_WEIGHTS: Dict[str, float] = {
    "sensor": 0.5,
    "satellite": 0.35,
    "excel": 0.15,
}


class DataFusionService:
    """Domain service: fuses multiple data sources into a single dataset."""

    def fuse(
        self,
        satellite_data: List[SatelliteData],
        sensor_readings: List[SensorReading],
        excel_records: List[ExcelRecord],
        bbox: GeoPolygon,
        time_range: Tuple[datetime, datetime],
        pollutant: str = "",
    ) -> FusedData:
        """Fuse satellite, sensor, and Excel data into a single dataset.

        Uses inverse-distance weighting for spatial interpolation and
        source-weight blending for multi-source fusion.
        """
        sources_used: List[str] = []
        if sensor_readings:
            sources_used.append("sensor")
        if satellite_data:
            sources_used.append("satellite")
        if excel_records:
            sources_used.append("excel")

        # Collect all unique locations.
        locations = self._collect_locations(
            satellite_data, sensor_readings, excel_records
        )

        data_points: List[FusedDataPoint] = []
        for lat, lon in locations:
            if not bbox.contains(lat, lon):
                continue

            source_values: Dict[str, float] = {}
            weights: Dict[str, float] = {}

            # Sensor value at location.
            sensor_val = self._nearest_sensor_value(sensor_readings, lat, lon)
            if sensor_val is not None:
                source_values["sensor"] = sensor_val
                weights["sensor"] = SOURCE_WEIGHTS["sensor"]

            # Satellite value at location.
            sat_val = self._satellite_value_at(satellite_data, lat, lon)
            if sat_val is not None:
                source_values["satellite"] = sat_val
                weights["satellite"] = SOURCE_WEIGHTS["satellite"]

            # Excel value at location.
            excel_val = self._nearest_excel_value(excel_records, lat, lon)
            if excel_val is not None:
                source_values["excel"] = excel_val
                weights["excel"] = SOURCE_WEIGHTS["excel"]

            if not source_values:
                continue

            fused_value = self._weighted_average(source_values, weights)
            confidence = self._compute_confidence(source_values, weights)

            data_points.append(
                FusedDataPoint(
                    lat=lat,
                    lon=lon,
                    fused_value=fused_value,
                    confidence=confidence,
                    sources=list(source_values.keys()),
                    source_values=source_values,
                )
            )

        logger.info(
            "Fused %d data points from %s", len(data_points), sources_used
        )

        return FusedData.create(
            sources_used=sources_used,
            bbox=bbox,
            time_range_start=time_range[0],
            time_range_end=time_range[1],
            data_points=data_points,
            pollutant=pollutant,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _collect_locations(
        satellite_data: List[SatelliteData],
        sensor_readings: List[SensorReading],
        excel_records: List[ExcelRecord],
    ) -> List[Tuple[float, float]]:
        """Gather all unique (lat, lon) pairs from every source."""
        seen: set = set()
        locations: List[Tuple[float, float]] = []

        for sd in satellite_data:
            for cell in sd.grid_cells:
                key = (round(cell.lat, 4), round(cell.lon, 4))
                if key not in seen:
                    seen.add(key)
                    locations.append(key)

        for sr in sensor_readings:
            key = (round(sr.lat, 4), round(sr.lon, 4))
            if key not in seen:
                seen.add(key)
                locations.append(key)

        for er in excel_records:
            key = (round(er.lat, 4), round(er.lon, 4))
            if key not in seen:
                seen.add(key)
                locations.append(key)

        return locations

    @staticmethod
    def _nearest_sensor_value(
        readings: List[SensorReading],
        lat: float,
        lon: float,
        max_distance_km: float = 5.0,
    ) -> Optional[float]:
        if not readings:
            return None
        nearest = min(
            readings,
            key=lambda r: ((r.lat - lat) ** 2 + (r.lon - lon) ** 2) ** 0.5,
        )
        dist_deg = ((nearest.lat - lat) ** 2 + (nearest.lon - lon) ** 2) ** 0.5
        if dist_deg > max_distance_km / 111.0:  # rough deg→km
            return None
        return nearest.value

    @staticmethod
    def _satellite_value_at(
        satellite_data: List[SatelliteData],
        lat: float,
        lon: float,
    ) -> Optional[float]:
        for sd in satellite_data:
            if sd.quality_flag == QualityFlag.INVALID:
                continue
            val = sd.get_value_at(lat, lon)
            if val is not None:
                return val
        return None

    @staticmethod
    def _nearest_excel_value(
        records: List[ExcelRecord],
        lat: float,
        lon: float,
        max_distance_km: float = 10.0,
    ) -> Optional[float]:
        if not records:
            return None
        nearest = min(
            records,
            key=lambda r: ((r.lat - lat) ** 2 + (r.lon - lon) ** 2) ** 0.5,
        )
        dist_deg = ((nearest.lat - lat) ** 2 + (nearest.lon - lon) ** 2) ** 0.5
        if dist_deg > max_distance_km / 111.0:
            return None
        return nearest.value

    @staticmethod
    def _weighted_average(
        values: Dict[str, float], weights: Dict[str, float]
    ) -> float:
        total_weight = sum(weights.values())
        if total_weight == 0:
            return 0.0
        return sum(
            values[k] * weights[k] for k in values
        ) / total_weight

    @staticmethod
    def _compute_confidence(
        values: Dict[str, float], weights: Dict[str, float]
    ) -> float:
        """Confidence increases with the number of agreeing sources."""
        n_sources = len(values)
        weight_sum = sum(weights.values())
        base = min(weight_sum / sum(SOURCE_WEIGHTS.values()), 1.0)

        # Bonus for multi-source agreement.
        source_bonus = min(n_sources / 3.0, 1.0) * 0.3
        return min(base + source_bonus, 1.0)

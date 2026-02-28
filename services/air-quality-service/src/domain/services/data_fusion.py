"""Data fusion domain service.

Fuses sensor readings with satellite data to produce calibrated air
quality measurements with confidence scores.

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from ..value_objects.location import Location


@dataclass
class FusedDataPoint:
    """Result of fusing multiple data sources."""

    location: Location
    timestamp: datetime

    # Raw values from each source
    sensor_pm25: Optional[float] = None
    sensor_pm10: Optional[float] = None
    satellite_aod: Optional[float] = None
    satellite_pm25: Optional[float] = None

    # Fused (calibrated) values
    fused_pm25: Optional[float] = None
    fused_pm10: Optional[float] = None
    fused_aqi: Optional[int] = None

    # Quality metrics
    confidence: float = 0.0
    data_sources: List[str] = field(default_factory=list)


class DataFusionService:
    """Domain service for multi-source data fusion.

    Algorithm:
        1. For each sensor, find corresponding satellite grid cell.
        2. Apply calibration model using satellite as reference.
        3. Calculate confidence based on data availability.
        4. Return fused data points.
    """

    def __init__(self, calibration_model: "CalibrationModel"):
        self.calibration_model = calibration_model

    def fuse_data(
        self,
        sensor_readings: List[Dict],
        satellite_data: Dict,
        timestamp: datetime,
    ) -> List[FusedDataPoint]:
        """Fuse sensor readings with satellite data.

        Parameters
        ----------
        sensor_readings:
            List of dicts with keys: latitude, longitude, pm25, pm10,
            temperature, humidity.
        satellite_data:
            Dict with ``grid_cells`` key containing satellite observations.
        timestamp:
            Observation timestamp.

        Returns
        -------
        list[FusedDataPoint]
            Fused data points with calibrated values and confidence.
        """
        fused_points: List[FusedDataPoint] = []

        for reading in sensor_readings:
            lat = reading["latitude"]
            lon = reading["longitude"]

            # Get satellite value at sensor location.
            sat_value = self._get_satellite_value(satellite_data, lat, lon)

            # Prepare features for calibration.
            features = {
                "raw_pm25": reading.get("pm25"),
                "raw_pm10": reading.get("pm10"),
                "temperature": reading.get("temperature"),
                "humidity": reading.get("humidity"),
                "satellite_aod": sat_value,
                "hour": timestamp.hour,
            }

            # Apply calibration with confidence scoring.
            if reading.get("pm25") and sat_value:
                calibrated = self.calibration_model.calibrate(features)
                confidence = 0.9  # High: both sources available
            elif reading.get("pm25"):
                calibrated = {
                    "pm25": reading["pm25"],
                    "pm10": reading.get("pm10"),
                }
                confidence = 0.6  # Medium: sensor only
            elif sat_value:
                calibrated = {"pm25": self._aod_to_pm25(sat_value)}
                confidence = 0.5  # Lower: satellite only
            else:
                continue

            fused_point = FusedDataPoint(
                location=Location(latitude=lat, longitude=lon),
                timestamp=timestamp,
                sensor_pm25=reading.get("pm25"),
                sensor_pm10=reading.get("pm10"),
                satellite_aod=sat_value,
                fused_pm25=calibrated.get("pm25"),
                fused_pm10=calibrated.get("pm10"),
                fused_aqi=self._calculate_aqi(calibrated.get("pm25")),
                confidence=confidence,
                data_sources=self._determine_sources(reading, sat_value),
            )
            fused_points.append(fused_point)

        return fused_points

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _get_satellite_value(
        self, satellite_data: Dict, lat: float, lon: float
    ) -> Optional[float]:
        """Get interpolated satellite value at location (nearest cell)."""
        grid_cells = satellite_data.get("grid_cells", [])
        if not grid_cells:
            return None

        nearest = min(
            grid_cells,
            key=lambda c: ((c["lat"] - lat) ** 2 + (c["lon"] - lon) ** 2) ** 0.5,
        )
        return nearest.get("value")

    def _aod_to_pm25(self, aod: float) -> float:
        """Convert Aerosol Optical Depth to PM2.5 estimate.

        Uses the simplified empirical relationship: PM2.5 ~ AOD x 100.
        """
        return aod * 100

    def _calculate_aqi(self, pm25: Optional[float]) -> Optional[int]:
        """Calculate AQI from PM2.5 using EPA breakpoints (simplified)."""
        if pm25 is None:
            return None
        if pm25 <= 12:
            return int(pm25 * 50 / 12)
        if pm25 <= 35.4:
            return int(50 + (pm25 - 12) * 50 / 23.4)
        if pm25 <= 55.4:
            return int(100 + (pm25 - 35.4) * 50 / 20)
        if pm25 <= 150.4:
            return int(150 + (pm25 - 55.4) * 50 / 95)
        return int(200 + (pm25 - 150.4) * 100 / 100)

    def _determine_sources(
        self, reading: Dict, sat_value: Optional[float]
    ) -> List[str]:
        """List which data sources contributed to this fused point."""
        sources: List[str] = []
        if reading.get("pm25"):
            sources.append("sensor")
        if sat_value:
            sources.append("satellite")
        return sources

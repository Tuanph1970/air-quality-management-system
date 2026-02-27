"""Cross-validation domain service.

Compares sensor readings against satellite observations to detect
anomalous deviations that may indicate sensor malfunction or
environmental events requiring investigation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from ..entities.satellite_data import SatelliteData
from ..value_objects.quality_flag import QualityFlag

logger = logging.getLogger(__name__)

# Default threshold: flag deviations > 50 %.
DEFAULT_DEVIATION_THRESHOLD = 50.0


@dataclass
class ValidationResult:
    """Result of validating a single sensor reading against satellite."""

    sensor_id: UUID
    sensor_value: float
    satellite_value: float
    deviation_percent: float
    pollutant: str
    is_anomalous: bool
    timestamp: datetime


class CrossValidationService:
    """Domain service: cross-validates sensor readings against satellite
    data and flags anomalous deviations."""

    def __init__(
        self, deviation_threshold: float = DEFAULT_DEVIATION_THRESHOLD
    ):
        self.deviation_threshold = deviation_threshold

    def validate_readings(
        self,
        sensor_readings: List[dict],
        satellite_data: List[SatelliteData],
        pollutant: str = "",
    ) -> List[ValidationResult]:
        """Compare each sensor reading against the nearest satellite
        observation and flag those exceeding the deviation threshold.

        ``sensor_readings`` items must contain keys:
        sensor_id, lat, lon, value, timestamp.
        """
        results: List[ValidationResult] = []

        for reading in sensor_readings:
            sat_value = self._find_satellite_value(
                satellite_data,
                reading["lat"],
                reading["lon"],
                reading["timestamp"],
            )
            if sat_value is None:
                continue

            sensor_value = reading["value"]
            deviation = self._deviation_percent(sensor_value, sat_value)
            is_anomalous = abs(deviation) > self.deviation_threshold

            results.append(
                ValidationResult(
                    sensor_id=reading["sensor_id"],
                    sensor_value=sensor_value,
                    satellite_value=sat_value,
                    deviation_percent=deviation,
                    pollutant=pollutant,
                    is_anomalous=is_anomalous,
                    timestamp=reading["timestamp"],
                )
            )

            if is_anomalous:
                logger.warning(
                    "Anomaly detected: sensor=%s deviation=%.1f%% "
                    "sensor_val=%.2f sat_val=%.2f pollutant=%s",
                    reading["sensor_id"],
                    deviation,
                    sensor_value,
                    sat_value,
                    pollutant,
                )

        return results

    def build_alert_events(
        self, anomalies: List[ValidationResult]
    ) -> list:
        """Create CrossValidationAlert domain events for anomalous results."""
        from shared.events.fusion_events import CrossValidationAlert

        events = []
        for a in anomalies:
            if not a.is_anomalous:
                continue
            events.append(
                CrossValidationAlert(
                    event_id=uuid4(),
                    occurred_at=datetime.utcnow(),
                    sensor_id=a.sensor_id,
                    sensor_value=a.sensor_value,
                    satellite_value=a.satellite_value,
                    deviation_percent=a.deviation_percent,
                    pollutant=a.pollutant,
                )
            )
        return events

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _find_satellite_value(
        self,
        satellite_data: List[SatelliteData],
        lat: float,
        lon: float,
        timestamp: datetime,
        max_time_diff_minutes: int = 120,
    ) -> Optional[float]:
        """Find the closest-in-time satellite value at a location."""
        best_val: Optional[float] = None
        best_diff: float = float("inf")

        for sd in satellite_data:
            if sd.quality_flag == QualityFlag.INVALID:
                continue

            diff = abs(
                (sd.observation_time - timestamp).total_seconds()
            ) / 60.0
            if diff > max_time_diff_minutes:
                continue

            val = sd.get_value_at(lat, lon)
            if val is not None and diff < best_diff:
                best_val = val
                best_diff = diff

        return best_val

    @staticmethod
    def _deviation_percent(
        sensor_value: float, satellite_value: float
    ) -> float:
        """Compute percentage deviation: (sensor - satellite) / satellite * 100."""
        if satellite_value == 0:
            return 0.0 if sensor_value == 0 else 100.0
        return (sensor_value - satellite_value) / satellite_value * 100.0

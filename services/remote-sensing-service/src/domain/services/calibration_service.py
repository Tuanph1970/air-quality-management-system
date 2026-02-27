"""Sensor calibration domain service.

Compares sensor readings against satellite observations to compute
calibration offsets and generate updated calibration models.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from ..entities.satellite_data import SatelliteData
from ..value_objects.quality_flag import QualityFlag

logger = logging.getLogger(__name__)


@dataclass
class CalibrationPair:
    """Matched sensor-satellite observation pair."""

    sensor_id: UUID
    sensor_value: float
    satellite_value: float
    timestamp: datetime
    lat: float
    lon: float


@dataclass
class CalibrationResult:
    """Result of a calibration computation."""

    sensor_id: Optional[UUID]  # None = global model
    slope: float
    intercept: float
    r_squared: float
    rmse: float
    training_samples: int
    model_version: str
    computed_at: datetime = field(default_factory=datetime.utcnow)

    def apply(self, raw_value: float) -> float:
        """Apply calibration correction to a raw sensor value."""
        return self.slope * raw_value + self.intercept


class CalibrationService:
    """Domain service: computes sensor calibration models from
    sensor-vs-satellite matched pairs."""

    def compute_calibration(
        self,
        pairs: List[CalibrationPair],
        sensor_id: Optional[UUID] = None,
        model_version: str = "",
    ) -> CalibrationResult:
        """Compute a simple linear regression calibration model.

        y = satellite (reference), x = sensor (to calibrate).
        Returns slope, intercept, R-squared, and RMSE.
        """
        if len(pairs) < 2:
            raise ValueError(
                "Need at least 2 matched pairs for calibration"
            )

        x_vals = [p.sensor_value for p in pairs]
        y_vals = [p.satellite_value for p in pairs]
        n = len(pairs)

        slope, intercept = self._linear_regression(x_vals, y_vals)
        r_squared = self._r_squared(x_vals, y_vals, slope, intercept)
        rmse = self._rmse(x_vals, y_vals, slope, intercept)

        version = model_version or f"v{datetime.utcnow().strftime('%Y%m%d%H%M')}"

        logger.info(
            "Calibration computed: sensor=%s slope=%.4f intercept=%.4f "
            "R²=%.4f RMSE=%.4f samples=%d",
            sensor_id or "global",
            slope,
            intercept,
            r_squared,
            rmse,
            n,
        )

        return CalibrationResult(
            sensor_id=sensor_id,
            slope=slope,
            intercept=intercept,
            r_squared=r_squared,
            rmse=rmse,
            training_samples=n,
            model_version=version,
        )

    def match_pairs(
        self,
        sensor_readings: List[Dict],
        satellite_data: List[SatelliteData],
        max_time_diff_minutes: int = 60,
        max_distance_km: float = 5.0,
    ) -> List[CalibrationPair]:
        """Match sensor readings with nearby satellite observations.

        Finds the closest satellite grid cell within time and distance
        thresholds for each sensor reading.
        """
        pairs: List[CalibrationPair] = []

        for reading in sensor_readings:
            r_lat = reading["lat"]
            r_lon = reading["lon"]
            r_time = reading["timestamp"]
            r_value = reading["value"]
            r_sensor_id = reading["sensor_id"]

            best_match: Optional[Tuple[float, SatelliteData]] = None

            for sd in satellite_data:
                if sd.quality_flag == QualityFlag.INVALID:
                    continue

                time_diff = abs(
                    (sd.observation_time - r_time).total_seconds()
                ) / 60.0
                if time_diff > max_time_diff_minutes:
                    continue

                sat_val = sd.get_value_at(r_lat, r_lon)
                if sat_val is None:
                    continue

                if best_match is None or time_diff < best_match[0]:
                    best_match = (time_diff, sd)

            if best_match is not None:
                sat_val = best_match[1].get_value_at(r_lat, r_lon)
                if sat_val is not None:
                    pairs.append(
                        CalibrationPair(
                            sensor_id=r_sensor_id,
                            sensor_value=r_value,
                            satellite_value=sat_val,
                            timestamp=r_time,
                            lat=r_lat,
                            lon=r_lon,
                        )
                    )

        logger.info(
            "Matched %d calibration pairs from %d readings",
            len(pairs),
            len(sensor_readings),
        )
        return pairs

    # ------------------------------------------------------------------
    # Statistics helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _linear_regression(
        x: List[float], y: List[float]
    ) -> Tuple[float, float]:
        """Simple OLS linear regression returning (slope, intercept)."""
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi ** 2 for xi in x)

        denom = n * sum_x2 - sum_x ** 2
        if denom == 0:
            return 1.0, 0.0

        slope = (n * sum_xy - sum_x * sum_y) / denom
        intercept = (sum_y - slope * sum_x) / n
        return slope, intercept

    @staticmethod
    def _r_squared(
        x: List[float],
        y: List[float],
        slope: float,
        intercept: float,
    ) -> float:
        """Coefficient of determination."""
        y_mean = sum(y) / len(y)
        ss_tot = sum((yi - y_mean) ** 2 for yi in y)
        ss_res = sum(
            (yi - (slope * xi + intercept)) ** 2
            for xi, yi in zip(x, y)
        )
        if ss_tot == 0:
            return 1.0
        return 1.0 - ss_res / ss_tot

    @staticmethod
    def _rmse(
        x: List[float],
        y: List[float],
        slope: float,
        intercept: float,
    ) -> float:
        """Root Mean Square Error."""
        n = len(x)
        mse = sum(
            (yi - (slope * xi + intercept)) ** 2
            for xi, yi in zip(x, y)
        ) / n
        return math.sqrt(mse)

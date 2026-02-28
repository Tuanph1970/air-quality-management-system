"""Cross-validation domain service.

Validates sensor readings against satellite reference data to detect
anomalies and assess sensor health.

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple
from uuid import UUID

import numpy as np


@dataclass
class ValidationResult:
    """Result of cross-validating a sensor against satellite data."""

    sensor_id: UUID
    sample_count: int
    correlation: float  # Pearson correlation coefficient
    bias: float  # Mean bias (sensor - satellite)
    rmse: float  # Root Mean Square Error
    mae: float  # Mean Absolute Error
    is_valid: bool  # Whether sensor passes validation

    @property
    def status(self) -> str:
        """Qualitative assessment of sensor accuracy."""
        if self.correlation > 0.8 and abs(self.bias) < 10:
            return "excellent"
        elif self.correlation > 0.6 and abs(self.bias) < 20:
            return "good"
        elif self.correlation > 0.4:
            return "fair"
        return "poor"


class CrossValidationService:
    """Domain service for sensor vs satellite cross-validation."""

    def __init__(self, deviation_threshold: float = 0.3):
        self.deviation_threshold = deviation_threshold

    def validate_sensor(
        self,
        sensor_id: UUID,
        sensor_values: List[float],
        satellite_values: List[float],
    ) -> ValidationResult:
        """Validate a single sensor against satellite reference.

        Parameters
        ----------
        sensor_id:
            UUID of the sensor being validated.
        sensor_values:
            Sensor readings to validate.
        satellite_values:
            Corresponding satellite reference values.

        Returns
        -------
        ValidationResult
            Statistical comparison with pass/fail determination.
        """
        if (
            len(sensor_values) != len(satellite_values)
            or len(sensor_values) < 3
        ):
            return ValidationResult(
                sensor_id=sensor_id,
                sample_count=len(sensor_values),
                correlation=0.0,
                bias=0.0,
                rmse=0.0,
                mae=0.0,
                is_valid=False,
            )

        sensor_arr = np.array(sensor_values)
        satellite_arr = np.array(satellite_values)

        # Calculate statistical metrics.
        correlation = float(np.corrcoef(sensor_arr, satellite_arr)[0, 1])
        bias = float(np.mean(sensor_arr - satellite_arr))
        rmse = float(np.sqrt(np.mean((sensor_arr - satellite_arr) ** 2)))
        mae = float(np.mean(np.abs(sensor_arr - satellite_arr)))

        # Determine validity.
        sat_mean = float(np.mean(satellite_arr))
        relative_bias = abs(bias) / sat_mean if sat_mean > 0 else 1.0
        is_valid = correlation > 0.5 and relative_bias < self.deviation_threshold

        return ValidationResult(
            sensor_id=sensor_id,
            sample_count=len(sensor_values),
            correlation=correlation,
            bias=bias,
            rmse=rmse,
            mae=mae,
            is_valid=is_valid,
        )

    def detect_anomaly(
        self,
        sensor_value: float,
        satellite_value: float,
    ) -> Tuple[bool, float]:
        """Detect if a single reading is anomalous.

        Parameters
        ----------
        sensor_value:
            Value from the sensor.
        satellite_value:
            Corresponding satellite reference value.

        Returns
        -------
        tuple[bool, float]
            ``(is_anomaly, deviation)`` where deviation is the relative
            difference between sensor and satellite.
        """
        if satellite_value == 0:
            return False, 0.0

        deviation = abs(sensor_value - satellite_value) / satellite_value
        is_anomaly = deviation > self.deviation_threshold

        return is_anomaly, deviation

"""Calibration domain service.

Provides calibration-related business logic that operates across
multiple entities or requires complex computations that don't naturally
belong to a single entity.

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from __future__ import annotations

from typing import Dict

from ..value_objects.air_quality_reading import AirQualityReading
from ..value_objects.calibration_params import CalibrationParams


class CalibrationService:
    """Stateless domain service for sensor calibration operations."""

    @staticmethod
    def apply_calibration(
        raw_reading: AirQualityReading,
        params: CalibrationParams,
    ) -> AirQualityReading:
        """Apply calibration parameters to a raw reading.

        Returns a new ``AirQualityReading`` with corrected values.

        Parameters
        ----------
        raw_reading:
            The uncorrected sensor measurement.
        params:
            Calibration coefficients to apply.
        """
        return AirQualityReading(
            pm25=params.correct_reading("pm25", raw_reading.pm25),
            pm10=params.correct_reading("pm10", raw_reading.pm10),
            co=params.correct_reading("co", raw_reading.co),
            co2=raw_reading.co2,  # CO2 typically not calibrated
            no2=params.correct_reading("no2", raw_reading.no2),
            nox=raw_reading.nox,
            so2=params.correct_reading("so2", raw_reading.so2),
            o3=params.correct_reading("o3", raw_reading.o3),
            temperature=raw_reading.temperature,
            humidity=raw_reading.humidity,
        )

    @staticmethod
    def validate_calibration(params: CalibrationParams) -> Dict[str, str]:
        """Validate calibration parameters and return any warnings.

        Returns a dictionary of pollutant → warning message for any
        parameters that look suspicious (e.g. very low R-squared).
        """
        warnings: Dict[str, str] = {}
        pollutant_fields = ["pm25", "pm10", "co", "no2", "so2", "o3"]

        for pollutant in pollutant_fields:
            cal = getattr(params, pollutant)
            if cal.slope != 1.0 or cal.intercept != 0.0:
                if cal.r_squared < 0.8:
                    warnings[pollutant] = (
                        f"Low R-squared ({cal.r_squared:.2f}) — "
                        f"calibration may be unreliable"
                    )
                if cal.slope < 0.0:
                    warnings[pollutant] = (
                        f"Negative slope ({cal.slope:.2f}) — "
                        f"calibration inverts readings"
                    )

        return warnings

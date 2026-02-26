"""Sensor type classification.

Categorises sensors by their measurement capability and deployment class.
Each type implies different accuracy levels, maintenance schedules, and
supported pollutant ranges.

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from __future__ import annotations

from enum import Enum


class SensorType(str, Enum):
    """Classification of air-quality sensor hardware.

    Types
    -----
    LOW_COST_PM
        Low-cost particulate matter sensor (PM2.5/PM10 only).
        Suitable for dense deployment but lower accuracy.
    REFERENCE_STATION
        Government-grade reference monitoring station.
        High accuracy, full pollutant coverage, expensive.
    MULTI_GAS
        Multi-gas analyser that measures several pollutants
        simultaneously (PM, CO, NO2, SO2, O3).
    """

    LOW_COST_PM = "LOW_COST_PM"
    REFERENCE_STATION = "REFERENCE_STATION"
    MULTI_GAS = "MULTI_GAS"

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    @property
    def supports_gas(self) -> bool:
        """Return ``True`` if the sensor type can measure gaseous pollutants."""
        return self in (self.REFERENCE_STATION, self.MULTI_GAS)

    @property
    def supports_pm(self) -> bool:
        """Return ``True`` if the sensor type can measure particulate matter."""
        return True  # All types support PM

    @property
    def is_reference_grade(self) -> bool:
        """Return ``True`` for government-grade reference stations."""
        return self == self.REFERENCE_STATION

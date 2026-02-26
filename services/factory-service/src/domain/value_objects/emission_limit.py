"""Emission limits value object.

Defines the maximum allowable pollutant concentrations for a factory.
Used by the Factory entity to evaluate whether current readings exceed
regulatory thresholds.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class EmissionLimits:
    """Immutable value object representing regulatory emission thresholds.

    All values are in µg/m³ unless otherwise noted.
    """

    pm25_limit: float = 0.0
    pm10_limit: float = 0.0
    co_limit: float = 0.0
    no2_limit: float = 0.0
    so2_limit: float = 0.0
    o3_limit: float = 0.0

    def __post_init__(self) -> None:
        for field_name in (
            "pm25_limit", "pm10_limit", "co_limit",
            "no2_limit", "so2_limit", "o3_limit",
        ):
            value = getattr(self, field_name)
            if value < 0:
                raise ValueError(f"{field_name} must be non-negative, got {value}")

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------
    @classmethod
    def from_dict(cls, data: Dict) -> EmissionLimits:
        """Create from a dict, silently ignoring unknown keys."""
        known = {k for k in cls.__dataclass_fields__}
        return cls(**{k: float(v) for k, v in data.items() if k in known})

    def to_dict(self) -> Dict[str, float]:
        return {
            "pm25_limit": self.pm25_limit,
            "pm10_limit": self.pm10_limit,
            "co_limit": self.co_limit,
            "no2_limit": self.no2_limit,
            "so2_limit": self.so2_limit,
            "o3_limit": self.o3_limit,
        }

    # ------------------------------------------------------------------
    # Business logic
    # ------------------------------------------------------------------
    def is_exceeded(self, readings: Dict[str, float]) -> bool:
        """Return ``True`` if any reading exceeds its corresponding limit.

        Parameters
        ----------
        readings:
            Mapping of pollutant names to measured concentrations, e.g.
            ``{"pm25": 45.2, "pm10": 80.0, "co": 1.5}``.
            Keys should match the limit field names *without* the ``_limit``
            suffix.
        """
        limit_map: Dict[str, float] = {
            "pm25": self.pm25_limit,
            "pm10": self.pm10_limit,
            "co": self.co_limit,
            "no2": self.no2_limit,
            "so2": self.so2_limit,
            "o3": self.o3_limit,
        }
        for pollutant, measured in readings.items():
            limit = limit_map.get(pollutant, 0.0)
            if limit > 0 and measured > limit:
                return True
        return False

    def exceeded_pollutants(self, readings: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        """Return details of every pollutant that exceeds its limit.

        Returns a dict keyed by pollutant name with ``measured`` and
        ``limit`` values for each breach.
        """
        limit_map: Dict[str, float] = {
            "pm25": self.pm25_limit,
            "pm10": self.pm10_limit,
            "co": self.co_limit,
            "no2": self.no2_limit,
            "so2": self.so2_limit,
            "o3": self.o3_limit,
        }
        breaches: Dict[str, Dict[str, float]] = {}
        for pollutant, measured in readings.items():
            limit = limit_map.get(pollutant, 0.0)
            if limit > 0 and measured > limit:
                breaches[pollutant] = {"measured": measured, "limit": limit}
        return breaches

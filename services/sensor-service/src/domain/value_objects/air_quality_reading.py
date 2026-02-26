"""Air quality reading value object.

Holds a complete snapshot of pollutant concentrations and environmental
parameters from a single measurement.  Immutable once created.

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class AirQualityReading:
    """Immutable snapshot of pollutant concentrations.

    All concentrations are in micrograms per cubic metre (ug/m3) unless
    otherwise noted.  ``co`` is in milligrams per cubic metre (mg/m3).
    """

    # Particulate matter
    pm25: float = 0.0
    pm10: float = 0.0

    # Gaseous pollutants
    co: float = 0.0        # mg/m3
    co2: float = 0.0       # ppm
    no2: float = 0.0       # ug/m3
    nox: float = 0.0       # ug/m3
    so2: float = 0.0       # ug/m3
    o3: float = 0.0        # ug/m3

    # Environmental parameters
    temperature: float = 0.0   # Celsius
    humidity: float = 0.0      # %RH

    def __post_init__(self) -> None:
        if self.humidity < 0.0 or self.humidity > 100.0:
            raise ValueError(
                f"Humidity must be between 0 and 100, got {self.humidity}"
            )

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------
    def to_dict(self) -> Dict[str, float]:
        """Return all measurements as a plain dictionary."""
        return {
            "pm25": self.pm25,
            "pm10": self.pm10,
            "co": self.co,
            "co2": self.co2,
            "no2": self.no2,
            "nox": self.nox,
            "so2": self.so2,
            "o3": self.o3,
            "temperature": self.temperature,
            "humidity": self.humidity,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> AirQualityReading:
        """Create from a dictionary, silently ignoring unknown keys."""
        known = set(cls.__dataclass_fields__)
        return cls(**{k: float(v) for k, v in data.items() if k in known})

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    def pollutant_dict(self) -> Dict[str, float]:
        """Return only the pollutant concentrations (no environmental data)."""
        return {
            "pm25": self.pm25,
            "pm10": self.pm10,
            "co": self.co,
            "no2": self.no2,
            "so2": self.so2,
            "o3": self.o3,
        }

    @property
    def has_particulate_data(self) -> bool:
        """Return ``True`` if PM data is present (non-zero)."""
        return self.pm25 > 0.0 or self.pm10 > 0.0

    @property
    def has_gas_data(self) -> bool:
        """Return ``True`` if any gaseous pollutant data is present."""
        return any(v > 0.0 for v in (self.co, self.no2, self.so2, self.o3))

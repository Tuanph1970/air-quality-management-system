"""Emission limits value object."""
from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class EmissionLimits:
    """Value Object for emission thresholds."""

    pm25_max: float = 0.0
    pm10_max: float = 0.0
    co_max: float = 0.0
    no2_max: float = 0.0
    so2_max: float = 0.0

    @classmethod
    def from_dict(cls, data: Dict) -> "EmissionLimits":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_dict(self) -> Dict:
        return {
            "pm25_max": self.pm25_max,
            "pm10_max": self.pm10_max,
            "co_max": self.co_max,
            "no2_max": self.no2_max,
            "so2_max": self.so2_max,
        }

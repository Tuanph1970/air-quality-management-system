"""Calibration parameters value object.

Stores per-pollutant linear calibration coefficients (slope + intercept)
and an overall R-squared goodness-of-fit metric.  Used to correct raw
sensor readings before AQI calculation.

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class PollutantCalibration:
    """Linear calibration coefficients for a single pollutant.

    Corrected value = ``slope * raw_value + intercept``.
    """

    slope: float = 1.0
    intercept: float = 0.0
    r_squared: float = 0.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.r_squared <= 1.0:
            raise ValueError(
                f"r_squared must be between 0 and 1, got {self.r_squared}"
            )

    def apply(self, raw_value: float) -> float:
        """Apply the linear calibration to a raw reading."""
        return self.slope * raw_value + self.intercept


@dataclass(frozen=True)
class CalibrationParams:
    """Immutable collection of per-pollutant calibration coefficients.

    Each pollutant has its own ``PollutantCalibration`` with slope,
    intercept, and R-squared values.  A global ``offset`` and
    ``scale_factor`` provide a simple fallback when per-pollutant
    coefficients are not available.
    """

    # Global fallback calibration
    offset: float = 0.0
    scale_factor: float = 1.0

    # Per-pollutant calibration
    pm25: PollutantCalibration = field(default_factory=PollutantCalibration)
    pm10: PollutantCalibration = field(default_factory=PollutantCalibration)
    co: PollutantCalibration = field(default_factory=PollutantCalibration)
    no2: PollutantCalibration = field(default_factory=PollutantCalibration)
    so2: PollutantCalibration = field(default_factory=PollutantCalibration)
    o3: PollutantCalibration = field(default_factory=PollutantCalibration)

    def __post_init__(self) -> None:
        if self.scale_factor == 0.0:
            raise ValueError("scale_factor must not be zero")

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------
    @classmethod
    def from_dict(cls, data: Dict) -> CalibrationParams:
        """Create from a dictionary, silently ignoring unknown keys.

        Supports two formats:
        - **Simple**: ``{"offset": 0.5, "scale_factor": 1.02}``
        - **Full**: ``{"pm25": {"slope": 1.1, "intercept": 0.2, "r_squared": 0.98}, ...}``
        """
        pollutant_keys = {"pm25", "pm10", "co", "no2", "so2", "o3"}
        scalar_keys = {"offset", "scale_factor"}

        kwargs: Dict = {}
        for key in scalar_keys:
            if key in data:
                kwargs[key] = float(data[key])

        for key in pollutant_keys:
            if key in data and isinstance(data[key], dict):
                kwargs[key] = PollutantCalibration(**{
                    k: float(v)
                    for k, v in data[key].items()
                    if k in PollutantCalibration.__dataclass_fields__
                })

        return cls(**kwargs)

    def to_dict(self) -> Dict:
        """Serialise to a plain dictionary."""
        return {
            "offset": self.offset,
            "scale_factor": self.scale_factor,
            "pm25": {"slope": self.pm25.slope, "intercept": self.pm25.intercept, "r_squared": self.pm25.r_squared},
            "pm10": {"slope": self.pm10.slope, "intercept": self.pm10.intercept, "r_squared": self.pm10.r_squared},
            "co": {"slope": self.co.slope, "intercept": self.co.intercept, "r_squared": self.co.r_squared},
            "no2": {"slope": self.no2.slope, "intercept": self.no2.intercept, "r_squared": self.no2.r_squared},
            "so2": {"slope": self.so2.slope, "intercept": self.so2.intercept, "r_squared": self.so2.r_squared},
            "o3": {"slope": self.o3.slope, "intercept": self.o3.intercept, "r_squared": self.o3.r_squared},
        }

    # ------------------------------------------------------------------
    # Correction helpers
    # ------------------------------------------------------------------
    def correct_reading(self, pollutant: str, raw_value: float) -> float:
        """Apply calibration to a raw sensor reading.

        Falls back to the global ``offset`` / ``scale_factor`` when no
        per-pollutant calibration is configured (i.e. slope == 1.0 and
        intercept == 0.0).
        """
        cal: PollutantCalibration | None = getattr(self, pollutant, None)
        if cal is not None and (cal.slope != 1.0 or cal.intercept != 0.0):
            return cal.apply(raw_value)
        return self.scale_factor * raw_value + self.offset

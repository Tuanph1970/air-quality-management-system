"""Threshold value object."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Threshold:
    """Value Object for alert thresholds."""

    pollutant: str
    max_value: float
    unit: str = "ug/m3"

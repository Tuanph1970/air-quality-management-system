"""Threshold value object for alert configuration.

Encapsulates the three-tier threshold levels for a single pollutant.
Given a measured value, ``check()`` returns the appropriate ``Severity``
or ``None`` if the value is within acceptable limits.

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .severity import Severity


@dataclass(frozen=True)
class Threshold:
    """Immutable three-tier threshold for a pollutant.

    Invariants:
        0 < warning <= high <= critical

    Parameters
    ----------
    warning:
        Value at or above which a WARNING severity is triggered.
    high:
        Value at or above which a HIGH severity is triggered.
    critical:
        Value at or above which a CRITICAL severity is triggered.
    """

    warning: float
    high: float
    critical: float

    def __post_init__(self) -> None:
        if self.warning <= 0:
            raise ValueError(
                f"Warning threshold must be positive, got {self.warning}"
            )
        if self.high < self.warning:
            raise ValueError(
                f"High threshold ({self.high}) must be >= warning ({self.warning})"
            )
        if self.critical < self.high:
            raise ValueError(
                f"Critical threshold ({self.critical}) must be >= high ({self.high})"
            )

    # ------------------------------------------------------------------
    # Core business logic
    # ------------------------------------------------------------------
    def check(self, value: float) -> Optional[Severity]:
        """Evaluate a measured value against the threshold tiers.

        Returns the highest matched ``Severity``, or ``None`` if the
        value is below the warning level.

        Parameters
        ----------
        value:
            The measured pollutant concentration.
        """
        if value >= self.critical:
            return Severity.CRITICAL
        if value >= self.high:
            return Severity.HIGH
        if value >= self.warning:
            return Severity.WARNING
        return None

    def exceedance_percentage(self, value: float) -> float:
        """Calculate how far *value* exceeds the warning threshold.

        Returns 0.0 if the value is below the warning level.

        Example::

            >>> t = Threshold(warning=50, high=100, critical=150)
            >>> t.exceedance_percentage(75)
            50.0   # 75 is 50 % above the 50 warning limit
        """
        if value <= self.warning:
            return 0.0
        return ((value - self.warning) / self.warning) * 100

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "warning": self.warning,
            "high": self.high,
            "critical": self.critical,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Threshold:
        return cls(
            warning=float(data["warning"]),
            high=float(data["high"]),
            critical=float(data["critical"]),
        )

"""Severity value object for violation classification.

Severity levels follow a three-tier model aligned with environmental
regulatory standards:

- **WARNING** — Pollutant exceeds the permitted limit by a small margin.
  Typically triggers email notification and a monitoring period.
- **HIGH** — Significant exceedance requiring immediate attention.
  Triggers both email and SMS notifications.
- **CRITICAL** — Dangerous exceedance that may warrant factory suspension.
  Triggers all notification channels and may auto-escalate.

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from __future__ import annotations

from enum import Enum


class Severity(str, Enum):
    """Three-tier violation severity classification.

    Inherits from ``str`` so that ``Severity.WARNING == "WARNING"`` is
    ``True`` — convenient for JSON serialization and database storage.
    """

    WARNING = "WARNING"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    # ------------------------------------------------------------------
    # Factory method
    # ------------------------------------------------------------------
    @classmethod
    def from_exceedance(cls, percentage: float) -> Severity:
        """Derive severity from the exceedance percentage over the limit.

        Thresholds::

            exceedance >= 100%  → CRITICAL
            exceedance >=  50%  → HIGH
            exceedance >    0%  → WARNING

        Parameters
        ----------
        percentage:
            The percentage by which the measured value exceeds the
            permitted limit.  E.g. 75.0 means 75 % over the limit.

        Raises
        ------
        ValueError
            If ``percentage`` is not positive.
        """
        if percentage <= 0:
            raise ValueError(
                f"Exceedance percentage must be positive, got {percentage}"
            )

        if percentage >= 100:
            return cls.CRITICAL
        if percentage >= 50:
            return cls.HIGH
        return cls.WARNING

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    @property
    def is_critical(self) -> bool:
        return self == Severity.CRITICAL

    @property
    def should_notify_sms(self) -> bool:
        """HIGH and CRITICAL violations warrant SMS alerts."""
        return self in (Severity.HIGH, Severity.CRITICAL)

    @property
    def numeric_level(self) -> int:
        """Numeric level for comparison (higher = more severe)."""
        return _SEVERITY_ORDER[self]


_SEVERITY_ORDER = {
    Severity.WARNING: 1,
    Severity.HIGH: 2,
    Severity.CRITICAL: 3,
}

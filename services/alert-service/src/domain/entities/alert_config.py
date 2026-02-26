"""Alert configuration entity.

Defines the threshold rules for a specific pollutant.  Each
``AlertConfig`` maps a pollutant to three threshold tiers (warning,
high, critical) and controls which notification channels are active.

The alert-service uses these configs when evaluating incoming sensor
readings — the ``ThresholdChecker`` domain service loads the active
configs and compares reading values against them.

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from ..value_objects.threshold import Threshold


@dataclass
class AlertConfig:
    """Entity representing a pollutant alert configuration.

    Identity is defined by ``id`` (UUID).
    """

    id: UUID
    name: str
    pollutant: str
    warning_threshold: float
    high_threshold: float
    critical_threshold: float
    duration_minutes: int = 0
    is_active: bool = True
    notify_email: bool = True
    notify_sms: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # ------------------------------------------------------------------
    # Factory method
    # ------------------------------------------------------------------
    @classmethod
    def create(
        cls,
        name: str,
        pollutant: str,
        warning_threshold: float,
        high_threshold: float,
        critical_threshold: float,
        duration_minutes: int = 0,
        notify_email: bool = True,
        notify_sms: bool = False,
    ) -> AlertConfig:
        """Create a new alert configuration.

        Validates that the threshold tiers are ordered correctly.

        Parameters
        ----------
        name:
            Human-readable configuration name (e.g. "PM2.5 City Limit").
        pollutant:
            Pollutant code (e.g. "pm25", "pm10", "co", "no2").
        warning_threshold:
            Concentration at or above which a WARNING is raised.
        high_threshold:
            Concentration at or above which a HIGH severity is raised.
        critical_threshold:
            Concentration at or above which a CRITICAL severity is raised.
        duration_minutes:
            How many consecutive minutes the threshold must be exceeded
            before a violation is created.  0 means immediate.
        notify_email:
            Whether to send email notifications.
        notify_sms:
            Whether to send SMS notifications.
        """
        # Validate via Threshold value object (enforces ordering invariant)
        Threshold(
            warning=warning_threshold,
            high=high_threshold,
            critical=critical_threshold,
        )

        if duration_minutes < 0:
            raise ValueError(
                f"Duration minutes must be non-negative, got {duration_minutes}"
            )

        return cls(
            id=uuid4(),
            name=name,
            pollutant=pollutant,
            warning_threshold=warning_threshold,
            high_threshold=high_threshold,
            critical_threshold=critical_threshold,
            duration_minutes=duration_minutes,
            notify_email=notify_email,
            notify_sms=notify_sms,
        )

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    def to_threshold(self) -> Threshold:
        """Build a ``Threshold`` value object from this config."""
        return Threshold(
            warning=self.warning_threshold,
            high=self.high_threshold,
            critical=self.critical_threshold,
        )

    def update(
        self,
        name: Optional[str] = None,
        warning_threshold: Optional[float] = None,
        high_threshold: Optional[float] = None,
        critical_threshold: Optional[float] = None,
        duration_minutes: Optional[int] = None,
        notify_email: Optional[bool] = None,
        notify_sms: Optional[bool] = None,
    ) -> None:
        """Update mutable fields.  Only non-None values are applied."""
        if name is not None:
            self.name = name
        if warning_threshold is not None:
            self.warning_threshold = warning_threshold
        if high_threshold is not None:
            self.high_threshold = high_threshold
        if critical_threshold is not None:
            self.critical_threshold = critical_threshold

        # Re-validate ordering if any threshold changed
        if any(v is not None for v in [warning_threshold, high_threshold, critical_threshold]):
            Threshold(
                warning=self.warning_threshold,
                high=self.high_threshold,
                critical=self.critical_threshold,
            )

        if duration_minutes is not None:
            if duration_minutes < 0:
                raise ValueError(
                    f"Duration minutes must be non-negative, got {duration_minutes}"
                )
            self.duration_minutes = duration_minutes

        if notify_email is not None:
            self.notify_email = notify_email
        if notify_sms is not None:
            self.notify_sms = notify_sms

        self.updated_at = datetime.now(timezone.utc)

    def activate(self) -> None:
        """Enable this alert configuration."""
        self.is_active = True
        self.updated_at = datetime.now(timezone.utc)

    def deactivate(self) -> None:
        """Disable this alert configuration."""
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)

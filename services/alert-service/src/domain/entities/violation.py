"""Violation entity — the core aggregate root of the alert bounded context.

A Violation records that a sensor reading exceeded a permitted pollutant
threshold.  It carries identity (UUID), lifecycle state (OPEN → RESOLVED),
business rules for resolution, and emits domain events consumed by the
Factory Service and notification infrastructure.

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from ..events.alert_events import ViolationDetected, ViolationResolved
from ..exceptions.alert_exceptions import (
    ViolationAlreadyResolvedError,
)
from ..value_objects.severity import Severity


@dataclass
class Violation:
    """Aggregate root representing a threshold violation.

    Identity is defined by ``id`` (UUID).  Equality and hashing should be
    based on ``id`` alone when stored in collections.
    """

    id: UUID
    factory_id: UUID
    sensor_id: UUID
    pollutant: str
    measured_value: float
    permitted_value: float
    exceedance_percentage: float
    severity: Severity
    status: str = "OPEN"
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    action_taken: str = ""
    notes: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    _events: List = field(default_factory=list, repr=False)

    # ------------------------------------------------------------------
    # Factory method (named-constructor pattern)
    # ------------------------------------------------------------------
    @classmethod
    def create(
        cls,
        factory_id: UUID,
        sensor_id: UUID,
        pollutant: str,
        measured_value: float,
        permitted_value: float,
        severity: Severity,
    ) -> Violation:
        """Create a new OPEN violation.

        Calculates the exceedance percentage automatically and emits a
        ``ViolationDetected`` domain event.

        Parameters
        ----------
        factory_id:
            The factory whose sensor triggered the violation.
        sensor_id:
            The sensor that produced the offending reading.
        pollutant:
            Pollutant code (e.g. "pm25", "co", "no2").
        measured_value:
            Actual measured concentration.
        permitted_value:
            Threshold value that was exceeded.
        severity:
            Severity classification for this violation.
        """
        if measured_value < 0:
            raise ValueError(
                f"Measured value must be non-negative, got {measured_value}"
            )
        if permitted_value <= 0:
            raise ValueError(
                f"Permitted value must be positive, got {permitted_value}"
            )

        exceedance = ((measured_value - permitted_value) / permitted_value) * 100

        violation = cls(
            id=uuid4(),
            factory_id=factory_id,
            sensor_id=sensor_id,
            pollutant=pollutant,
            measured_value=measured_value,
            permitted_value=permitted_value,
            exceedance_percentage=round(exceedance, 2),
            severity=severity,
        )

        violation._events.append(
            ViolationDetected(
                violation_id=violation.id,
                factory_id=factory_id,
                sensor_id=sensor_id,
                pollutant=pollutant,
                measured_value=measured_value,
                threshold=permitted_value,
                severity=severity.value,
            )
        )

        return violation

    # ------------------------------------------------------------------
    # Command methods (state mutations)
    # ------------------------------------------------------------------
    def resolve(self, notes: str = "", action_taken: str = "") -> None:
        """Resolve this violation.

        Transitions the status from OPEN to RESOLVED and records the
        resolution timestamp.  Emits a ``ViolationResolved`` event.

        Parameters
        ----------
        notes:
            Free-text notes about the resolution.
        action_taken:
            Description of corrective action taken.

        Raises
        ------
        ViolationAlreadyResolvedError
            If the violation has already been resolved.
        """
        if self.status == "RESOLVED":
            raise ViolationAlreadyResolvedError(str(self.id))

        self.status = "RESOLVED"
        self.resolved_at = datetime.now(timezone.utc)
        self.notes = notes
        self.action_taken = action_taken
        self.updated_at = datetime.now(timezone.utc)

        self._events.append(
            ViolationResolved(
                violation_id=self.id,
                factory_id=self.factory_id,
                resolution_notes=notes,
            )
        )

    # ------------------------------------------------------------------
    # Event collection
    # ------------------------------------------------------------------
    def collect_events(self) -> List:
        """Return and clear all pending domain events."""
        events = self._events.copy()
        self._events.clear()
        return events

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    @property
    def is_open(self) -> bool:
        return self.status == "OPEN"

    @property
    def is_resolved(self) -> bool:
        return self.status == "RESOLVED"

    @property
    def is_critical(self) -> bool:
        return self.severity == Severity.CRITICAL

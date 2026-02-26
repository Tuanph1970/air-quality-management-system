"""Factory entity — the core aggregate root of the factory bounded context.

Encapsulates identity, lifecycle state, business rules, and domain event
emission.  All state mutations go through explicit methods that enforce
invariants and record events for downstream consumers.

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from ..events.factory_events import (
    FactoryCreated,
    FactoryResumed,
    FactoryStatusChanged,
    FactorySuspended,
    FactoryUpdated,
)
from ..exceptions.factory_exceptions import (
    FactoryAlreadySuspendedError,
    FactoryClosedError,
    FactoryNotSuspendedError,
    InvalidFactoryStatusError,
)
from ..value_objects.emission_limit import EmissionLimits
from ..value_objects.factory_status import FactoryStatus
from ..value_objects.location import Location


@dataclass
class Factory:
    """Aggregate root representing a factory with emissions monitoring.

    Identity is defined by ``id`` (UUID).  Equality and hashing should be
    based on ``id`` alone when stored in collections.
    """

    id: UUID
    name: str
    registration_number: str
    industry_type: str
    location: Location
    emission_limits: EmissionLimits
    status: FactoryStatus = field(default_factory=lambda: FactoryStatus.ACTIVE)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    _events: List = field(default_factory=list, repr=False)

    # ------------------------------------------------------------------
    # Factory method (named-constructor pattern)
    # ------------------------------------------------------------------
    @classmethod
    def create(
        cls,
        name: str,
        registration_number: str,
        industry_type: str,
        latitude: float,
        longitude: float,
        emission_limits: Dict,
    ) -> Factory:
        """Create a new Factory with an ACTIVE status.

        Emits a ``FactoryCreated`` domain event.
        """
        factory = cls(
            id=uuid4(),
            name=name,
            registration_number=registration_number,
            industry_type=industry_type,
            location=Location(latitude=latitude, longitude=longitude),
            emission_limits=EmissionLimits.from_dict(emission_limits),
        )
        factory._events.append(
            FactoryCreated(
                factory_id=factory.id,
                name=name,
                registration_number=registration_number,
                industry_type=industry_type,
                latitude=latitude,
                longitude=longitude,
                max_emissions=emission_limits,
            )
        )
        return factory

    # ------------------------------------------------------------------
    # Command methods (state mutations)
    # ------------------------------------------------------------------
    def update(self, **fields) -> None:
        """Update mutable fields.

        Accepted keyword arguments: ``name``, ``industry_type``,
        ``emission_limits`` (dict), ``location`` (dict with lat/lng).
        Emits ``FactoryUpdated``.
        """
        self._assert_not_closed()

        updated: Dict = {}
        if "name" in fields:
            self.name = fields["name"]
            updated["name"] = self.name
        if "industry_type" in fields:
            self.industry_type = fields["industry_type"]
            updated["industry_type"] = self.industry_type
        if "emission_limits" in fields:
            self.emission_limits = EmissionLimits.from_dict(fields["emission_limits"])
            updated["emission_limits"] = self.emission_limits.to_dict()
        if "location" in fields:
            loc = fields["location"]
            self.location = Location(
                latitude=loc.get("latitude", self.location.latitude),
                longitude=loc.get("longitude", self.location.longitude),
            )
            updated["latitude"] = self.location.latitude
            updated["longitude"] = self.location.longitude

        if updated:
            self.updated_at = datetime.now(timezone.utc)
            self._events.append(
                FactoryUpdated(factory_id=self.id, updated_fields=updated)
            )

    def suspend(self, reason: str, suspended_by: Optional[UUID] = None) -> None:
        """Suspend factory operations.

        Raises
        ------
        FactoryClosedError
            If the factory is permanently closed.
        FactoryAlreadySuspendedError
            If the factory is already suspended.
        """
        self._assert_not_closed()

        if self.status == FactoryStatus.SUSPENDED:
            raise FactoryAlreadySuspendedError()

        old_status = self.status
        self.status = FactoryStatus.SUSPENDED
        self.updated_at = datetime.now(timezone.utc)

        self._events.append(
            FactoryStatusChanged(
                factory_id=self.id,
                old_status=old_status.value,
                new_status=self.status.value,
                reason=reason,
            )
        )
        self._events.append(
            FactorySuspended(
                factory_id=self.id,
                reason=reason,
                suspended_by=suspended_by,
            )
        )

    def resume(self, resumed_by: Optional[UUID] = None, notes: str = "") -> None:
        """Resume a previously suspended factory.

        Raises
        ------
        FactoryNotSuspendedError
            If the factory is not currently suspended.
        """
        if self.status != FactoryStatus.SUSPENDED:
            raise FactoryNotSuspendedError()

        old_status = self.status
        self.status = FactoryStatus.ACTIVE
        self.updated_at = datetime.now(timezone.utc)

        self._events.append(
            FactoryStatusChanged(
                factory_id=self.id,
                old_status=old_status.value,
                new_status=self.status.value,
                reason="Resumed operations",
            )
        )
        self._events.append(
            FactoryResumed(
                factory_id=self.id,
                resumed_by=resumed_by,
                notes=notes,
            )
        )

    def close(self, reason: str = "") -> None:
        """Permanently close the factory.

        Once closed, no further status transitions are permitted.
        """
        self._assert_not_closed()

        old_status = self.status
        self.status = FactoryStatus.CLOSED
        self.updated_at = datetime.now(timezone.utc)

        self._events.append(
            FactoryStatusChanged(
                factory_id=self.id,
                old_status=old_status.value,
                new_status=self.status.value,
                reason=reason or "Permanently closed",
            )
        )

    def update_status_from_emissions(self, current_aqi: int) -> None:
        """Re-evaluate operational status based on the latest AQI reading.

        Does nothing if the factory is suspended or closed — those states
        are managed explicitly through ``suspend()`` / ``resume()`` /
        ``close()``.

        Thresholds:
            - AQI > 200 → CRITICAL
            - AQI > 150 → WARNING
            - Otherwise  → ACTIVE
        """
        if not self.status.is_operational:
            return

        if current_aqi > 200:
            new_status = FactoryStatus.CRITICAL
        elif current_aqi > 150:
            new_status = FactoryStatus.WARNING
        else:
            new_status = FactoryStatus.ACTIVE

        if new_status != self.status:
            old_status = self.status
            self.status = new_status
            self.updated_at = datetime.now(timezone.utc)
            self._events.append(
                FactoryStatusChanged(
                    factory_id=self.id,
                    old_status=old_status.value,
                    new_status=new_status.value,
                    reason=f"AQI reading: {current_aqi}",
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
    def is_active(self) -> bool:
        return self.status == FactoryStatus.ACTIVE

    @property
    def is_suspended(self) -> bool:
        return self.status == FactoryStatus.SUSPENDED

    @property
    def is_closed(self) -> bool:
        return self.status == FactoryStatus.CLOSED

    # ------------------------------------------------------------------
    # Internal guards
    # ------------------------------------------------------------------
    def _assert_not_closed(self) -> None:
        if self.status.is_terminal:
            raise FactoryClosedError()

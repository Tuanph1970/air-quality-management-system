"""Alert configuration data transfer objects."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from ...domain.entities.alert_config import AlertConfig


@dataclass
class AlertConfigDTO:
    """Read-only projection of an AlertConfig entity for the interface layer."""

    id: UUID
    name: str
    pollutant: str
    warning_threshold: float
    high_threshold: float
    critical_threshold: float
    duration_minutes: int
    is_active: bool
    notify_email: bool
    notify_sms: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, entity: AlertConfig) -> AlertConfigDTO:
        """Map a domain entity to a DTO."""
        return cls(
            id=entity.id,
            name=entity.name,
            pollutant=entity.pollutant,
            warning_threshold=entity.warning_threshold,
            high_threshold=entity.high_threshold,
            critical_threshold=entity.critical_threshold,
            duration_minutes=entity.duration_minutes,
            is_active=entity.is_active,
            notify_email=entity.notify_email,
            notify_sms=entity.notify_sms,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

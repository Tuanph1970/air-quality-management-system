"""Alert domain events shared across services.

Published by the Alert Service when threshold violations are detected
or resolved.  The Factory Service listens for ViolationDetected to
update factory operational status.
"""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from .base_event import DomainEvent


@dataclass
class ViolationDetected(DomainEvent):
    """A sensor reading has exceeded a configured threshold.

    The Factory Service consumes this to transition a factory into
    WARNING or CRITICAL status.
    """

    violation_id: UUID = None
    factory_id: UUID = None
    sensor_id: UUID = None
    pollutant: str = ""
    measured_value: float = 0.0
    threshold: float = 0.0
    unit: str = "ug/m3"
    severity: str = ""           # LOW | MEDIUM | HIGH | CRITICAL
    event_type: str = "alert.violation.detected"


@dataclass
class ViolationResolved(DomainEvent):
    """A previously open violation has been resolved."""

    violation_id: UUID = None
    factory_id: UUID = None
    resolved_by: UUID = None
    resolution_notes: str = ""
    event_type: str = "alert.violation.resolved"


@dataclass
class AlertConfigUpdated(DomainEvent):
    """An alert threshold configuration has been created or modified."""

    config_id: UUID = None
    pollutant: str = ""
    old_threshold: Optional[float] = None
    new_threshold: float = 0.0
    severity: str = ""
    updated_by: UUID = None
    event_type: str = "alert.config.updated"

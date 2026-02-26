"""Alert domain events."""
from dataclasses import dataclass
from uuid import UUID


@dataclass
class ViolationDetected:
    violation_id: UUID = None
    factory_id: UUID = None
    pollutant: str = ""
    severity: str = ""


@dataclass
class ViolationResolved:
    violation_id: UUID = None
    resolved_by: UUID = None


@dataclass
class AlertTriggered:
    alert_id: UUID = None
    factory_id: UUID = None
    message: str = ""

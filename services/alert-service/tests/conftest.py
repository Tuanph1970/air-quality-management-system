"""Shared test fixtures for the alert service test suite.

Bootstraps ``shared.*`` modules with lightweight stubs so tests can run
locally without Docker.  Provides common fixtures: sample data, mock
repositories, mock event publishers, and a configured application service.
"""
from __future__ import annotations

import sys
import types
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import pytest


# =========================================================================
# 1. Bootstrap shared modules (must run before any src.* imports)
# =========================================================================

# --- shared.events.base_event ---
_shared_events_base = types.ModuleType("shared.events.base_event")


@dataclass
class _DomainEvent:
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str = ""

    def to_dict(self) -> Dict[str, Any]:
        from dataclasses import asdict

        return asdict(self)


_shared_events_base.DomainEvent = _DomainEvent

# --- shared.events.alert_events ---
_shared_events_alert = types.ModuleType("shared.events.alert_events")


@dataclass
class _ViolationDetected(_DomainEvent):
    violation_id: UUID = field(default_factory=uuid4)
    factory_id: UUID = field(default_factory=uuid4)
    sensor_id: UUID = field(default_factory=uuid4)
    pollutant: str = ""
    measured_value: float = 0.0
    threshold: float = 0.0
    severity: str = "WARNING"
    event_type: str = "alert.violation.detected"


@dataclass
class _ViolationResolved(_DomainEvent):
    violation_id: UUID = field(default_factory=uuid4)
    factory_id: UUID = field(default_factory=uuid4)
    resolution_notes: str = ""
    event_type: str = "alert.violation.resolved"


@dataclass
class _AlertConfigUpdated(_DomainEvent):
    config_id: UUID = field(default_factory=uuid4)
    pollutant: str = ""
    event_type: str = "alert.config.updated"


_shared_events_alert.ViolationDetected = _ViolationDetected
_shared_events_alert.ViolationResolved = _ViolationResolved
_shared_events_alert.AlertConfigUpdated = _AlertConfigUpdated

# --- shared.events.sensor_events (for integration tests) ---
_shared_events_sensor = types.ModuleType("shared.events.sensor_events")


@dataclass
class _SensorReadingCreated(_DomainEvent):
    sensor_id: UUID = field(default_factory=uuid4)
    factory_id: UUID = field(default_factory=uuid4)
    pm25: float = 0.0
    pm10: float = 0.0
    co: float = 0.0
    no2: float = 0.0
    so2: float = 0.0
    o3: float = 0.0
    aqi: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str = "sensor.reading.created"


_shared_events_sensor.SensorReadingCreated = _SensorReadingCreated

# --- shared.events.factory_events ---
_shared_events_factory = types.ModuleType("shared.events.factory_events")


@dataclass
class _FactoryStatusChanged(_DomainEvent):
    factory_id: UUID = field(default_factory=uuid4)
    old_status: str = ""
    new_status: str = ""
    reason: str = ""
    event_type: str = "factory.status.changed"


_shared_events_factory.FactoryStatusChanged = _FactoryStatusChanged

# --- shared.messaging.config ---
_shared_msg_config = types.ModuleType("shared.messaging.config")
_shared_msg_config.FACTORY_EXCHANGE = "factory.events"
_shared_msg_config.SENSOR_EXCHANGE = "sensor.events"
_shared_msg_config.ALERT_EXCHANGE = "alert.events"
_shared_msg_config.RABBITMQ_URL = "amqp://guest:guest@localhost:5672/"
_shared_msg_config.RECONNECT_INTERVAL = 5
_shared_msg_config.MAX_RECONNECT_ATTEMPTS = 0
_shared_msg_config.PREFETCH_COUNT = 10
_shared_msg_config.ALERT_SENSOR_READINGS_QUEUE = "alert.sensor_readings"
_shared_msg_config.ALERT_FACTORY_EVENTS_QUEUE = "alert.factory_handler"


@dataclass(frozen=True)
class _QueueBinding:
    queue: str = ""
    exchange: str = ""
    routing_keys: list = field(default_factory=list)


_shared_msg_config.QueueBinding = _QueueBinding
_shared_msg_config.ALERT_SERVICE_BINDINGS = []

# --- shared.messaging.publisher ---
_shared_msg_pub = types.ModuleType("shared.messaging.publisher")


class _RabbitMQPublisher:
    """Stub RabbitMQ publisher for tests."""
    def __init__(self, url: str = "") -> None:
        pass

    async def connect(self) -> None:
        pass

    async def close(self) -> None:
        pass

    async def publish(self, event, exchange: str = "") -> None:
        pass


_shared_msg_pub.RabbitMQPublisher = _RabbitMQPublisher

# --- shared.messaging.consumer ---
_shared_msg_con = types.ModuleType("shared.messaging.consumer")


class _RabbitMQConsumer:
    def __init__(self, **kw) -> None:
        pass

    async def connect(self) -> None:
        pass

    async def close(self) -> None:
        pass

    async def subscribe_bindings(self, bindings, handlers) -> None:
        pass

    async def start_consuming(self) -> None:
        pass


_shared_msg_con.RabbitMQConsumer = _RabbitMQConsumer

# Wire everything into sys.modules
_shared = types.ModuleType("shared")
_shared_events = types.ModuleType("shared.events")
sys.modules.setdefault("shared", _shared)
sys.modules.setdefault("shared.events", _shared_events)
sys.modules.setdefault("shared.events.base_event", _shared_events_base)
sys.modules.setdefault("shared.events.alert_events", _shared_events_alert)
sys.modules.setdefault("shared.events.sensor_events", _shared_events_sensor)
sys.modules.setdefault("shared.events.factory_events", _shared_events_factory)
sys.modules.setdefault("shared.messaging", types.ModuleType("shared.messaging"))
sys.modules.setdefault("shared.messaging.config", _shared_msg_config)
sys.modules.setdefault("shared.messaging.publisher", _shared_msg_pub)
sys.modules.setdefault("shared.messaging.consumer", _shared_msg_con)


# =========================================================================
# 2. Now safe to import src.* modules
# =========================================================================
from src.domain.entities.violation import Violation
from src.domain.entities.alert_config import AlertConfig
from src.domain.value_objects.severity import Severity
from src.domain.repositories.violation_repository import ViolationRepository
from src.domain.repositories.alert_config_repository import AlertConfigRepository
from src.application.services.alert_application_service import (
    AlertApplicationService,
)


# =========================================================================
# 3. In-memory repositories for unit tests
# =========================================================================
class InMemoryViolationRepository(ViolationRepository):
    """Test double — stores violations in a plain dict."""

    def __init__(self) -> None:
        self._store: Dict[UUID, Violation] = {}

    async def get_by_id(self, violation_id: UUID) -> Optional[Violation]:
        return self._store.get(violation_id)

    async def list_by_factory(
        self,
        factory_id: UUID,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Violation]:
        items = [v for v in self._store.values() if v.factory_id == factory_id]
        if status:
            items = [v for v in items if v.status == status]
        return items[skip : skip + limit]

    async def list_open(
        self,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Violation]:
        items = [v for v in self._store.values() if v.status == "OPEN"]
        items.sort(key=lambda x: x.detected_at, reverse=True)
        return items[skip : skip + limit]

    async def list_by_sensor(
        self,
        sensor_id: UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Violation]:
        items = [v for v in self._store.values() if v.sensor_id == sensor_id]
        return items[skip : skip + limit]

    async def list_by_severity(
        self,
        severity: str,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Violation]:
        items = [v for v in self._store.values() if v.severity.value == severity]
        return items[skip : skip + limit]

    async def count(
        self,
        factory_id: Optional[UUID] = None,
        status: Optional[str] = None,
    ) -> int:
        items = list(self._store.values())
        if factory_id:
            items = [v for v in items if v.factory_id == factory_id]
        if status:
            items = [v for v in items if v.status == status]
        return len(items)

    async def save(self, violation: Violation) -> Violation:
        self._store[violation.id] = violation
        return violation

    async def delete(self, violation_id: UUID) -> bool:
        return self._store.pop(violation_id, None) is not None


class InMemoryAlertConfigRepository(AlertConfigRepository):
    """Test double — stores alert configs in a plain dict."""

    def __init__(self) -> None:
        self._store: Dict[UUID, AlertConfig] = {}
        self._by_pollutant: Dict[str, UUID] = {}

    async def get_by_id(self, config_id: UUID) -> Optional[AlertConfig]:
        return self._store.get(config_id)

    async def get_by_pollutant(self, pollutant: str) -> Optional[AlertConfig]:
        config_id = self._by_pollutant.get(pollutant)
        if config_id:
            config = self._store.get(config_id)
            if config and config.is_active:
                return config
        return None

    async def list_active(self) -> List[AlertConfig]:
        items = [c for c in self._store.values() if c.is_active]
        items.sort(key=lambda x: x.pollutant)
        return items

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 20,
    ) -> List[AlertConfig]:
        items = list(self._store.values())
        items.sort(key=lambda x: x.pollutant)
        return items[skip : skip + limit]

    async def save(self, config: AlertConfig) -> AlertConfig:
        self._store[config.id] = config
        self._by_pollutant[config.pollutant] = config.id
        return config

    async def delete(self, config_id: UUID) -> bool:
        config = self._store.pop(config_id, None)
        if config:
            self._by_pollutant.pop(config.pollutant, None)
            return True
        return False


# =========================================================================
# 4. Mock event publisher for unit tests
# =========================================================================
class MockEventPublisher:
    """Collects published events for assertion."""

    def __init__(self) -> None:
        self.events: list = []
        self.connected = False

    async def connect(self) -> None:
        self.connected = True

    async def close(self) -> None:
        self.connected = False

    async def publish(self, event) -> None:
        self.events.append(event)

    def clear(self) -> None:
        self.events.clear()


# =========================================================================
# 5. Sample data fixtures
# =========================================================================
SAMPLE_FACTORY_ID = uuid4()
SAMPLE_SENSOR_ID = uuid4()


@pytest.fixture
def sample_factory_id() -> UUID:
    return SAMPLE_FACTORY_ID


@pytest.fixture
def sample_sensor_id() -> UUID:
    return SAMPLE_SENSOR_ID


@pytest.fixture
def sample_violation_data() -> Dict[str, Any]:
    return {
        "factory_id": SAMPLE_FACTORY_ID,
        "sensor_id": SAMPLE_SENSOR_ID,
        "pollutant": "pm25",
        "measured_value": 85.5,
        "permitted_value": 50.0,
        "severity": Severity.WARNING,
    }


@pytest.fixture
def sample_violation(sample_violation_data) -> Violation:
    return Violation.create(**sample_violation_data)


@pytest.fixture
def sample_alert_config_data() -> Dict[str, Any]:
    return {
        "name": "PM2.5 City Limit",
        "pollutant": "pm25",
        "warning_threshold": 35.0,
        "high_threshold": 55.0,
        "critical_threshold": 150.0,
        "duration_minutes": 0,
        "notify_email": True,
        "notify_sms": False,
    }


@pytest.fixture
def sample_alert_config(sample_alert_config_data) -> AlertConfig:
    return AlertConfig.create(**sample_alert_config_data)


@pytest.fixture
def mock_publisher() -> MockEventPublisher:
    return MockEventPublisher()


@pytest.fixture
def in_memory_violation_repo() -> InMemoryViolationRepository:
    return InMemoryViolationRepository()


@pytest.fixture
def in_memory_alert_config_repo() -> InMemoryAlertConfigRepository:
    return InMemoryAlertConfigRepository()


@pytest.fixture
def alert_service(
    in_memory_violation_repo: InMemoryViolationRepository,
    in_memory_alert_config_repo: InMemoryAlertConfigRepository,
    mock_publisher: MockEventPublisher,
) -> AlertApplicationService:
    """Create an AlertApplicationService with in-memory dependencies."""
    return AlertApplicationService(
        violation_repository=in_memory_violation_repo,
        alert_config_repository=in_memory_alert_config_repo,
        event_publisher=mock_publisher,
    )


@pytest.fixture
def anyio_backend():
    return "asyncio"

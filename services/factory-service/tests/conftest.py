"""Shared test fixtures for the factory service test suite.

Bootstraps ``shared.*`` modules with lightweight stubs so tests can run
locally without Docker.  Provides common fixtures: sample data, mock
repositories, mock event publishers, and a configured application service.
"""
from __future__ import annotations

import importlib
import sys
import types
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import pytest

# =========================================================================
# 1. Bootstrap shared modules  (must run before any src.* imports)
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

# --- shared.events.factory_events ---
_shared_events_factory = types.ModuleType("shared.events.factory_events")


@dataclass
class _FactoryCreated(_DomainEvent):
    factory_id: UUID = None
    name: str = ""
    registration_number: str = ""
    industry_type: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    max_emissions: Dict = field(default_factory=dict)
    event_type: str = "factory.created"


@dataclass
class _FactoryUpdated(_DomainEvent):
    factory_id: UUID = None
    updated_fields: Dict = field(default_factory=dict)
    event_type: str = "factory.updated"


@dataclass
class _FactoryStatusChanged(_DomainEvent):
    factory_id: UUID = None
    old_status: str = ""
    new_status: str = ""
    reason: str = ""
    event_type: str = "factory.status.changed"


@dataclass
class _FactorySuspended(_DomainEvent):
    factory_id: UUID = None
    reason: str = ""
    suspended_by: UUID = None
    event_type: str = "factory.suspended"


@dataclass
class _FactoryResumed(_DomainEvent):
    factory_id: UUID = None
    resumed_by: UUID = None
    notes: str = ""
    event_type: str = "factory.resumed"


_shared_events_factory.FactoryCreated = _FactoryCreated
_shared_events_factory.FactoryUpdated = _FactoryUpdated
_shared_events_factory.FactoryStatusChanged = _FactoryStatusChanged
_shared_events_factory.FactorySuspended = _FactorySuspended
_shared_events_factory.FactoryResumed = _FactoryResumed

# --- shared.auth.* (for integration tests) ---
_shared_auth = types.ModuleType("shared.auth")
_shared_auth_models = types.ModuleType("shared.auth.models")
_shared_auth_deps = types.ModuleType("shared.auth.dependencies")
_shared_auth_exc = types.ModuleType("shared.auth.exceptions")


@dataclass(frozen=True)
class _UserClaims:
    user_id: UUID = field(default_factory=uuid4)
    role: str = "viewer"

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_inspector(self) -> bool:
        return self.role in ("admin", "inspector")

    def has_role(self, *roles: str) -> bool:
        return self.role in roles


_shared_auth_models.UserClaims = _UserClaims


# Auth dependency stubs
async def _get_current_user() -> _UserClaims:
    return _UserClaims(user_id=uuid4(), role="admin")


def _require_role(roles):
    async def _checker():
        return _UserClaims(user_id=uuid4(), role="admin")

    return _checker


_shared_auth_deps.get_current_user = _get_current_user
_shared_auth_deps.require_role = _require_role
_shared_auth_exc.AuthError = type("AuthError", (Exception,), {"detail": ""})
_shared_auth_exc.AuthenticationError = type("AuthenticationError", (Exception,), {})
_shared_auth_exc.AuthorizationError = type("AuthorizationError", (Exception,), {})

# --- shared.messaging.config (stubs) ---
_shared_msg = types.ModuleType("shared.messaging")
_shared_msg_config = types.ModuleType("shared.messaging.config")
_shared_msg_config.FACTORY_EXCHANGE = "factory.events"
_shared_msg_config.SENSOR_EXCHANGE = "sensor.events"
_shared_msg_config.ALERT_EXCHANGE = "alert.events"
_shared_msg_config.RABBITMQ_URL = "amqp://guest:guest@localhost:5672/"
_shared_msg_config.RECONNECT_INTERVAL = 5
_shared_msg_config.MAX_RECONNECT_ATTEMPTS = 0
_shared_msg_config.PREFETCH_COUNT = 10
_shared_msg_config.FACTORY_VIOLATION_QUEUE = "factory.violation_handler"
_shared_msg_config.FACTORY_SENSOR_STATUS_QUEUE = "factory.sensor_status"
_shared_msg_config.FACTORY_SERVICE_BINDINGS = []


@dataclass(frozen=True)
class _QueueBinding:
    queue: str = ""
    exchange: str = ""
    routing_keys: list = field(default_factory=list)


_shared_msg_config.QueueBinding = _QueueBinding

# --- shared.messaging.publisher ---
_shared_msg_pub = types.ModuleType("shared.messaging.publisher")


class _RabbitMQPublisher:
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
_shared_events.__init__ = types.ModuleType("shared.events.__init__")
sys.modules.setdefault("shared", _shared)
sys.modules.setdefault("shared.events", _shared_events)
sys.modules.setdefault("shared.events.base_event", _shared_events_base)
sys.modules.setdefault("shared.events.factory_events", _shared_events_factory)
sys.modules.setdefault("shared.auth", _shared_auth)
sys.modules.setdefault("shared.auth.models", _shared_auth_models)
sys.modules.setdefault("shared.auth.dependencies", _shared_auth_deps)
sys.modules.setdefault("shared.auth.exceptions", _shared_auth_exc)
sys.modules.setdefault("shared.messaging", _shared_msg)
sys.modules.setdefault("shared.messaging.config", _shared_msg_config)
sys.modules.setdefault("shared.messaging.publisher", _shared_msg_pub)
sys.modules.setdefault("shared.messaging.consumer", _shared_msg_con)


# =========================================================================
# 2. Now safe to import src.* modules
# =========================================================================
from src.domain.entities.factory import Factory
from src.domain.value_objects.emission_limit import EmissionLimits
from src.domain.value_objects.factory_status import FactoryStatus
from src.domain.value_objects.location import Location
from src.domain.repositories.factory_repository import FactoryRepository
from src.application.services.factory_application_service import (
    FactoryApplicationService,
)


# =========================================================================
# 3. In-memory repository for unit and integration tests
# =========================================================================
class InMemoryFactoryRepository(FactoryRepository):
    """Test double — stores factories in a plain dict."""

    def __init__(self) -> None:
        self._store: Dict[UUID, Factory] = {}

    async def get_by_id(self, factory_id: UUID) -> Optional[Factory]:
        return self._store.get(factory_id)

    async def get_by_registration_number(self, reg_number: str) -> Optional[Factory]:
        for f in self._store.values():
            if f.registration_number == reg_number:
                return f
        return None

    async def list_all(
        self, status: Optional[str] = None, skip: int = 0, limit: int = 20,
    ) -> List[Factory]:
        items = list(self._store.values())
        if status:
            items = [f for f in items if f.status.value == status]
        return items[skip : skip + limit]

    async def save(self, factory: Factory) -> Factory:
        self._store[factory.id] = factory
        return factory

    async def delete(self, factory_id: UUID) -> bool:
        return self._store.pop(factory_id, None) is not None

    async def count(self, status: Optional[str] = None) -> int:
        if status:
            return sum(1 for f in self._store.values() if f.status.value == status)
        return len(self._store)


# =========================================================================
# 4. Mock event publisher for unit tests
# =========================================================================
class MockEventPublisher:
    """Collects published events for assertion."""

    def __init__(self) -> None:
        self.events: list = []

    async def publish(self, event) -> None:
        self.events.append(event)

    def clear(self) -> None:
        self.events.clear()


# =========================================================================
# 5. Fixtures
# =========================================================================
SAMPLE_EMISSION_LIMITS = {
    "pm25_limit": 50.0,
    "pm10_limit": 100.0,
    "co_limit": 10.0,
    "no2_limit": 40.0,
    "so2_limit": 20.0,
    "o3_limit": 60.0,
}


@pytest.fixture
def sample_emission_limits() -> Dict[str, float]:
    return SAMPLE_EMISSION_LIMITS.copy()


@pytest.fixture
def sample_factory_data() -> Dict[str, Any]:
    return {
        "name": "Viet Steel Manufacturing",
        "registration_number": "REG-2024-001",
        "industry_type": "Steel",
        "latitude": 21.0285,
        "longitude": 105.8542,
        "emission_limits": SAMPLE_EMISSION_LIMITS.copy(),
    }


@pytest.fixture
def sample_factory(sample_factory_data) -> Factory:
    return Factory.create(**sample_factory_data)


@pytest.fixture
def mock_publisher() -> MockEventPublisher:
    return MockEventPublisher()


@pytest.fixture
def in_memory_repo() -> InMemoryFactoryRepository:
    return InMemoryFactoryRepository()


@pytest.fixture
def factory_service(
    in_memory_repo: InMemoryFactoryRepository,
    mock_publisher: MockEventPublisher,
) -> FactoryApplicationService:
    return FactoryApplicationService(
        factory_repository=in_memory_repo,
        event_publisher=mock_publisher,
    )

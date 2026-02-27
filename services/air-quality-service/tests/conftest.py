"""Shared test fixtures for the air quality service test suite.

Bootstraps ``shared.*`` modules with lightweight stubs so tests can run
locally without Docker.
"""
from __future__ import annotations

import sys
import types
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import UUID, uuid4

import pytest


# =========================================================================
# 1. Bootstrap shared modules
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

# --- shared.events.sensor_events ---
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

# --- shared.events.alert_events ---
_shared_events_alert = types.ModuleType("shared.events.alert_events")


@dataclass
class _ViolationDetected(_DomainEvent):
    violation_id: UUID = field(default_factory=uuid4)
    factory_id: UUID = field(default_factory=uuid4)
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


_shared_events_alert.ViolationDetected = _ViolationDetected
_shared_events_alert.ViolationResolved = _ViolationResolved

# --- shared.messaging.config ---
_shared_msg_config = types.ModuleType("shared.messaging.config")
_shared_msg_config.AQ_SENSOR_READINGS_QUEUE = "airquality.sensor_readings"
_shared_msg_config.AQ_ALERT_EVENTS_QUEUE = "airquality.alert_handler"
_shared_msg_config.RABBITMQ_URL = "amqp://guest:guest@localhost:5672/"


@dataclass(frozen=True)
class _QueueBinding:
    queue: str = ""
    exchange: str = ""
    routing_keys: list = field(default_factory=list)


_shared_msg_config.QueueBinding = _QueueBinding
_shared_msg_config.AIR_QUALITY_SERVICE_BINDINGS = []

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

# Wire into sys.modules
_shared = types.ModuleType("shared")
_shared_events = types.ModuleType("shared.events")
sys.modules.setdefault("shared", _shared)
sys.modules.setdefault("shared.events", _shared_events)
sys.modules.setdefault("shared.events.base_event", _shared_events_base)
sys.modules.setdefault("shared.events.sensor_events", _shared_events_sensor)
sys.modules.setdefault("shared.events.alert_events", _shared_events_alert)
sys.modules.setdefault("shared.messaging", types.ModuleType("shared.messaging"))
sys.modules.setdefault("shared.messaging.config", _shared_msg_config)
sys.modules.setdefault("shared.messaging.consumer", _shared_msg_con)


# =========================================================================
# 2. Test fixtures
# =========================================================================

@pytest.fixture
def sample_location() -> tuple:
    """Sample location for testing."""
    return (21.0285, 105.8542)  # Hanoi


@pytest.fixture
def sample_pollutants() -> Dict[str, float]:
    """Sample pollutant concentrations."""
    return {
        "pm25": 35.0,
        "pm10": 50.0,
        "o3": 60.0,
        "no2": 30.0,
        "co": 5.0,
        "so2": 20.0,
    }


@pytest.fixture
def sample_sensor_data():
    """Sample historical sensor data for forecasting."""
    from src.domain.services.prediction_service import SensorDataPoint
    
    now = datetime.utcnow()
    return [
        SensorDataPoint(
            timestamp=now - timedelta(hours=i),
            pollutants={"pm25": 30 + i * 2, "pm10": 50},
            aqi=50 + i * 3,
        )
        for i in range(12, 0, -1)
    ]


@pytest.fixture
def anyio_backend():
    return "asyncio"


# Import timedelta for sample data generation
from datetime import timedelta

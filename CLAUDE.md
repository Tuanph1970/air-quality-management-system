# CLAUDE.md - Air Quality Management Information System (AQMIS)

## Project Overview

You are building an **Air Quality Management Information System** using **Microservice Architecture** and **Domain-Driven Design (DDD)** patterns. The system monitors city air quality, manages factory emissions, and enables enforcement actions.

### Architecture Principles
- **Microservices**: Independent, loosely-coupled services
- **Domain-Driven Design**: Business logic organized by bounded contexts
- **Event-Driven**: Services communicate via events/messages
- **API Gateway**: Single entry point for all clients
- **Docker**: Containerized deployment for all services

### Tech Stack
- **Frontend**: React 18 + JavaScript + Vite + TailwindCSS
- **Backend Services**: Python FastAPI (per microservice)
- **API Gateway**: FastAPI with routing
- **Message Broker**: RabbitMQ (async communication)
- **Databases**: PostgreSQL (per service), TimescaleDB (sensor data), Redis (cache)
- **Container Orchestration**: Docker Compose
- **Service Communication**: REST (sync) + RabbitMQ (async)

---

## Microservices Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                        │
│                    (Web App, Mobile App, IoT Devices)                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY                                       │
│                    (Authentication, Routing, Rate Limiting)                 │
│                           Port: 8000                                        │
└─────────────────────────────────────────────────────────────────────────────┘
          │              │              │              │              │
          ▼              ▼              ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   FACTORY    │ │   SENSOR     │ │   ALERT      │ │ AIR QUALITY  │ │    USER      │
│   SERVICE    │ │   SERVICE    │ │   SERVICE    │ │   SERVICE    │ │   SERVICE    │
│   Port:8001  │ │   Port:8002  │ │   Port:8003  │ │   Port:8004  │ │   Port:8005  │
│              │ │              │ │              │ │              │ │              │
│ - Factories  │ │ - Sensors    │ │ - Violations │ │ - AQI Calc   │ │ - Auth       │
│ - Emissions  │ │ - Readings   │ │ - Alerts     │ │ - Predictions│ │ - Users      │
│ - Suspensions│ │ - Calibration│ │ - Notify     │ │ - Google Maps│ │ - Roles      │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │                │                │
       │                │                │                │                │
       ▼                ▼                ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MESSAGE BROKER (RabbitMQ)                         │
│                              Port: 5672                                     │
│    Events: SensorReadingCreated, ViolationDetected, FactorySuspended, etc.  │
└─────────────────────────────────────────────────────────────────────────────┘
       │                │                │                │                │
       ▼                ▼                ▼                ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  PostgreSQL  │ │ TimescaleDB  │ │  PostgreSQL  │ │    Redis     │ │  PostgreSQL  │
│  factory_db  │ │  sensor_db   │ │  alert_db    │ │    Cache     │ │   user_db    │
│  Port:5432   │ │  Port:5433   │ │  Port:5434   │ │  Port:6379   │ │  Port:5435   │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

---

## Domain-Driven Design Structure

Each microservice follows this DDD folder structure:

```
service-name/
├── src/
│   ├── domain/                    # 🔵 DOMAIN LAYER (Core Business Logic)
│   │   ├── entities/              # Business entities with identity
│   │   │   └── factory.py         # Entity classes
│   │   ├── value_objects/         # Immutable value types
│   │   │   └── location.py        # Value object classes
│   │   ├── aggregates/            # Aggregate roots
│   │   │   └── factory_aggregate.py
│   │   ├── repositories/          # Repository interfaces (abstractions)
│   │   │   └── factory_repository.py
│   │   ├── services/              # Domain services (business rules)
│   │   │   └── emission_calculator.py
│   │   ├── events/                # Domain events
│   │   │   └── factory_events.py
│   │   └── exceptions/            # Domain exceptions
│   │       └── domain_exceptions.py
│   │
│   ├── application/               # 🟢 APPLICATION LAYER (Use Cases)
│   │   ├── commands/              # Command handlers (write operations)
│   │   │   ├── create_factory.py
│   │   │   └── suspend_factory.py
│   │   ├── queries/               # Query handlers (read operations)
│   │   │   ├── get_factory.py
│   │   │   └── list_factories.py
│   │   ├── dto/                   # Data Transfer Objects
│   │   │   ├── factory_dto.py
│   │   │   └── responses.py
│   │   ├── services/              # Application services (orchestration)
│   │   │   └── factory_app_service.py
│   │   └── interfaces/            # Port interfaces
│   │       └── event_publisher.py
│   │
│   ├── infrastructure/            # 🟠 INFRASTRUCTURE LAYER (External)
│   │   ├── persistence/           # Database implementations
│   │   │   ├── models.py          # SQLAlchemy models
│   │   │   ├── factory_repo_impl.py
│   │   │   └── database.py
│   │   ├── messaging/             # Message broker
│   │   │   ├── rabbitmq_publisher.py
│   │   │   └── event_handlers.py
│   │   └── external/              # External API clients
│   │       └── google_maps_client.py
│   │
│   └── interfaces/                # 🟣 INTERFACE LAYER (Entry Points)
│       ├── api/                   # REST API endpoints
│       │   ├── routes.py
│       │   ├── factory_controller.py
│       │   └── schemas.py         # Pydantic request/response
│       └── events/                # Event consumers
│           └── event_consumers.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
│
├── alembic/                       # Database migrations
├── Dockerfile
├── requirements.txt
└── main.py                        # Service entry point
```

---

## Project Structure

```
air-quality-system/
├── CLAUDE.md
├── docker-compose.yml             # Development environment
├── docker-compose.prod.yml        # Production environment
├── .env.example
│
├── services/                      # 🔷 MICROSERVICES
│   │
│   ├── api-gateway/               # API Gateway Service
│   │   ├── src/
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── routes/
│   │   │   │   ├── factory_routes.py
│   │   │   │   ├── sensor_routes.py
│   │   │   │   ├── alert_routes.py
│   │   │   │   └── air_quality_routes.py
│   │   │   ├── middleware/
│   │   │   │   ├── auth_middleware.py
│   │   │   │   ├── rate_limiter.py
│   │   │   │   └── request_logger.py
│   │   │   └── utils/
│   │   │       └── service_client.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── factory-service/           # Factory Management Service
│   │   ├── src/
│   │   │   ├── domain/
│   │   │   │   ├── entities/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── factory.py
│   │   │   │   │   └── suspension.py
│   │   │   │   ├── value_objects/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── location.py
│   │   │   │   │   ├── emission_limit.py
│   │   │   │   │   └── factory_status.py
│   │   │   │   ├── aggregates/
│   │   │   │   │   └── factory_aggregate.py
│   │   │   │   ├── repositories/
│   │   │   │   │   └── factory_repository.py
│   │   │   │   ├── services/
│   │   │   │   │   └── suspension_service.py
│   │   │   │   ├── events/
│   │   │   │   │   └── factory_events.py
│   │   │   │   └── exceptions/
│   │   │   │       └── factory_exceptions.py
│   │   │   ├── application/
│   │   │   │   ├── commands/
│   │   │   │   │   ├── create_factory_command.py
│   │   │   │   │   ├── update_factory_command.py
│   │   │   │   │   ├── suspend_factory_command.py
│   │   │   │   │   └── resume_factory_command.py
│   │   │   │   ├── queries/
│   │   │   │   │   ├── get_factory_query.py
│   │   │   │   │   ├── list_factories_query.py
│   │   │   │   │   └── get_factory_emissions_query.py
│   │   │   │   ├── dto/
│   │   │   │   │   └── factory_dto.py
│   │   │   │   └── services/
│   │   │   │       └── factory_application_service.py
│   │   │   ├── infrastructure/
│   │   │   │   ├── persistence/
│   │   │   │   │   ├── models.py
│   │   │   │   │   ├── database.py
│   │   │   │   │   └── factory_repository_impl.py
│   │   │   │   └── messaging/
│   │   │   │       ├── rabbitmq_publisher.py
│   │   │   │       └── event_handlers.py
│   │   │   └── interfaces/
│   │   │       └── api/
│   │   │           ├── routes.py
│   │   │           ├── factory_controller.py
│   │   │           └── schemas.py
│   │   ├── alembic/
│   │   ├── tests/
│   │   ├── main.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── sensor-service/            # Sensor & Readings Service
│   │   ├── src/
│   │   │   ├── domain/
│   │   │   │   ├── entities/
│   │   │   │   │   ├── sensor.py
│   │   │   │   │   └── reading.py
│   │   │   │   ├── value_objects/
│   │   │   │   │   ├── sensor_type.py
│   │   │   │   │   ├── calibration_params.py
│   │   │   │   │   └── air_quality_reading.py
│   │   │   │   ├── aggregates/
│   │   │   │   │   └── sensor_aggregate.py
│   │   │   │   ├── repositories/
│   │   │   │   │   ├── sensor_repository.py
│   │   │   │   │   └── reading_repository.py
│   │   │   │   ├── services/
│   │   │   │   │   └── calibration_service.py
│   │   │   │   └── events/
│   │   │   │       └── sensor_events.py
│   │   │   ├── application/
│   │   │   │   ├── commands/
│   │   │   │   │   ├── register_sensor_command.py
│   │   │   │   │   ├── submit_reading_command.py
│   │   │   │   │   └── calibrate_sensor_command.py
│   │   │   │   ├── queries/
│   │   │   │   │   ├── get_sensor_query.py
│   │   │   │   │   └── get_readings_query.py
│   │   │   │   └── services/
│   │   │   │       └── sensor_application_service.py
│   │   │   ├── infrastructure/
│   │   │   │   ├── persistence/
│   │   │   │   │   ├── models.py
│   │   │   │   │   ├── timescale_database.py
│   │   │   │   │   └── sensor_repository_impl.py
│   │   │   │   └── messaging/
│   │   │   │       └── rabbitmq_publisher.py
│   │   │   └── interfaces/
│   │   │       └── api/
│   │   │           ├── routes.py
│   │   │           └── schemas.py
│   │   ├── alembic/
│   │   ├── main.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── alert-service/             # Alerts & Violations Service
│   │   ├── src/
│   │   │   ├── domain/
│   │   │   │   ├── entities/
│   │   │   │   │   ├── violation.py
│   │   │   │   │   └── alert_config.py
│   │   │   │   ├── value_objects/
│   │   │   │   │   ├── severity.py
│   │   │   │   │   └── threshold.py
│   │   │   │   ├── services/
│   │   │   │   │   ├── threshold_checker.py
│   │   │   │   │   └── notification_service.py
│   │   │   │   └── events/
│   │   │   │       └── alert_events.py
│   │   │   ├── application/
│   │   │   │   ├── commands/
│   │   │   │   │   ├── create_violation_command.py
│   │   │   │   │   └── resolve_violation_command.py
│   │   │   │   ├── queries/
│   │   │   │   │   └── get_violations_query.py
│   │   │   │   └── services/
│   │   │   │       └── alert_application_service.py
│   │   │   ├── infrastructure/
│   │   │   │   ├── persistence/
│   │   │   │   └── messaging/
│   │   │   │       └── event_consumers.py  # Listens to SensorReadingCreated
│   │   │   └── interfaces/
│   │   │       └── api/
│   │   ├── main.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── air-quality-service/       # AQI & Maps Service
│   │   ├── src/
│   │   │   ├── domain/
│   │   │   │   ├── entities/
│   │   │   │   │   └── air_quality_index.py
│   │   │   │   ├── value_objects/
│   │   │   │   │   ├── aqi_level.py
│   │   │   │   │   └── pollutant.py
│   │   │   │   └── services/
│   │   │   │       ├── aqi_calculator.py
│   │   │   │       └── prediction_service.py
│   │   │   ├── application/
│   │   │   │   ├── queries/
│   │   │   │   │   ├── get_current_aqi_query.py
│   │   │   │   │   ├── get_forecast_query.py
│   │   │   │   │   └── get_map_data_query.py
│   │   │   │   └── services/
│   │   │   │       └── air_quality_application_service.py
│   │   │   ├── infrastructure/
│   │   │   │   ├── external/
│   │   │   │   │   └── google_maps_client.py
│   │   │   │   └── cache/
│   │   │   │       └── redis_cache.py
│   │   │   └── interfaces/
│   │   │       └── api/
│   │   ├── main.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── user-service/              # Authentication & Users Service
│   │   ├── src/
│   │   │   ├── domain/
│   │   │   │   ├── entities/
│   │   │   │   │   ├── user.py
│   │   │   │   │   └── role.py
│   │   │   │   ├── value_objects/
│   │   │   │   │   ├── email.py
│   │   │   │   │   └── password.py
│   │   │   │   └── services/
│   │   │   │       └── auth_service.py
│   │   │   ├── application/
│   │   │   │   ├── commands/
│   │   │   │   │   ├── register_user_command.py
│   │   │   │   │   └── login_command.py
│   │   │   │   └── queries/
│   │   │   │       └── get_user_query.py
│   │   │   ├── infrastructure/
│   │   │   │   └── persistence/
│   │   │   └── interfaces/
│   │   │       └── api/
│   │   ├── main.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   └── shared/                    # Shared Libraries
│       ├── events/                # Shared event definitions
│       │   ├── __init__.py
│       │   ├── base_event.py
│       │   ├── factory_events.py
│       │   ├── sensor_events.py
│       │   └── alert_events.py
│       ├── messaging/             # RabbitMQ utilities
│       │   ├── __init__.py
│       │   ├── publisher.py
│       │   └── consumer.py
│       ├── auth/                  # JWT utilities
│       │   ├── __init__.py
│       │   └── jwt_handler.py
│       └── utils/
│           ├── __init__.py
│           └── exceptions.py
│
├── frontend/                      # 🔷 FRONTEND (React)
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── common/
│   │   │   ├── layout/
│   │   │   ├── maps/
│   │   │   ├── charts/
│   │   │   ├── factories/
│   │   │   ├── alerts/
│   │   │   └── sensors/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/              # API calls (through gateway)
│   │   │   ├── api.js
│   │   │   ├── factoryApi.js
│   │   │   ├── sensorApi.js
│   │   │   └── alertApi.js
│   │   ├── store/
│   │   └── utils/
│   ├── Dockerfile
│   ├── nginx.conf                 # Nginx for serving frontend
│   ├── package.json
│   └── vite.config.js
│
└── scripts/
    ├── init-databases.sh          # Initialize all databases
    ├── seed-data.py               # Seed sample data
    └── simulate-sensors.py        # Sensor data simulator
```

---

## Docker Compose Configuration

### Services Overview

| Service | Port | Database | Description |
|---------|------|----------|-------------|
| api-gateway | 8000 | - | Routes requests, auth, rate limiting |
| factory-service | 8001 | factory_db:5432 | Factory management |
| sensor-service | 8002 | sensor_db:5433 | Sensors & readings |
| alert-service | 8003 | alert_db:5434 | Violations & alerts |
| air-quality-service | 8004 | Redis:6379 | AQI, maps, predictions |
| user-service | 8005 | user_db:5435 | Authentication |
| rabbitmq | 5672, 15672 | - | Message broker |
| frontend | 3000 | - | React web app |

---

## Domain Events

### Event Flow Example: Sensor Reading → Violation

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Sensor Service │     │    RabbitMQ     │     │  Alert Service  │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         │  1. New Reading       │                       │
         │──────────────────────>│                       │
         │                       │                       │
         │  Publish:             │  2. Route Event       │
         │  SensorReadingCreated │──────────────────────>│
         │                       │                       │
         │                       │                       │  3. Check Thresholds
         │                       │                       │  4. If exceeded:
         │                       │                       │     Create Violation
         │                       │  5. Publish:          │
         │                       │<──────────────────────│
         │                       │  ViolationDetected    │
         │                       │                       │
┌────────┴────────┐              │              ┌────────┴────────┐
│ Factory Service │<─────────────│              │ Notification    │
│ (Update Status) │              │              │ (Email/SMS)     │
└─────────────────┘              │              └─────────────────┘
```

### Event Definitions

```python
# shared/events/base_event.py
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

@dataclass
class DomainEvent:
    event_id: UUID
    occurred_at: datetime
    event_type: str
    
    def __post_init__(self):
        if self.event_id is None:
            self.event_id = uuid4()
        if self.occurred_at is None:
            self.occurred_at = datetime.utcnow()

# shared/events/sensor_events.py
@dataclass
class SensorReadingCreated(DomainEvent):
    sensor_id: UUID
    factory_id: UUID
    pm25: float
    pm10: float
    aqi: int
    timestamp: datetime
    event_type: str = "sensor.reading.created"

# shared/events/alert_events.py
@dataclass
class ViolationDetected(DomainEvent):
    violation_id: UUID
    factory_id: UUID
    pollutant: str
    measured_value: float
    threshold: float
    severity: str
    event_type: str = "alert.violation.detected"

@dataclass
class FactorySuspended(DomainEvent):
    factory_id: UUID
    reason: str
    suspended_by: UUID
    event_type: str = "factory.suspended"
```

---

## DDD Code Examples

### Entity Example (Factory)

```python
# services/factory-service/src/domain/entities/factory.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from ..value_objects.location import Location
from ..value_objects.factory_status import FactoryStatus
from ..value_objects.emission_limit import EmissionLimits
from ..events.factory_events import FactoryCreated, FactoryStatusChanged

@dataclass
class Factory:
    """Factory Entity - has identity and lifecycle"""
    
    id: UUID
    name: str
    registration_number: str
    industry_type: str
    location: Location
    emission_limits: EmissionLimits
    status: FactoryStatus = field(default_factory=lambda: FactoryStatus.ACTIVE)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    _events: list = field(default_factory=list, repr=False)
    
    @classmethod
    def create(cls, name: str, registration_number: str, industry_type: str,
               latitude: float, longitude: float, emission_limits: dict) -> 'Factory':
        """Factory method to create new Factory"""
        factory = cls(
            id=uuid4(),
            name=name,
            registration_number=registration_number,
            industry_type=industry_type,
            location=Location(latitude=latitude, longitude=longitude),
            emission_limits=EmissionLimits.from_dict(emission_limits)
        )
        factory._events.append(FactoryCreated(factory_id=factory.id, name=name))
        return factory
    
    def suspend(self, reason: str) -> None:
        """Business rule: Suspend factory operations"""
        if self.status == FactoryStatus.SUSPENDED:
            raise ValueError("Factory is already suspended")
        
        old_status = self.status
        self.status = FactoryStatus.SUSPENDED
        self.updated_at = datetime.utcnow()
        self._events.append(FactoryStatusChanged(
            factory_id=self.id,
            old_status=old_status.value,
            new_status=self.status.value,
            reason=reason
        ))
    
    def resume(self) -> None:
        """Business rule: Resume factory operations"""
        if self.status != FactoryStatus.SUSPENDED:
            raise ValueError("Factory is not suspended")
        
        self.status = FactoryStatus.ACTIVE
        self.updated_at = datetime.utcnow()
    
    def update_status_from_emissions(self, current_aqi: int) -> None:
        """Business rule: Update status based on AQI"""
        if self.status == FactoryStatus.SUSPENDED:
            return  # Don't change if suspended
            
        if current_aqi > 200:
            self.status = FactoryStatus.CRITICAL
        elif current_aqi > 150:
            self.status = FactoryStatus.WARNING
        else:
            self.status = FactoryStatus.ACTIVE
    
    def collect_events(self) -> list:
        """Collect and clear domain events"""
        events = self._events.copy()
        self._events.clear()
        return events
```

### Value Object Example

```python
# services/factory-service/src/domain/value_objects/location.py
from dataclasses import dataclass

@dataclass(frozen=True)  # Immutable
class Location:
    """Value Object - no identity, compared by attributes"""
    
    latitude: float
    longitude: float
    
    def __post_init__(self):
        if not -90 <= self.latitude <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        if not -180 <= self.longitude <= 180:
            raise ValueError("Longitude must be between -180 and 180")
    
    def distance_to(self, other: 'Location') -> float:
        """Calculate distance to another location (simplified)"""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # Earth's radius in km
        lat1, lon1 = radians(self.latitude), radians(self.longitude)
        lat2, lon2 = radians(other.latitude), radians(other.longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
```

### Repository Interface & Implementation

```python
# services/factory-service/src/domain/repositories/factory_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ..entities.factory import Factory

class FactoryRepository(ABC):
    """Repository Interface (Port) - defined in domain layer"""
    
    @abstractmethod
    async def get_by_id(self, factory_id: UUID) -> Optional[Factory]:
        pass
    
    @abstractmethod
    async def get_by_registration_number(self, reg_number: str) -> Optional[Factory]:
        pass
    
    @abstractmethod
    async def list_all(self, status: Optional[str] = None, 
                       skip: int = 0, limit: int = 20) -> List[Factory]:
        pass
    
    @abstractmethod
    async def save(self, factory: Factory) -> Factory:
        pass
    
    @abstractmethod
    async def delete(self, factory_id: UUID) -> bool:
        pass


# services/factory-service/src/infrastructure/persistence/factory_repository_impl.py
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...domain.entities.factory import Factory
from ...domain.repositories.factory_repository import FactoryRepository
from ...domain.value_objects.location import Location
from ...domain.value_objects.factory_status import FactoryStatus
from ...domain.value_objects.emission_limit import EmissionLimits
from .models import FactoryModel

class SQLAlchemyFactoryRepository(FactoryRepository):
    """Repository Implementation (Adapter) - in infrastructure layer"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, factory_id: UUID) -> Optional[Factory]:
        result = await self.session.execute(
            select(FactoryModel).where(FactoryModel.id == factory_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def save(self, factory: Factory) -> Factory:
        model = self._to_model(factory)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)
    
    def _to_entity(self, model: FactoryModel) -> Factory:
        """Map database model to domain entity"""
        return Factory(
            id=model.id,
            name=model.name,
            registration_number=model.registration_number,
            industry_type=model.industry_type,
            location=Location(latitude=model.latitude, longitude=model.longitude),
            emission_limits=EmissionLimits.from_dict(model.max_emissions),
            status=FactoryStatus(model.operational_status),
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _to_model(self, entity: Factory) -> FactoryModel:
        """Map domain entity to database model"""
        return FactoryModel(
            id=entity.id,
            name=entity.name,
            registration_number=entity.registration_number,
            industry_type=entity.industry_type,
            latitude=entity.location.latitude,
            longitude=entity.location.longitude,
            max_emissions=entity.emission_limits.to_dict(),
            operational_status=entity.status.value,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
```

### Application Service (Use Case)

```python
# services/factory-service/src/application/services/factory_application_service.py
from typing import Optional, List
from uuid import UUID

from ...domain.entities.factory import Factory
from ...domain.repositories.factory_repository import FactoryRepository
from ..commands.create_factory_command import CreateFactoryCommand
from ..commands.suspend_factory_command import SuspendFactoryCommand
from ..dto.factory_dto import FactoryDTO
from ..interfaces.event_publisher import EventPublisher

class FactoryApplicationService:
    """Application Service - orchestrates use cases"""
    
    def __init__(
        self, 
        factory_repository: FactoryRepository,
        event_publisher: EventPublisher
    ):
        self.factory_repository = factory_repository
        self.event_publisher = event_publisher
    
    async def create_factory(self, command: CreateFactoryCommand) -> FactoryDTO:
        """Use Case: Create a new factory"""
        # Check if registration number already exists
        existing = await self.factory_repository.get_by_registration_number(
            command.registration_number
        )
        if existing:
            raise ValueError(f"Factory with registration {command.registration_number} already exists")
        
        # Create domain entity
        factory = Factory.create(
            name=command.name,
            registration_number=command.registration_number,
            industry_type=command.industry_type,
            latitude=command.latitude,
            longitude=command.longitude,
            emission_limits=command.emission_limits
        )
        
        # Persist
        saved_factory = await self.factory_repository.save(factory)
        
        # Publish domain events
        for event in saved_factory.collect_events():
            await self.event_publisher.publish(event)
        
        return FactoryDTO.from_entity(saved_factory)
    
    async def suspend_factory(self, command: SuspendFactoryCommand) -> FactoryDTO:
        """Use Case: Suspend factory operations"""
        factory = await self.factory_repository.get_by_id(command.factory_id)
        if not factory:
            raise ValueError(f"Factory {command.factory_id} not found")
        
        # Domain logic
        factory.suspend(reason=command.reason)
        
        # Persist
        saved_factory = await self.factory_repository.save(factory)
        
        # Publish events
        for event in saved_factory.collect_events():
            await self.event_publisher.publish(event)
        
        return FactoryDTO.from_entity(saved_factory)
    
    async def get_factory(self, factory_id: UUID) -> Optional[FactoryDTO]:
        """Use Case: Get factory by ID"""
        factory = await self.factory_repository.get_by_id(factory_id)
        return FactoryDTO.from_entity(factory) if factory else None
    
    async def list_factories(
        self, status: Optional[str] = None, skip: int = 0, limit: int = 20
    ) -> List[FactoryDTO]:
        """Use Case: List factories with optional filter"""
        factories = await self.factory_repository.list_all(status, skip, limit)
        return [FactoryDTO.from_entity(f) for f in factories]
```

### API Controller

```python
# services/factory-service/src/interfaces/api/factory_controller.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from uuid import UUID

from ...application.services.factory_application_service import FactoryApplicationService
from ...application.commands.create_factory_command import CreateFactoryCommand
from ...application.commands.suspend_factory_command import SuspendFactoryCommand
from .schemas import (
    FactoryCreateRequest, 
    FactoryResponse, 
    FactoryListResponse,
    SuspendRequest
)
from .dependencies import get_factory_service

router = APIRouter(prefix="/factories", tags=["factories"])

@router.post("", response_model=FactoryResponse, status_code=status.HTTP_201_CREATED)
async def create_factory(
    request: FactoryCreateRequest,
    service: FactoryApplicationService = Depends(get_factory_service)
):
    """Create a new factory"""
    command = CreateFactoryCommand(
        name=request.name,
        registration_number=request.registration_number,
        industry_type=request.industry_type,
        latitude=request.latitude,
        longitude=request.longitude,
        emission_limits=request.max_emissions
    )
    try:
        factory_dto = await service.create_factory(command)
        return FactoryResponse.from_dto(factory_dto)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=FactoryListResponse)
async def list_factories(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    service: FactoryApplicationService = Depends(get_factory_service)
):
    """List all factories with optional status filter"""
    factories = await service.list_factories(status, skip, limit)
    return FactoryListResponse(data=factories, total=len(factories))

@router.get("/{factory_id}", response_model=FactoryResponse)
async def get_factory(
    factory_id: UUID,
    service: FactoryApplicationService = Depends(get_factory_service)
):
    """Get factory by ID"""
    factory = await service.get_factory(factory_id)
    if not factory:
        raise HTTPException(status_code=404, detail="Factory not found")
    return FactoryResponse.from_dto(factory)

@router.post("/{factory_id}/suspend", response_model=FactoryResponse)
async def suspend_factory(
    factory_id: UUID,
    request: SuspendRequest,
    service: FactoryApplicationService = Depends(get_factory_service)
):
    """Suspend factory operations"""
    command = SuspendFactoryCommand(
        factory_id=factory_id,
        reason=request.reason,
        suspended_by=request.suspended_by
    )
    try:
        factory_dto = await service.suspend_factory(command)
        return FactoryResponse.from_dto(factory_dto)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## API Gateway Routes

```python
# services/api-gateway/src/routes/factory_routes.py
from fastapi import APIRouter, Request, HTTPException
from ..utils.service_client import ServiceClient

router = APIRouter(prefix="/api/v1/factories", tags=["factories"])
factory_client = ServiceClient(base_url="http://factory-service:8001")

@router.get("")
async def list_factories(request: Request):
    """Proxy to Factory Service"""
    return await factory_client.get("/factories", params=dict(request.query_params))

@router.post("")
async def create_factory(request: Request):
    body = await request.json()
    return await factory_client.post("/factories", json=body)

@router.get("/{factory_id}")
async def get_factory(factory_id: str):
    return await factory_client.get(f"/factories/{factory_id}")

@router.post("/{factory_id}/suspend")
async def suspend_factory(factory_id: str, request: Request):
    body = await request.json()
    return await factory_client.post(f"/factories/{factory_id}/suspend", json=body)
```

---

## Frontend API Service

```javascript
// frontend/src/services/api.js
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  timeout: 10000,
});

// Request interceptor for auth
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

---

## Environment Variables

```bash
# .env.example

# API Gateway
API_GATEWAY_PORT=8000
JWT_SECRET=your-super-secret-key

# Factory Service
FACTORY_SERVICE_PORT=8001
FACTORY_DB_URL=postgresql://user:pass@factory-db:5432/factory_db

# Sensor Service
SENSOR_SERVICE_PORT=8002
SENSOR_DB_URL=postgresql://user:pass@sensor-db:5433/sensor_db

# Alert Service
ALERT_SERVICE_PORT=8003
ALERT_DB_URL=postgresql://user:pass@alert-db:5434/alert_db

# Air Quality Service
AIR_QUALITY_SERVICE_PORT=8004
REDIS_URL=redis://redis:6379

# User Service
USER_SERVICE_PORT=8005
USER_DB_URL=postgresql://user:pass@user-db:5435/user_db

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672
RABBITMQ_MANAGEMENT_PORT=15672

# Google Maps
VITE_GOOGLE_MAPS_API_KEY=your-google-maps-api-key

# Frontend
VITE_API_URL=http://localhost:8000/api/v1
```

---

## Commands Reference

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d factory-service

# View logs
docker-compose logs -f api-gateway
docker-compose logs -f factory-service

# Rebuild after changes
docker-compose build factory-service
docker-compose up -d factory-service

# Run migrations for a service
docker-compose exec factory-service alembic upgrade head

# Access RabbitMQ Management UI
# http://localhost:15672 (guest/guest)

# Stop all services
docker-compose down

# Remove all data (volumes)
docker-compose down -v
```

---

## Important Rules

1. **Use JavaScript** (.js, .jsx) for frontend
2. **Follow DDD layers**: Domain → Application → Infrastructure → Interface
3. **Domain layer has NO dependencies** on other layers
4. **Use Repository pattern** for data access
5. **Publish domain events** after state changes
6. **Each service owns its database** - no shared databases
7. **Communicate via events** for async operations
8. **API Gateway** is the single entry point
9. **PropTypes** for React component validation
10. **Test each service independently**

---

*This document is the single source of truth. Follow this architecture exactly.*

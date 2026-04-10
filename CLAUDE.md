# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

An **Air Quality Management Information System** built with microservice architecture and Domain-Driven Design (DDD). It monitors city air quality, tracks factory emissions, manages monitoring stations, and enables enforcement actions.

### Architecture

```
Clients (Web, Mobile, IoT)
         │
         ▼
   API Gateway (Port 8000) ─── JWT Auth, Rate Limiting, Routing
         │
   ┌─────┼──────┬──────────┬──────────┬──────────┬──────────┐
   ▼     ▼      ▼          ▼          ▼          ▼          ▼
Factory Sensor Alert  AirQuality  User   RemoteSensing Station
Service Service Service Service  Service    Service    Service
   │     │      │          │          │          │          │
   └─────┴──────┴──────────┴──────────┴──────────┴──────────┘
                              │
                    RabbitMQ (async events)
                    MySQL (per-service DBs)
                    Redis (cache)

Additional ingestion services (do not expose REST APIs):
  purpleair-ingestion-service  - Pulls data from PurpleAir cloud API
  purpleair-listener           - Listens to RabbitMQ for PurpleAir events
  station-ingestion-service    - Fetches from external station API (admin-qttd.tedp.vn)
  station-excel-fetcher        - Downloads Envisoft Excel reports → MySQL
  wrf-service                  - WRF weather model simulation (sample data mode by default)
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite + TailwindCSS + Zustand + Recharts |
| Backend | Python FastAPI (per microservice) |
| API Gateway | FastAPI + httpx (async HTTP client to backend services) |
| Database | MySQL 8.0 (one DB per service), Redis 7 |
| Message Broker | RabbitMQ 3.13 (async events) |
| Container | Docker Compose v2 (`docker compose`, space not hyphen) |

### Database Assignment

| Service | Database | Port |
|---------|----------|------|
| factory-service | factory_db | internal 3306 → host 3307 |
| sensor-service | sensor_db | internal 3306 |
| alert-service | alert_db | internal 3306 |
| user-service | user_db | internal 3306 |
| remote-sensing-service | remote_sensing_db | internal 3306 |
| station-service | station_db | internal 3306 |
| station-ingestion-service | station_ingestion_db | internal 3306 |
| wrf-service | wrf_db | internal 3306 |
| air-quality-service | (Redis cache only, no MySQL) | 6379 |

---

## Services Detail

### Core Microservices (REST APIs)

| Service | Port | Purpose |
|---------|------|---------|
| api-gateway | 8000 | Single entry point. Proxies all requests to backend services. Handles JWT validation and route forwarding. |
| factory-service | 8001 | Factories, emission limits, suspensions. Emits `FactoryCreated`, `FactorySuspended`, etc. |
| sensor-service | 8002 | Sensor registration, readings. Stores in MySQL with SQLAlchemy async. |
| alert-service | 8003 | Violations, alert thresholds. Consumes `SensorReadingCreated` from RabbitMQ. |
| air-quality-service | 8004 | AQI calculation, Google Maps, Redis cache. |
| user-service | 8005 | Auth, JWT tokens, user/role management. |
| remote-sensing-service | 8006 | Satellite data (Copernicus, NASA MODIS, Sentinel Hub), Excel import, data fusion. |
| station-service | 8007 | Official air quality monitoring stations. Emits station readings to RabbitMQ. |
| wrf-service | 8009 | Weather Research and Forecasting model. Runs in sample-data mode by default (`WRF_USE_SAMPLE_DATA=True`). |

### Ingestion Services (Background/Event-Driven)

| Service | Port | Purpose |
|---------|------|---------|
| purpleair-ingestion-service | 8008 | Polls PurpleAir cloud API (`api.purpleair.com`) for device readings. Publishes to RabbitMQ. |
| purpleair-listener | 8012 | Consumes PurpleAir events from RabbitMQ, syncs sensor data. |
| station-ingestion-service | 8010 | Fetches from `admin-qttd.tedp.vn/api/partner/v1`. Uses STATION_API_KEY from env. |
| station-excel-fetcher | 8011 | Cron-based Envisoft Excel download → parse → MySQL. Credentials in env. |

### Frontend

| Service | Port | Profile |
|---------|------|---------|
| frontend (nginx) | 3002 | Production build served by nginx |
| frontend-dev (vite) | 3002 | Hot-reload dev server (enabled with `docker compose --profile dev up -d`) |

---

## DDD Layer Convention

Every microservice follows this layer order (domain has zero dependencies on other layers):

```
domain/        → Entities, Value Objects, Repository interfaces, Domain Events
application/   → Commands, Queries, DTOs, Application Services
infrastructure/→ SQLAlchemy models, Repository implementations, RabbitMQ publisher/consumer
interfaces/    → FastAPI routers, Pydantic schemas, Event consumers
```

Domain events are published via `shared.messaging.RabbitMQPublisher` after state changes. Application services collect events from entities and dispatch them.

---

## Shared Libraries (`services/shared/`)

```
shared/
├── events/           # Dataclass event definitions (SensorReadingCreated, ViolationDetected, etc.)
├── messaging/        # RabbitMQPublisher, RabbitMQConsumer, exchange/queue config
├── auth/             # JWT decode, UserClaims model, auth dependencies
└── utils/            # Shared exceptions, helpers
```

---

## Frontend Architecture

```
frontend/src/
├── pages/          # Route-level page components
├── components/     # Feature components (factories/, sensors/, alerts/, maps/, charts/)
├── hooks/          # Shared React hooks
├── services/       # Axios API clients (api.js, factoryApi.js, sensorApi.js, alertApi.js)
├── store/          # Zustand stores
└── utils/
```

Frontend API calls go through the API Gateway: `http://localhost:8000/api/v1`. Auth token is stored in `localStorage` and injected via Axios request interceptor.

---

## Commands

### Docker (always `docker compose`, space not hyphen)

```bash
# Full stack (all 13 containers)
docker compose up -d

# Start with dev frontend (hot-reload)
docker compose --profile dev up -d

# Rebuild after code changes
docker compose build <service-name> && docker compose up -d <service-name>

# Logs
docker compose logs -f api-gateway
docker compose logs -f factory-service

# Database access
docker exec -it aqms-mysql mysql -u root -pMysql_2026 factory_db

# Stop (preserves data)
docker compose down

# Complete wipe (removes volumes)
docker compose down -v
```

### Backend Services (run inside containers)

```bash
# Python shell in running container
docker compose exec factory-service python -c "import sqlalchemy; print(sqlalchemy.__version__)"

# Run Alembic migrations (if using PostgreSQL-based services; MySQL uses create_all)
docker compose exec factory-service alembic upgrade head

# Seed sample data
python3 scripts/seed-data.py          # from host (requires httpx installed)
docker compose exec factory-service python /app/scripts/seed-data.py   # from container

# Simulate sensor readings (continuous)
python3 scripts/simulate-sensors.py
```

### Python Tests (per service)

Each service has `pytest` + `pytest-asyncio` installed. Tests use an in-memory repository stub that mocks `shared.*` imports without needing Docker.

```bash
# All tests for one service
docker compose exec <service-name> pytest /app/tests/ -v

# Single test file
docker compose exec factory-service pytest /app/tests/unit/test_factory_entity.py -v

# Single test function
docker compose exec factory-service pytest /app/tests/unit/test_factory_entity.py::test_suspend_factory_when_active -v

# From host (service directory)
cd services/factory-service
pip install -r requirements.txt
pytest tests/ -v
```

### Frontend

```bash
cd frontend

npm install
npm run dev          # Vite dev server on port 5173
npm run build        # Production build
npm run lint         # ESLint
npm run preview      # Preview production build
```

### Quick Health Check

```bash
for port in 8000 8001 8002 8003 8004 8005 8006 8007 8008 8009; do
  curl -s -o /dev/null -w "Port $port — HTTP %{http_code}\n" http://localhost:$port/health
done
```

---

## Code Conventions

- **Python**: async/await throughout. SQLAlchemy 2.0 with async session. Pydantic v2 for schemas and settings. Dataclasses for domain entities and events.
- **Frontend**: JavaScript (`.js`, `.jsx`). PropTypes for component validation. Zustand for state. TailwindCSS for styling.
- **API Gateway**: Uses `aiohttp.ClientSession` (not `httpx`) to call backend services asynchronously.
- **Tests**: `pytest-asyncio` for async Python tests. In-memory repository test doubles avoid needing Docker during unit tests. `conftest.py` bootstraps `shared.*` stubs into `sys.modules`.
- **Config**: All settings via `pydantic-settings` from env vars (`.env` → `docker-compose.yml` → container env).

---

## Important Rules

1. **Use `docker compose`** (v2, space) — NOT `docker-compose` (hyphenated v1)
2. **Domain layer is isolated** — it may not import from `infrastructure` or `interfaces`
3. **Publish domain events** after every state mutation via `RabbitMQPublisher`
4. **Each service owns its database** — no cross-service direct DB access
5. **API Gateway is the only public entry point** — frontend and external clients never call backend services directly
6. **Use JavaScript** (`.js/.jsx`) for frontend — not TypeScript
7. **Test services independently** via `docker compose exec <svc> pytest`
8. **The WRF service defaults to sample-data mode** — real WRF requires binaries mounted separately
9. **Ingestion services run continuously** — they have no REST API (purpleair-ingestion, purpleair-listener, station-ingestion, station-excel-fetcher)
10. **MySQL is shared** — all services connect to `mysql:3306` inside Docker; host port is 3307

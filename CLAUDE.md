# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working in this repository.

---

## Project Overview

Air Quality Management Information System — microservice architecture with DDD. Monitors city air quality, tracks factory emissions, manages monitoring stations, and enables enforcement actions.

```
Clients (Web, Mobile, IoT)
         │
   API Gateway (8000) ─── JWT Auth, Rate Limiting, Routing
         │
  ┌──────┼──────┬───────┬───────┬───────┬───────┬───────┐
  ▼      ▼      ▼       ▼       ▼       ▼       ▼       ▼
Factory Sensor Alert  AirQuality  User  RemoteSensing Station WRF
(8001)  (8002) (8003)  (8004)  (8005)   (8006)      (8009)
                            │              │
                   RabbitMQ (async events)
                   MySQL 8.0 (per-service DBs)
                   Redis (cache)
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite + TailwindCSS + Zustand + Recharts |
| Backend | Python FastAPI (async, per microservice) |
| API Gateway | FastAPI + `aiohttp.ClientSession` |
| Database | MySQL 8.0 (one DB per service), Redis 7 |
| Message Broker | RabbitMQ 3.13 |
| Container | Docker Compose v2 (`docker compose`, space not hyphen) |

---

## Services

### REST API Services (ports)

| Service | Host Port | Database | Purpose |
|---------|----------|----------|---------|
| api-gateway | 8000 | — | Single entry point, proxies to all backend services |
| factory-service | 8001 | factory_db | Factories, emission limits, suspensions |
| sensor-service | 8002 | sensor_db | Sensor registration, readings |
| alert-service | 8003 | alert_db | Violations, alert thresholds |
| air-quality-service | 8004 | Redis only | AQI calculation, data fusion, Redis cache |
| user-service | 8005 | user_db | Auth, JWT tokens, roles |
| remote-sensing-service | 8006 | remote_sensing_db | Satellite data, Excel import |
| station-service | 8007 | station_db | Official monitoring stations |
| wrf-service | 8009 | wrf_db | WRF weather model (sample-data mode by default) |

### Ingestion Services (no REST API)

| Service | Host Port | Purpose |
|---------|----------|---------|
| purpleair-ingestion-service | 8008 | Polls PurpleAir cloud API → RabbitMQ |
| purpleair-listener | 8012 | Consumes PurpleAir events → MySQL |
| station-ingestion-service | 8010 | Fetches from `admin-qttd.tedp.vn` |
| station-excel-fetcher | 8011 | Downloads Envisoft Excel → MySQL |

### Databases (auto-created by `scripts/init-mysql.sql`)

`factory_db`, `sensor_db`, `alert_db`, `user_db`, `remote_sensing_db`, `station_db`, `station_ingestion_db`, `wrf_db`, `station_excel_fetcher_db`

MySQL inside Docker is `mysql:3306`; host port is **3307** (3306 is free for local MySQL).

### Frontend

| Service | Port | Description |
|---------|------|-------------|
| frontend (nginx) | 3000 | Production build |
| frontend-dev (vite) | 3002 | Hot-reload dev (use `docker compose --profile dev up -d`) |

---

## DDD Layer Convention

Every backend service follows this layer order — **domain has zero dependencies** on other layers:

```
domain/       → Entities, Value Objects, Repository interfaces, Domain Events
application/  → Commands, Queries, DTOs, Application Services
infrastructure/→ SQLAlchemy models, Repository implementations, RabbitMQ publisher/consumer
interfaces/   → FastAPI routers, Pydantic schemas, Event consumers
```

Domain events are published via `shared.messaging.RabbitMQPublisher` after state changes. Application services collect events from entities and dispatch them.

---

## Shared Libraries (`services/shared/`)

```
shared/
├── events/      # Dataclass definitions: SensorReadingCreated, ViolationDetected,
│                # FactoryCreated, FactorySuspended, SatelliteDataFetched, etc.
├── messaging/   # RabbitMQPublisher, RabbitMQConsumer, config (exchanges/queues)
├── auth/        # JWT decode, UserClaims model, auth dependencies
└── utils/       # Shared exceptions, helpers
```

---

## RabbitMQ Topology (from `shared/messaging/config.py`)

**5 topic exchanges**: `factory.events`, `sensor.events`, `alert.events`, `satellite.events`, `fusion.events`

Key routing keys: `sensor.reading.created`, `alert.violation.detected`, `alert.violation.resolved`, `factory.suspended`, `factory.resumed`, `satellite.data.fetched`, `fusion.completed`, `validation.alert`

The consumer in `shared/messaging/consumer.py` declares ALL 5 exchanges on connect — `FUSION_EXCHANGE` and `SATELLITE_EXCHANGE` must be in `_ALL_EXCHANGES`.

---

## Entry Points

- **Backend services**: `uvicorn src.interfaces.api.routes:app --host 0.0.0.0 --port <port>`
- **api-gateway**: `uvicorn src.main:app --host 0.0.0.0 --port 8000`
- All services: multi-stage Dockerfiles with non-root user + `PYTHONUNBUFFERED=1`

---

## Commands

### Docker (always `docker compose`, space not hyphen)

```bash
docker compose up -d                        # Full stack
docker compose --profile dev up -d         # With hot-reload frontend
docker compose build <service> && docker compose up -d <service>   # Rebuild after changes
docker compose logs -f <service>            # Tail logs
docker compose exec <service> python -c "..."  # Run Python in container
docker compose down                          # Stop (preserves data)
docker compose down -v                      # Complete wipe (removes volumes)
```

### Database Access (MySQL host port is 3307)

```bash
docker exec -it aqms-mysql mysql -u root -pMysql_2026 factory_db
```

### Seed Data

```bash
python3 scripts/seed-data.py                # from host (needs httpx)
docker compose exec factory-service python /app/scripts/seed-data.py  # from container
python3 scripts/simulate-sensors.py        # continuous sensor simulation
```

### Python Tests (per service, no Docker needed)

```bash
# Inside container
docker compose exec <service> pytest /app/tests/ -v

# Single test file / function
docker compose exec factory-service pytest /app/tests/unit/test_factory_entity.py -v
docker compose exec factory-service pytest /app/tests/unit/test_factory_entity.py::test_suspend_factory_when_active -v

# From host
cd services/factory-service && pip install -r requirements.txt && pytest tests/ -v
```

### Frontend

```bash
cd frontend
npm install
npm run dev          # Vite dev server on port 5173 (proxied to 3000)
npm run build        # Production build
npm run lint         # ESLint
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
- **Frontend**: JavaScript (`.js`, `.jsx`) — **NOT TypeScript**. PropTypes for validation. Zustand for state. TailwindCSS for styling.
- **API Gateway**: Uses `aiohttp.ClientSession` (not `httpx`) to call backend services asynchronously.
- **Tests**: `pytest-asyncio` for async Python tests. In-memory repository test doubles mock `shared.*` imports via `conftest.py` (no Docker required for unit tests).
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
9. **Ingestion services run continuously** — they have no REST API
10. **MySQL is shared** — all services connect to `mysql:3306` inside Docker; host port is **3307**

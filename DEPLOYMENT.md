# Air Quality Management System — Deployment Guide

A step-by-step guide to deploy the full system on a new machine from scratch.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Get the Source Code](#2-get-the-source-code)
3. [Configure Environment Variables](#3-configure-environment-variables)
4. [Build and Start All Services](#4-build-and-start-all-services)
5. [Verify the Deployment](#5-verify-the-deployment)
6. [Database Tables Setup](#6-database-tables-setup)
7. [Seed Sample Data (Optional)](#7-seed-sample-data-optional)
8. [Access the Application](#8-access-the-application)
9. [Common Commands](#9-common-commands)
10. [Troubleshooting](#10-troubleshooting)
11. [Port Reference](#11-port-reference)

---

## 1. Prerequisites

### Required Software

Install the following on the new machine before proceeding.

#### Docker Engine (v24+)
```bash
# Ubuntu / Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to the docker group (avoids needing sudo for every command)
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version
# Expected: Docker version 29.x.x or higher
```

#### Docker Compose (v2.20+)
Docker Compose v2 is included with Docker Engine since version 24. Verify:
```bash
docker compose version
# Expected: Docker Compose version v2.x.x
```

> **Note:** Use `docker compose` (with a space), not the old `docker-compose` (with a hyphen).

#### Git
```bash
# Ubuntu / Debian
sudo apt install git -y

# Verify
git --version
```

### System Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| RAM | 4 GB | 8 GB |
| Disk | 10 GB free | 20 GB free |
| OS | Ubuntu 20.04+ / Windows WSL2 / macOS 12+ | Ubuntu 22.04 LTS |

### Port Availability

The following host ports must be free before deploying:

| Port | Service |
|------|---------|
| 3000 | Frontend (React UI) |
| 8000 | API Gateway |
| 8001 | Factory Service |
| 8002 | Sensor Service |
| 8003 | Alert Service |
| 8004 | Air Quality Service |
| 8005 | User Service |
| 8006 | Remote Sensing Service |
| 3307 | MySQL (host-side) |
| 5672 | RabbitMQ (AMQP) |
| 15672 | RabbitMQ Management UI |
| 6379 | Redis |

> **Important:** MySQL inside Docker runs on port 3306 internally. The host port is mapped to **3307** to avoid conflicts with any local MySQL installation. If your machine also has port 3307 in use, change `MYSQL_PORT=3307` in the `.env` file to another free port (e.g., `3308`).

---

## 2. Get the Source Code

```bash
# Clone the repository
git clone <your-repository-url> air-quality-management-system
cd air-quality-management-system
```

If you received the project as a ZIP archive:
```bash
unzip air-quality-management-system.zip
cd air-quality-management-system
```

---

## 3. Configure Environment Variables

Copy the example environment file and edit it:
```bash
cp .env.example .env
```

Open `.env` in any text editor and update the values below.

### Minimum Required Changes

```bash
# ── Security (REQUIRED — change before first start) ──────────────────────────
JWT_SECRET=replace-this-with-a-long-random-string-at-least-32-chars

# ── MySQL Database ────────────────────────────────────────────────────────────
MYSQL_ROOT_PASSWORD=Mysql_2026      # MySQL root password
MYSQL_PORT=3307                     # Host port (change if 3307 is already in use)

# ── RabbitMQ ──────────────────────────────────────────────────────────────────
RABBITMQ_USER=guest
RABBITMQ_PASS=guest

# ── Frontend API URL ──────────────────────────────────────────────────────────
VITE_API_URL=http://localhost:8000/api/v1

# ── Log Level ─────────────────────────────────────────────────────────────────
LOG_LEVEL=INFO          # Use DEBUG for development, INFO for production
```

### Optional API Keys

These are needed for external integrations. Leave blank to skip:
```bash
GOOGLE_MAPS_API_KEY=         # Google Maps for air quality map view
COPERNICUS_ADS_API_KEY=      # Copernicus satellite data
NASA_EARTHDATA_TOKEN=        # NASA MODIS satellite data
SENTINEL_HUB_CLIENT_ID=      # Sentinel Hub imagery
SENTINEL_HUB_CLIENT_SECRET=
```

### City Bounding Box (Hanoi defaults)

Used by the remote sensing service to define the monitored geographic area:
```bash
CITY_BBOX_NORTH=21.1
CITY_BBOX_SOUTH=20.9
CITY_BBOX_EAST=105.9
CITY_BBOX_WEST=105.7
```

> Change these coordinates to match your city if needed.

---

## 4. Build and Start All Services

### Step 1 — Build all Docker images

This downloads base images and installs all Python/Node dependencies. The first build takes 5–15 minutes depending on your internet speed. Subsequent builds are much faster thanks to Docker layer caching.

```bash
docker compose build
```

To force a complete rebuild from scratch (clears all cache):
```bash
docker compose build --no-cache
```

### Step 2 — Start all services

```bash
docker compose up -d
```

Docker Compose starts containers in the correct dependency order:
1. MySQL, RabbitMQ, Redis (infrastructure)
2. All 6 microservices (wait for MySQL/RabbitMQ to be healthy)
3. API Gateway (waits for all 6 microservices)
4. Frontend / nginx (waits for API Gateway)

The entire stack takes about **60–90 seconds** to be fully healthy after `up -d`.

---

## 5. Verify the Deployment

### Check container status
```bash
docker compose ps
```

All containers should show `(healthy)` in the STATUS column:
```
NAME                          STATUS
aqms-mysql                    Up X minutes (healthy)
aqms-rabbitmq                 Up X minutes (healthy)
aqms-redis                    Up X minutes (healthy)
aqms-factory-service          Up X minutes (healthy)
aqms-sensor-service           Up X minutes (healthy)
aqms-alert-service            Up X minutes (healthy)
aqms-air-quality-service      Up X minutes (healthy)
aqms-user-service             Up X minutes (healthy)
aqms-remote-sensing-service   Up X minutes (healthy)
aqms-api-gateway              Up X minutes (healthy)
aqms-frontend                 Up X minutes (healthy)
```

### Quick health check — all services at once
```bash
for port in 8000 8001 8002 8003 8004 8005 8006; do
  status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/health)
  service=$(curl -s http://localhost:$port/health | python3 -c "import sys,json; print(json.load(sys.stdin).get('service','ok'))" 2>/dev/null)
  echo "Port $port — HTTP $status — $service"
done
```

Expected output:
```
Port 8000 — HTTP 200 — api-gateway
Port 8001 — HTTP 200 — factory-service
Port 8002 — HTTP 200 — sensor-service
Port 8003 — HTTP 200 — alert-service
Port 8004 — HTTP 200 — air-quality-service
Port 8005 — HTTP 200 — user-service
Port 8006 — HTTP 200 — remote-sensing-service
```

### Check the frontend
```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000/
# Expected: 200
```

### View logs if something is wrong
```bash
# Tail logs for all services
docker compose logs -f

# Tail logs for a specific service
docker compose logs -f factory-service
docker compose logs -f api-gateway
docker compose logs -f mysql
```

---

## 6. Database Tables Setup

On first startup, each service **automatically creates its own database tables** (via SQLAlchemy `create_all`). No manual migration step is required for a fresh deployment.

The 5 databases are created automatically by MySQL on first startup via `scripts/init-mysql.sql`:
- `factory_db`
- `sensor_db`
- `alert_db`
- `user_db`
- `remote_sensing_db`

### Verify databases were created
```bash
docker exec aqms-mysql mysql -u root -pMysql_2026 -e "SHOW DATABASES;"
```

Expected output includes all 5 service databases.

### Running Alembic migrations (optional — for future schema changes)

If you need to run database migrations manually (e.g., after a schema update):
```bash
# Factory Service
docker compose exec factory-service alembic upgrade head

# Sensor Service
docker compose exec sensor-service alembic upgrade head

# Alert Service
docker compose exec alert-service alembic upgrade head

# User Service
docker compose exec user-service alembic upgrade head

# Remote Sensing Service
docker compose exec remote-sensing-service alembic upgrade head
```

---

## 7. Seed Sample Data (Optional)

Load sample factories, sensors, and readings to test the UI immediately:
```bash
docker compose exec factory-service python /app/scripts/seed-data.py 2>/dev/null || \
  python3 scripts/seed-data.py
```

Or run it from the host (requires Python 3 and `httpx` installed):
```bash
pip3 install httpx
python3 scripts/seed-data.py
```

Simulate real-time sensor readings (runs continuously):
```bash
python3 scripts/simulate-sensors.py
```

---

## 8. Access the Application

| URL | Description |
|-----|-------------|
| `http://localhost:3000` | **Main Web Application** (React UI) |
| `http://localhost:8000/api/v1/docs` | **API Gateway** — Swagger UI (all routes) |
| `http://localhost:8001/docs` | Factory Service — Swagger UI |
| `http://localhost:8002/docs` | Sensor Service — Swagger UI |
| `http://localhost:8003/docs` | Alert Service — Swagger UI |
| `http://localhost:8004/docs` | Air Quality Service — Swagger UI |
| `http://localhost:8005/docs` | User Service — Swagger UI |
| `http://localhost:8006/docs` | Remote Sensing Service — Swagger UI |
| `http://localhost:15672` | **RabbitMQ Management UI** (user: `guest` / pass: `guest`) |

### First Login

Open `http://localhost:3000` and register a new admin account via the UI, or use the API:

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "Admin@12345",
    "full_name": "System Administrator",
    "role": "ADMIN"
  }' | python3 -m json.tool
```

---

## 9. Common Commands

### Start / Stop / Restart

```bash
# Start the full stack
docker compose up -d

# Stop all containers (data is preserved)
docker compose down

# Stop and delete all data (fresh start)
docker compose down -v

# Restart a single service (e.g., after a code change)
docker compose restart factory-service

# Rebuild a single service image and restart it
docker compose build factory-service && docker compose up -d factory-service
```

### Logs

```bash
# Follow logs for all services
docker compose logs -f

# Follow logs for one service
docker compose logs -f api-gateway

# Show last 100 lines without following
docker compose logs --tail=100 user-service
```

### Database Access

```bash
# Open MySQL CLI in the container
docker exec -it aqms-mysql mysql -u root -pMysql_2026

# Connect to a specific database
docker exec -it aqms-mysql mysql -u root -pMysql_2026 factory_db

# Run a quick query
docker exec aqms-mysql mysql -u root -pMysql_2026 -e "SELECT COUNT(*) FROM factory_db.factories;"
```

### RabbitMQ

```bash
# List all queues and message counts
docker exec aqms-rabbitmq rabbitmqctl list_queues name messages consumers
```

### Reset Everything (complete wipe)

```bash
# Stop containers, remove volumes, remove images
docker compose down -v --rmi local
```

---

## 10. Troubleshooting

### Container keeps restarting

```bash
# Check what's wrong
docker compose logs --tail=50 <service-name>
```

### Port already in use

```bash
# Find what is using the port (example: 3307)
sudo lsof -i :3307
# or
sudo ss -tlnp | grep 3307
```

Edit `.env` and change the conflicting port variable, then restart:
```bash
docker compose down
docker compose up -d
```

**Common conflict:** If your machine already has MySQL running on port 3306, the MySQL container is mapped to `3307` by default. If port `3307` is also taken, set `MYSQL_PORT=3308` (or any free port) in `.env`.

### Service shows `(unhealthy)`

```bash
# Step 1: check logs
docker compose logs --tail=50 <service-name>

# Step 2: inspect health check details
docker inspect aqms-<service-name> | python3 -c \
  "import sys,json; s=json.load(sys.stdin)[0]; h=s['State']['Health']; \
   [print(l['Output']) for l in h.get('Log',[])]"

# Step 3: restart the service
docker compose restart <service-name>
```

### Cannot connect to MySQL

The services connect to MySQL using the **internal Docker network name** `mysql` on port `3306`. This is different from the host-side port `3307`. If you need to connect from your host machine (e.g., MySQL Workbench), use:
- Host: `127.0.0.1`
- Port: `3307` (or whatever `MYSQL_PORT` is set to in `.env`)
- User: `root`
- Password: `Mysql_2026`

### Build fails with "network timeout"

Retry the build. Large packages (rasterio, netcdf4) can time out on slow connections:
```bash
docker compose build --no-cache
```

### Out of disk space

```bash
# Remove unused Docker objects (safe — only removes stopped containers / dangling images)
docker system prune

# More aggressive cleanup (removes all unused images)
docker system prune -a
```

### Windows / WSL2 Notes

- Make sure Docker Desktop is running before you open WSL2.
- Clone the repository inside the WSL2 filesystem (`~/` or `/home/username/`), **not** inside `/mnt/c/`. File I/O from Windows drives is very slow.
- Ensure the WSL2 integration is enabled in Docker Desktop → Settings → Resources → WSL Integration.

---

## 11. Port Reference

### Host → Container mapping

| Host Port | Container Port | Service | Container Name |
|-----------|---------------|---------|---------------|
| 3000 | 80 | Frontend (nginx) | aqms-frontend |
| 8000 | 8000 | API Gateway | aqms-api-gateway |
| 8001 | 8001 | Factory Service | aqms-factory-service |
| 8002 | 8002 | Sensor Service | aqms-sensor-service |
| 8003 | 8003 | Alert Service | aqms-alert-service |
| 8004 | 8004 | Air Quality Service | aqms-air-quality-service |
| 8005 | 8005 | User Service | aqms-user-service |
| 8006 | 8006 | Remote Sensing Service | aqms-remote-sensing-service |
| **3307** | 3306 | MySQL 8.0 | aqms-mysql |
| 5672 | 5672 | RabbitMQ (AMQP) | aqms-rabbitmq |
| 15672 | 15672 | RabbitMQ Management | aqms-rabbitmq |
| 6379 | 6379 | Redis | aqms-redis |

### Internal Docker network

All containers communicate on the `aqms-network` bridge network using service names as hostnames (e.g., `mysql:3306`, `rabbitmq:5672`, `redis:6379`).

---

## Quick Reference Card

```
┌──────────────────────────────────────────────────────────────────┐
│              AQMS — Quick Start (copy-paste)                     │
├──────────────────────────────────────────────────────────────────┤
│  git clone <repo-url> aqms && cd aqms                            │
│  cp .env.example .env                                            │
│  # edit .env — set JWT_SECRET and MYSQL_ROOT_PASSWORD            │
│  docker compose build                                            │
│  docker compose up -d                                            │
│  # wait ~90 seconds, then:                                       │
│  docker compose ps          # all should show (healthy)          │
│  open http://localhost:3000 # Web UI                             │
│  open http://localhost:8000/api/v1/docs  # Swagger API docs      │
└──────────────────────────────────────────────────────────────────┘
```

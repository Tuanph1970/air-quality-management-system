# Remote Server Deployment Guide

This guide walks you through deploying the Air Quality Management System to a remote server.

---

## Prerequisites

- Ubuntu/Debian server (recommended) with **root or sudo access**
- Docker & Docker Compose v2 installed
- Git installed
- Domain name pointed to server IP (optional, for production)

---

## Step 1 — Install Docker (if not already installed)

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose-v2
sudo systemctl enable docker
sudo usermod -aG docker $USER
# Log out and back in for group changes to take effect
```

---

## Step 2 — Clone the Repository

```bash
# First-time setup only
git clone https://github.com/YOUR_USERNAME/air-quality-management-system.git
cd air-quality-management-system
```

```bash
# For subsequent deployments
cd air-quality-management-system
git pull
```

---

## Step 3 — Deploy

Run the deploy script with `--prod` flag and set your secrets:

```bash
./deploy.sh --prod \
  -e DB_PASSWORD="$(openssl rand -hex 24)" \
  -e JWT_SECRET="$(openssl rand -hex 32)" \
  -e RABBITMQ_PASS="$(openssl rand -hex 24)" \
  -e REDIS_PASSWORD="$(openssl rand -hex 24)" \
  -e ENVISOFT_BASIC_PASS=your_envisoft_password \
  -e ENVISOFT_FORM_PASS=your_envisoft_password
```

> **Note**: The first time you deploy, you will be prompted to confirm if any required secrets are still empty. You can type `y` to proceed or `n` to abort and set the values first.

---

## Step 4 — Verify Deployment

```bash
# Check running containers
docker compose -f docker-compose.prod.yml ps

# Check logs for a specific service
docker compose -f docker-compose.prod.yml logs -f station-excel-fetcher
```

### Service Endpoints

| Service | URL |
|---------|-----|
| Frontend | `http://<your-server-ip>` |
| API Gateway | `http://<your-server-ip>/api/v1` |
| API Docs (Swagger) | `http://<your-server-ip>/api/v1/docs` |
| RabbitMQ Management | `http://<your-server-ip>:15672` |

---

## Common Operations

### Stop all services
```bash
docker compose -f docker-compose.prod.yml down
```

### Restart all services
```bash
docker compose -f docker-compose.prod.yml restart
```

### Rebuild a specific service after code changes
```bash
git pull
./deploy.sh --prod --no-cache \
  -e DB_PASSWORD="$(openssl rand -hex 24)" \
  -e JWT_SECRET="$(openssl rand -hex 32)" \
  -e RABBITMQ_PASS="$(openssl rand -hex 24)" \
  -e REDIS_PASSWORD="$(openssl rand -hex 24)" \
  -e ENVISOFT_BASIC_PASS=your_envisoft_password \
  -e ENVISOFT_FORM_PASS=your_envisoft_password
```

### Access a service's database
```bash
docker exec -it aqms-factory-db psql -U aqms_admin -d factory_db
```

### View logs for all services
```bash
docker compose -f docker-compose.prod.yml logs -f
```

### View logs for a specific service
```bash
docker compose -f docker-compose.prod.yml logs -f api-gateway
docker compose -f docker-compose.prod.yml logs -f station-excel-fetcher
```

---

## Environment Variables Reference

All production variables are documented in `.env.prod`. Key secrets that **must** be set:

| Variable | Description | Generate |
|----------|-------------|----------|
| `DB_PASSWORD` | PostgreSQL password | `openssl rand -hex 24` |
| `JWT_SECRET` | JWT signing key (min 32 chars) | `openssl rand -hex 32` |
| `RABBITMQ_PASS` | RabbitMQ password | `openssl rand -hex 24` |
| `REDIS_PASSWORD` | Redis password | `openssl rand -hex 24` |
| `ENVISOFT_BASIC_PASS` | Envisoft HTTP Basic Auth | Provided by Envisoft |
| `ENVISOFT_FORM_PASS` | Envisoft Form Login | Provided by Envisoft |

---

## Data Persistence

All databases and Redis data are stored in **Docker named volumes** and persist across restarts:

```
factory_db_data
sensor_db_data
alert_db_data
user_db_data
remote_sensing_db_data
station_db_data
wrf_db_data
station_excel_fetcher_db_data
station_excel_fetcher_data
redis_data
rabbitmq_data
ml_models_data
satellite_data
```

To **completely wipe** all data:
```bash
docker compose -f docker-compose.prod.yml down -v
```

---

## Troubleshooting

### Service is unhealthy

```bash
# Check logs
docker compose -f docker-compose.prod.yml logs <service-name>

# Example
docker compose -f docker-compose.prod.yml logs api-gateway
```

### Port already in use

If port `80`, `443`, or `5672` conflicts with another service:
```bash
# Check what's using port 80
sudo ss -tlnp | grep :80

# Kill the conflicting process or change the port in .env.prod
```

### Out of disk space

```bash
# Clean up unused Docker resources
docker system prune -af --volumes
```

### Database connection issues

```bash
# Check if database containers are healthy
docker compose -f docker-compose.prod.yml ps | grep -E "db|-db"

# Restart database first
docker compose -f docker-compose.prod.yml restart factory-db
```

---

## Updating to New Versions

```bash
cd air-quality-management-system
git pull                          # Pull latest code
./deploy.sh --prod \
  -e DB_PASSWORD="$(openssl rand -hex 24)" \
  -e JWT_SECRET="$(openssl rand -hex 32)" \
  -e RABBITMQ_PASS="$(openssl rand -hex 24)" \
  -e REDIS_PASSWORD="$(openssl rand -hex 24)" \
  -e ENVISOFT_BASIC_PASS=your_envisoft_password \
  -e ENVISOFT_FORM_PASS=your_envisoft_password
```

> **Important**: Pass the same secret values each time. If you generate new passwords, the existing database volumes will no longer be accessible (encrypted with old passwords).

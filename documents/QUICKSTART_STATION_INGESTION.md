# Quick Start - Station Ingestion Service

## Overview
The Station Ingestion Service fetches environmental monitoring data from the external API (admin-qttd.tedp.vn) and makes it available to the frontend.

## Quick Start

### 1. Configure Environment

Add these variables to your `.env` file:

```bash
# Station Ingestion Service
STATION_API_BASE_URL=https://admin-qttd.tedp.vn/api/partner/v1
STATION_API_KEY=c9e03048-46e1-40b0-9b6b-f12accef9f5a
STATION_INGESTION_PORT=8010
FETCH_INTERVAL_SECONDS=300
AQI_HOURS_PAGE_SIZE=100

# Frontend
VITE_STATION_INGESTION_API_URL=http://localhost:8010/api/v1
```

### 2. Deploy with Script

```bash
# Full deployment (all services)
./deploy.sh

# Or start only the station-ingestion-service
docker-compose up -d station-ingestion-service
```

### 3. Verify Service is Running

```bash
# Check service status
docker-compose ps station-ingestion-service

# View logs
docker-compose logs -f station-ingestion-service

# Test health endpoint
curl http://localhost:8010/api/v1/health
```

### 4. Access the Frontend

1. Open browser: `http://localhost:3000/stations`
2. Click "Sync Data" to fetch initial data from the external API
3. Click on any station card to view details

## Manual Data Sync

```bash
# Sync stations list
curl -X POST http://localhost:8010/api/v1/sync/stations

# Sync AQI data (last 24 hours)
curl -X POST "http://localhost:8010/api/v1/sync/aqi?hours=24"
```

## API Endpoints

### Get All Stations
```bash
curl http://localhost:8010/api/v1/stations
```

### Get Station by Code
```bash
curl http://localhost:8010/api/v1/stations/LSOS_KHIKHO
```

### Get Station Readings (24 hours)
```bash
curl "http://localhost:8010/api/v1/stations/LSOS_KHIKHO/readings"
```

### Get Time Series for All Stations
```bash
curl "http://localhost:8010/api/v1/readings/timeseries"
```

## Troubleshooting

### Service Won't Start

Check logs:
```bash
docker-compose logs station-ingestion-service
```

Common issues:
- MySQL not running: `docker-compose up -d mysql`
- Database not created: Service auto-creates tables on first run

### No Data Showing

1. Check external API connection:
```bash
curl -H "X-API-KEY: c9e03048-46e1-40b0-9b6b-f12accef9f5a" \
  "https://admin-qttd.tedp.vn/api/partner/v1/get-automation-stations?page=0&size=10&apiType=1"
```

2. Manually trigger sync:
```bash
curl -X POST http://localhost:8010/api/v1/sync/stations
curl -X POST "http://localhost:8010/api/v1/sync/aqi?hours=24"
```

### Database Issues

Connect to MySQL:
```bash
docker-compose exec mysql mysql -uroot -pMysql_2026
```

Check tables:
```sql
USE station_ingestion_db;
SHOW TABLES;
SELECT COUNT(*) FROM stations;
SELECT COUNT(*) FROM air_quality_readings;
```

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `FETCH_INTERVAL_SECONDS` | 300 | How often to fetch new data (seconds) |
| `AQI_HOURS_PAGE_SIZE` | 100 | Number of records per API page |
| `STATION_API_BASE_URL` | https://admin-qttd.tedp.vn/api/partner/v1 | External API URL |
| `STATION_API_KEY` | c9e03048-... | External API authentication |

## Background Data Fetcher

The service automatically fetches data every 5 minutes. To run a dedicated fetcher:

```bash
docker-compose exec station-ingestion-service python scripts/data_fetcher.py
```

## Stopping the Service

```bash
# Stop only this service
docker-compose stop station-ingestion-service

# Or use undeploy script (removes everything)
./undeploy.sh
```

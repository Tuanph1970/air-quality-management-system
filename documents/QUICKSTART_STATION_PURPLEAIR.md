# Quick Start Guide - Station Service & PurpleAir Integration

## New Services Overview

This implementation adds two new microservices to the Air Quality Management System:

### 1. Station Service (Port 8007)
- **Purpose**: Manage air quality monitoring stations
- **Data**: SO2, NOX, CO, PM25, PM10, O3, NO2, CO2
- **Features**: API configuration, automatic data collection, fake data generation

### 2. PurpleAir Ingestion Service (Port 8008)
- **Purpose**: Receive data from PurpleAir Flex-Air Quality Monitors
- **Features**: Webhook endpoint, cloud API polling, fake data generator

---

## Quick Start

### 1. Configure Environment

Add to your `.env` file:
```bash
# Station Service
STATION_SERVICE_PORT=8007
USE_FAKE_DATA=True
FAKE_DATA_STATION_COUNT=5

# PurpleAir
PURPLEAIR_INGESTION_PORT=8008
PURPLEAIR_USE_FAKE_DATA=True
```

### 2. Start Services

```bash
# Build and start all services
docker compose build
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f station-service
docker compose logs -f purpleair-ingestion-service
```

### 3. Access API Documentation

- **Station Service**: http://localhost:8007/docs
- **PurpleAir Service**: http://localhost:8008/docs
- **API Gateway**: http://localhost:8000/api/v1/docs

---

## Usage Examples

### Create a Station

```bash
curl -X POST http://localhost:8000/api/v1/stations \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Downtown Monitoring Station",
    "station_code": "EPA-001",
    "station_type": "URBAN",
    "latitude": 21.0285,
    "longitude": 105.8542,
    "data_retention_days": 1
  }'
```

### Configure Station API

```bash
# Get station ID from previous response
STATION_ID="your-station-id"

curl -X POST "http://localhost:8000/api/v1/stations/${STATION_ID}/configure-api" \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint": "https://api.example.com/stations/123/readings",
    "method": "GET",
    "adapter_type": "generic",
    "poll_interval_seconds": 300
  }'
```

### Activate Station

```bash
curl -X POST "http://localhost:8000/api/v1/stations/${STATION_ID}/activate"
```

### Record Readings (Webhook/Manual)

```bash
curl -X POST "http://localhost:8000/api/v1/stations/${STATION_ID}/record-readings" \
  -H "Content-Type: application/json" \
  -d '{
    "readings": {
      "PM25": 35.5,
      "PM10": 50.0,
      "SO2": 10.0,
      "NOX": 40.0,
      "CO": 5.2,
      "O3": 60.0
    },
    "source": "MANUAL"
  }'
```

### Get Station Readings

```bash
curl "http://localhost:8000/api/v1/stations/${STATION_ID}/readings/latest"
```

### Generate Fake Data (Station Service)

```bash
# Via API - creates fake stations and submits readings
curl "http://localhost:8007/api/v1/stations/nearby?latitude=21.0285&longitude=105.8542&radius_km=50"

# Or run the fake data generator script
docker compose exec station-service python scripts/fake_data_generator.py
```

### PurpleAir Webhook

```bash
# Simulate PurpleAir device sending data
curl -X POST http://localhost:8008/api/v1/purpleair/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": 12345,
    "api_key": "test-key",
    "latitude": 21.0285,
    "longitude": 105.8542,
    "data": {
      "pm2_5": 35.5,
      "pm10_0": 50.0,
      "pm1_0": 25.0,
      "temperature": 28.5,
      "humidity": 65.0,
      "pressure": 1013.25,
      "ozone": 0.05,
      "no2": 0.03,
      "co": 0.5
    }
  }'
```

### Generate Fake PurpleAir Data

```bash
curl http://localhost:8008/api/v1/purpleair/fake-data?count=5
```

---

## Health Checks

```bash
# Station Service
curl http://localhost:8007/health
# Expected: {"status": "healthy", "service": "station-service", "version": "1.0.0"}

# PurpleAir Service
curl http://localhost:8008/health
# Expected: {"status": "healthy", "service": "purpleair-ingestion-service", "version": "1.0.0"}
```

---

## Architecture Verification

### Check All Services Running

```bash
docker compose ps
```

Expected output should include:
- `aqms-station-service` - (healthy)
- `aqms-purpleair-ingestion-service` - (healthy)

### Check RabbitMQ Events

```bash
# Access RabbitMQ Management UI
open http://localhost:15672
# Login: guest / guest
# Check queues for station.* and purpleair.* events
```

### Check Database

```bash
# Access MySQL
docker exec -it aqms-mysql mysql -u root -pMysql_2026

# Use station database
USE station_db;

# List stations
SELECT id, station_code, name, station_type, is_active FROM stations;

# List recent readings
SELECT station_id, pollutant_type, value, timestamp 
FROM pollutant_readings 
ORDER BY timestamp DESC 
LIMIT 10;
```

---

## Common Issues & Solutions

### Service Won't Start

```bash
# Check logs
docker compose logs station-service

# Common issues:
# 1. Database not ready - wait for MySQL health check
# 2. Port conflict - check .env for correct port mapping
# 3. RabbitMQ connection - verify rabbitmq is healthy
```

### Database Not Created

```bash
# Manually create database
docker exec -it aqms-mysql mysql -u root -pMysql_2026 -e "CREATE DATABASE IF NOT EXISTS station_db;"
```

### Fake Data Not Generating

```bash
# Check environment variable
docker compose exec station-service env | grep FAKE

# Should show:
# USE_FAKE_DATA=True
# FAKE_DATA_STATION_COUNT=5
```

---

## Next Steps

1. **Configure Real Stations**: Set up API endpoints for actual air quality stations
2. **PurpleAir Device Setup**: Configure physical PurpleAir devices to send to your webhook URL
3. **AQI Integration**: Verify air-quality-service receives and processes events
4. **Alert Configuration**: Set up alert thresholds for station readings
5. **Dashboard Integration**: Add station data to frontend dashboard

---

## Documentation

- Full implementation details: `documents/STATION_SERVICE_IMPLEMENTATION.md`
- API Gateway routes: http://localhost:8000/api/v1/docs
- Original project docs: `DEPLOYMENT.md`, `documents/CLAUDE.md`

---

## Support

For issues or questions:
1. Check service logs: `docker compose logs -f <service-name>`
2. Review API documentation: http://localhost:8007/docs or http://localhost:8008/docs
3. Check RabbitMQ events: http://localhost:15672

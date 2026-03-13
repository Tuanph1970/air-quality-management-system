# Quick Start Guide - PurpleAir Cloud Polling Integration

## Overview

This guide covers the complete setup for integrating PurpleAir Flex-Air sensors with your Air Quality Management System using **cloud API polling** and **event-driven architecture**.

### Architecture

```
┌─────────────────┐     Polling      ┌──────────────────┐
│  PurpleAir Cloud│◄─────────────────│ Ingestion Service│
│  (api.purpleair)│                  │  (Port 8008)     │
└─────────────────┘                  └────────┬─────────┘
                                             │
                                             │ Publish Event
                                             │ (purpleair.data.ingested)
                                             ▼
                                    ┌──────────────────┐
                                    │   RabbitMQ       │
                                    │   (amq.topic)    │
                                    └────────┬─────────┘
                                             │
                                             │ Consume Event
                                             │ (purpleair.*)
                                             ▼
                                    ┌──────────────────┐
                                    │  Event Listener  │
                                    │  (New Service)   │
                                    └────────┬─────────┘
                                             │
                                             │ HTTP API Call
                                             ▼
┌─────────────────┐                  ┌──────────────────┐
│   Frontend      │◄─────────────────│  Sensor Service  │
│   (Port 3000)   │   HTTP API       │  (Port 8002)     │
└─────────────────┘                  └────────┬─────────┘
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │   MySQL          │
                                    │   (sensor_db)    │
                                    └──────────────────┘
```

### Components

| Service | Port | Purpose |
|---------|------|---------|
| `purpleair-ingestion-service` | 8008 | Polls PurpleAir cloud API, publishes events |
| `purpleair-listener` | - | Consumes events, registers sensors, submits readings |
| `sensor-service` | 8002 | Manages sensors and readings, provides API for frontend |
| `frontend` | 3000 | Displays sensors and data |

---

## Quick Start

### 1. Configure Environment

Add to your `.env` file:

```bash
# =============================================================================
# PurpleAir Cloud Polling Configuration
# =============================================================================

# Your PurpleAir API key (get from https://www.purpleair.com/)
PURPLEAIR_API_KEY=your-purpleair-api-key

# List of sensors to poll (JSON format)
# Supports up to 10 sensors, configurable via environment
PURPLEAIR_SENSORS=[
  {
    "sensor_id": 12345,
    "api_key": "your-sensor-api-key",
    "name": "Home Sensor",
    "latitude": 21.0285,
    "longitude": 105.8542
  }
]

# Polling interval in hours (default: 2 hours)
PURPLEAIR_POLLING_INTERVAL_HOURS=2

# Directory for raw data storage (inside container)
PURPLEAIR_RAW_DATA_DIR=/app/data/purpleair/raw

# Disable fake data for production
PURPLEAIR_USE_FAKE_DATA=False
```

### 2. Start Services

```bash
# Build all services (including new purpleair-listener)
docker compose build

# Start all services
docker compose up -d

# Check status
docker compose ps
```

Expected services:
- `aqms-purpleair-ingestion-service` (healthy)
- `aqms-purpleair-listener` (healthy)
- `aqms-sensor-service` (healthy)
- `aqms-mysql` (healthy)
- `aqms-rabbitmq` (healthy)

### 3. Verify Services

```bash
# Check ingestion service health
curl http://localhost:8008/health

# Check sensor service health
curl http://localhost:8002/health

# View logs
docker compose logs -f purpleair-ingestion-service
docker compose logs -f purpleair-listener
```

---

## Adding Sensors

### Method 1: Environment Variable (Recommended for Initial Setup)

1. **Edit `.env`:**
   ```bash
   PURPLEAIR_SENSORS=[
     {"sensor_id": 12345, "api_key": "key1", "name": "Home"},
     {"sensor_id": 67890, "api_key": "key2", "name": "Office"}
   ]
   ```

2. **Restart service:**
   ```bash
   docker compose restart purpleair-ingestion-service
   ```

### Method 2: API (Dynamic Addition)

```bash
# Add a sensor via API
curl -X POST http://localhost:8008/api/v1/purpleair/sensors \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": 12345,
    "api_key": "your-api-key",
    "name": "Home Sensor",
    "latitude": 21.0285,
    "longitude": 105.8542
  }'

# List all configured sensors
curl http://localhost:8008/api/v1/purpleair/sensors

# Trigger immediate polling
curl -X POST http://localhost:8008/api/v1/purpleair/poll-now
```

---

## Verify Data Flow

### 1. Check Raw Data

```bash
# Access the container
docker compose exec purpleair-ingestion-service ls -la /app/data/purpleair/raw/

# View latest raw data
docker compose exec purpleair-ingestion-service cat /app/data/purpleair/raw/*/2026-03/*.json | head -100
```

### 2. Check Registered Sensors

```bash
# List sensors in sensor-service
curl http://localhost:8002/sensors | jq .

# Look for PurpleAir sensors (serial_number starts with "PURPLEAIR-")
```

### 3. Check Readings

```bash
# Get a sensor's readings (replace {UUID} with actual sensor ID)
curl http://localhost:8002/sensors/{UUID}/readings | jq .

# Get latest reading
curl http://localhost:8002/sensors/{UUID}/readings/latest | jq .
```

### 4. Check RabbitMQ Events

1. Open RabbitMQ UI: http://localhost:15672 (guest/guest)
2. Go to **Queues** tab
3. Look for `purpleair.events` queue
4. Check message rates

### 5. Check Frontend

Open http://localhost:3000/sensors and verify:
- PurpleAir sensors appear in the list
- Sensor type shows "LOW_COST_PM"
- Status shows "online" after first reading

---

## Troubleshooting

### Sensors Not Appearing in Frontend

**Check 1: Event Listener Logs**
```bash
docker compose logs purpleair-listener | grep -i error
```

**Check 2: Sensor Service**
```bash
# Check if sensors are registered
curl http://localhost:8002/sensors | jq '.items[] | {id, serial_number, status}'
```

**Check 3: RabbitMQ Connection**
```bash
docker compose logs purpleair-listener | grep -i "rabbitmq\|connected"
```

### Polling Not Working

**Check Configuration:**
```bash
docker compose exec purpleair-ingestion-service env | grep PURPLEAIR
```

**Check Logs:**
```bash
docker compose logs -f purpleair-ingestion-service | grep -i "polling\|sensor"
```

**Manual Trigger:**
```bash
curl -X POST http://localhost:8008/api/v1/purpleair/poll-now
```

### Readings Not Submitted

**Check Listener Logs:**
```bash
docker compose logs -f purpleair-listener
```

Look for:
- "Processing event" messages
- "Successfully submitted reading" messages
- Error messages with HTTP status codes

**Check Sensor Service API:**
```bash
# Test sensor registration manually
curl -X POST http://localhost:8002/sensors \
  -H "Content-Type: application/json" \
  -d '{
    "serial_number": "PURPLEAIR-99999",
    "sensor_type": "LOW_COST_PM",
    "model": "PurpleAir Flex",
    "latitude": 21.0285,
    "longitude": 105.8542
  }'
```

---

## API Reference

### PurpleAir Ingestion Service (Port 8008)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/purpleair/sensors` | POST | Add sensor to polling list |
| `/api/v1/purpleair/sensors` | GET | List configured sensors |
| `/api/v1/purpleair/sensors/{id}` | DELETE | Remove sensor |
| `/api/v1/purpleair/sensors/{id}/fetch` | POST | Fetch single sensor |
| `/api/v1/purpleair/poll-now` | POST | Poll all sensors immediately |
| `/api/v1/purpleair/sensors/{id}/raw-data` | GET | Get latest raw data |
| `/health` | GET | Health check |

### Sensor Service (Port 8002)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sensors` | POST | Register new sensor |
| `/sensors` | GET | List all sensors |
| `/sensors/{id}` | GET | Get sensor details |
| `/sensors/{id}/readings` | POST | Submit reading |
| `/sensors/{id}/readings` | GET | Get sensor readings |
| `/sensors/{id}/readings/latest` | GET | Get latest reading |
| `/health` | GET | Health check |

---

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PURPLEAIR_API_KEY` | `""` | Global PurpleAir API key |
| `PURPLEAIR_SENSORS` | `[]` | JSON array of sensor configs |
| `PURPLEAIR_POLLING_INTERVAL_HOURS` | `2` | Hours between polling cycles |
| `PURPLEAIR_RAW_DATA_DIR` | `/app/data/purpleair/raw` | Raw data storage path |
| `PURPLEAIR_USE_FAKE_DATA` | `False` | Enable fake data mode |
| `RABBITMQ_URL` | `amqp://guest:guest@rabbitmq:5672/` | RabbitMQ connection |
| `SENSOR_SERVICE_URL` | `http://sensor-service:8002` | Sensor service endpoint |

### Sensor Configuration Format

```json
{
  "sensor_id": 12345,
  "api_key": "your-api-key",
  "name": "Home Sensor",
  "latitude": 21.0285,
  "longitude": 105.8542
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `sensor_id` | Yes | PurpleAir sensor ID (numeric) |
| `api_key` | Yes | API key for this sensor |
| `name` | No | Friendly name |
| `latitude` | No | Sensor latitude (auto-fetched if not provided) |
| `longitude` | No | Sensor longitude (auto-fetched if not provided) |

---

## Data Flow Example

1. **Polling** (every 2 hours):
   ```
   purpleair-ingestion-service → api.purpleair.com/v1/sensors/12345
   ```

2. **Raw Data Storage**:
   ```
   /app/data/purpleair/raw/12345/2026-03/2026-03-14_12345.json
   ```

3. **Event Publishing**:
   ```json
   {
     "event_type": "purpleair.data.ingested",
     "purpleair_sensor_id": 12345,
     "readings": {"PM25": 35.5, "PM10": 50.0, ...},
     "timestamp": "2026-03-14T10:30:00Z"
   }
   ```

4. **Event Consumption**:
   ```
   purpleair-listener consumes event → registers sensor (if new) → submits reading
   ```

5. **Database Storage**:
   ```sql
   INSERT INTO sensor_readings (sensor_id, pm25, pm10, aqi, timestamp)
   VALUES ('uuid-...', 35.5, 50.0, 101, '2026-03-14 10:30:00');
   ```

6. **Frontend Display**:
   ```
   Frontend GET /sensors → Display sensor list with readings
   ```

---

## Next Steps

1. **Configure Real Sensors**: Add your actual PurpleAir sensor IDs and API keys
2. **Set Up Alerts**: Configure alert thresholds in alert-service
3. **Dashboard Integration**: Add PurpleAir sensors to main dashboard
4. **Calibration**: Calibrate sensors against reference stations
5. **Monitoring**: Set up monitoring for the listener service

---

## Support

- **PurpleAir Setup Guide**: `documents/PURPLEAIR_SETUP_GUIDE.md`
- **API Documentation**: http://localhost:8008/docs
- **Sensor Service Docs**: http://localhost:8002/docs

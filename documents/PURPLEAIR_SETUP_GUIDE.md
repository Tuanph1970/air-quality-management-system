# PurpleAir Flex-Air Sensor Setup Guide

## Overview

This guide covers the complete setup process for connecting PurpleAir Flex-Air Quality Monitors to your Air Quality Management System (AQMS) using cloud API polling.

### PurpleAir Flex Specifications

| Feature | Specification |
|---------|---------------|
| **Sensors** | Dual PMS-6003 (PM1.0, PM2.5, PM10), BME688 (Temp, Humidity, Pressure, Gas) |
| **Connectivity** | WiFi 802.11b/g/n @ 2.4GHz |
| **Data Transmission** | Cloud API, Webhook, SD Card (optional) |
| **Power** | 5V USB Micro (0.18A continuous) |
| **Dimensions** | 3.5" x 3.5" x 5" (85mm x 85mm x 125mm) |
| **Operating Range** | -40°F to 185°F (-40°C to 85°C) |

---

## Table of Contents

1. [Hardware Setup](#1-hardware-setup)
2. [WiFi Configuration](#2-wifi-configuration)
3. [Obtaining API Key](#3-obtaining-api-key)
4. [Server Configuration](#4-server-configuration)
5. [Adding Sensors to AQMS](#5-adding-sensors-to-aqms)
6. [Verification & Testing](#6-verification--testing)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. Hardware Setup

### 1.1 Unboxing

Your PurpleAir Flex package includes:
- PurpleAir Flex monitor unit
- Mounting bracket and hardware
- USB cable (power supply NOT included)

### 1.2 Power Requirements

**Important:** The device requires a 5V USB power adapter with at least 1A output.

```
Power Specification:
- Input: 5V DC
- Current: 0.18A continuous, 600mA peak
- Connector: USB Micro
```

### 1.3 Physical Installation

1. **Choose Location:**
   - Outdoor: Mount under eaves or protective cover
   - Indoor: Place in open area away from direct airflow
   - Maintain 20cm clearance from walls/obstacles

2. **Mount the Device:**
   - Attach mounting bracket to wall/post
   - Slide monitor onto bracket
   - Ensure WiFi signal strength at location

3. **Connect Power:**
   - Plug USB cable into monitor
   - Connect to 5V power adapter
   - LED will blink blue during startup

---

## 2. WiFi Configuration

### 2.1 Initial Setup

1. **Power on the device** - LED blinks blue

2. **Connect to device WiFi:**
   - On your phone/computer, look for WiFi network: `PurpleAir-XXXX`
   - XXXX = last 4 digits of device MAC address
   - No password required for initial setup

3. **Open setup page:**
   - Browser will auto-redirect to setup page
   - If not, navigate to: `http://192.168.4.1`

### 2.2 Configure WiFi Connection

1. **Select your WiFi network** from the list
2. **Enter WiFi password** (WPA2 supported)
3. **Click "Connect"**

> **Note:** PurpleAir Flex only supports 2.4GHz WiFi networks. 5GHz networks are not compatible.

### 2.3 Verify Connection

- LED should turn solid green (WiFi connected)
- Device will appear on PurpleAir map within 5-10 minutes (if registered)

---

## 3. Obtaining API Key

### 3.1 Register Sensor on PurpleAir (Optional but Recommended)

1. Go to: https://www.purpleair.com/
2. Click "Login" → Create account or sign in
3. Navigate to: https://www.purpleair.com/map
4. Find your sensor (search by location or sensor ID)
5. Click on your sensor marker
6. Click "Claim This Sensor"
7. Follow verification process

### 3.2 Get API Key

**Method 1: From PurpleAir Account**

1. Login to https://www.purpleair.com/
2. Go to Account Settings → API Keys
3. Generate new API key or copy existing one
4. Save the key securely

**Method 2: From Sensor Page**

1. Go to your sensor page: `https://www.purpleair.com/sensors/{SENSOR_ID}`
2. Click "Settings" tab
3. Under "API Access", find your API key
4. Copy the key

### 3.3 Note Your Sensor ID

- Sensor ID is displayed on the device page
- Format: Numeric (e.g., `12345`)
- You'll need both Sensor ID and API Key for AQMS configuration

---

## 4. Server Configuration

### 4.1 Environment Variables

Add the following to your `.env` file:

```bash
# =============================================================================
# PurpleAir Cloud Polling Configuration
# =============================================================================

# Global PurpleAir API Key (fallback if sensor-specific key not provided)
PURPLEAIR_API_KEY=your-global-api-key

# List of sensors to poll (JSON format)
# Each sensor: sensor_id, api_key, name (optional), latitude, longitude (optional)
PURPLEAIR_SENSORS=[
  {
    "sensor_id": 12345,
    "api_key": "sensor-specific-api-key-1",
    "name": "Home Sensor",
    "latitude": 21.0285,
    "longitude": 105.8542
  },
  {
    "sensor_id": 67890,
    "api_key": "sensor-specific-api-key-2",
    "name": "Office Sensor"
  }
]

# Polling interval in hours (default: 2 hours)
PURPLEAIR_POLLING_INTERVAL_HOURS=2

# Directory for raw data storage
PURPLEAIR_RAW_DATA_DIR=./data/purpleair/raw

# Use fake data for testing (set to False in production)
PURPLEAIR_USE_FAKE_DATA=False
PURPLEAIR_FAKE_DATA_INTERVAL=60
```

### 4.2 Configuration Examples

**Single Sensor:**
```bash
PURPLEAIR_SENSORS=[{"sensor_id": 12345, "api_key": "abc123xyz", "name": "Home"}]
```

**Multiple Sensors (up to 10 recommended):**
```bash
PURPLEAIR_SENSORS=[
  {"sensor_id": 12345, "api_key": "key1", "name": "Home"},
  {"sensor_id": 67890, "api_key": "key2", "name": "Office"},
  {"sensor_id": 11111, "api_key": "key3", "name": "Factory"}
]
```

**Custom Polling Interval (4 hours):**
```bash
PURPLEAIR_POLLING_INTERVAL_HOURS=4
```

### 4.3 Apply Configuration

```bash
# Restart the PurpleAir ingestion service
docker compose restart purpleair-ingestion-service

# Check logs
docker compose logs -f purpleair-ingestion-service
```

---

## 5. Adding Sensors to AQMS

### 5.1 Via API (Recommended)

**Add a Sensor:**
```bash
curl -X POST http://localhost:8008/api/v1/purpleair/sensors \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": 12345,
    "api_key": "your-api-key",
    "name": "Home Sensor",
    "latitude": 21.0285,
    "longitude": 105.8542
  }'
```

**List All Sensors:**
```bash
curl http://localhost:8008/api/v1/purpleair/sensors
```

**Remove a Sensor:**
```bash
curl -X DELETE http://localhost:8008/api/v1/purpleair/sensors/12345
```

**Manually Trigger Polling:**
```bash
# Poll all sensors immediately
curl -X POST http://localhost:8008/api/v1/purpleair/poll-now

# Poll specific sensor
curl -X POST http://localhost:8008/api/v1/purpleair/sensors/12345/fetch
```

### 5.2 Via Environment Variable (Static Configuration)

1. Edit `.env` file
2. Update `PURPLEAIR_SENSORS` JSON array
3. Restart service:
   ```bash
   docker compose restart purpleair-ingestion-service
   ```

---

## 6. Verification & Testing

### 6.1 Check Service Health

```bash
curl http://localhost:8008/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "purpleair-ingestion-service",
  "version": "1.0.0"
}
```

### 6.2 View Service Logs

```bash
# Real-time logs
docker compose logs -f purpleair-ingestion-service

# Last 100 lines
docker compose logs --tail=100 purpleair-ingestion-service
```

Look for messages like:
```
Polling service started with 2 sensors (interval=2h)
Polling 2 sensors...
Processed sensor 12345 (Home Sensor): PM2.5=35.5, PM10=50.0
Polling complete: 2/2 sensors succeeded
```

### 6.3 Check Raw Data Storage

```bash
# Navigate to raw data directory
cd ./data/purpleair/raw

# List sensor folders
ls -la

# View latest data for sensor 12345
cat 12345/2026-03/*.json | jq .
```

Directory structure:
```
data/purpleair/raw/
├── 12345/
│   └── 2026-03/
│       ├── 2026-03-13_12345.json
│       └── 2026-03-14_12345.json
└── 67890/
    └── 2026-03/
        └── 2026-03-14_67890.json
```

### 6.4 Verify RabbitMQ Events

1. Open RabbitMQ Management UI: http://localhost:15672
2. Login: `guest` / `guest`
3. Go to "Queues" tab
4. Look for `aqms.events` queue
5. Check message rate during polling

### 6.5 Access API Documentation

Open in browser:
- **Service Docs:** http://localhost:8008/docs
- **API Gateway:** http://localhost:8000/api/v1/docs

---

## 7. Troubleshooting

### Problem: Sensor Not Polling

**Check 1: Configuration**
```bash
# Verify environment variables
docker compose exec purpleair-ingestion-service env | grep PURPLEAIR

# Check sensors are loaded
curl http://localhost:8008/api/v1/purpleair/sensors
```

**Check 2: API Key Validity**
```bash
# Test API connection manually
curl -H "X-API-Key: your-api-key" \
  https://api.purpleair.com/v1/sensors/12345
```

**Check 3: Service Logs**
```bash
docker compose logs purpleair-ingestion-service | grep -i error
```

### Problem: Invalid API Key

**Solution:**
1. Verify API key in PurpleAir account
2. Ensure key has not expired
3. Re-generate key if needed
4. Update `.env` and restart service

### Problem: No Data in Database

**Check 1: RabbitMQ Connection**
```bash
docker compose logs purpleair-ingestion-service | grep RabbitMQ
```

**Check 2: Event Publishing**
```bash
# Should see "Published event" messages
docker compose logs purpleair-ingestion-service | grep "Published event"
```

**Check 3: AQI Service**
```bash
# Check if AQI service is receiving events
docker compose logs air-quality-service | grep purpleair
```

### Problem: Raw Data Not Saved

**Check Directory Permissions:**
```bash
# Create directory manually if needed
mkdir -p ./data/purpleair/raw
chmod 755 ./data/purpleair/raw
```

**Check Configuration:**
```bash
# Verify PURPLEAIR_RAW_DATA_DIR setting
docker compose exec purpleair-ingestion-service env | grep RAW_DATA
```

### Problem: WiFi Connection Issues

1. **Verify 2.4GHz Network:**
   - PurpleAir Flex does not support 5GHz
   - Check router settings for 2.4GHz band

2. **Signal Strength:**
   - Move sensor closer to router during setup
   - Use WiFi analyzer app to check signal

3. **Reset Device:**
   - Press reset button for 10 seconds
   - Re-run WiFi setup from beginning

---

## Appendix A: API Reference

### Sensor Management Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/purpleair/sensors` | Add new sensor |
| `GET` | `/api/v1/purpleair/sensors` | List all sensors |
| `DELETE` | `/api/v1/purpleair/sensors/{id}` | Remove sensor |
| `POST` | `/api/v1/purpleair/sensors/{id}/fetch` | Fetch sensor data |
| `POST` | `/api/v1/purpleair/poll-now` | Poll all sensors |
| `GET` | `/api/v1/purpleair/sensors/{id}/raw-data` | Get raw data |

### Request/Response Examples

**Add Sensor Request:**
```json
{
  "sensor_id": 12345,
  "api_key": "your-api-key",
  "name": "Home Sensor",
  "latitude": 21.0285,
  "longitude": 105.8542
}
```

**List Sensors Response:**
```json
{
  "success": true,
  "count": 2,
  "sensors": [
    {
      "sensor_id": 12345,
      "api_key": "abc123...",
      "name": "Home Sensor",
      "latitude": 21.0285,
      "longitude": 105.8542
    }
  ]
}
```

---

## Appendix B: Data Format

### Raw Data Storage Format

```json
{
  "sensor_id": 12345,
  "stored_at": "2026-03-14T10:30:00Z",
  "reading_timestamp": "2026-03-14T10:28:00Z",
  "data": {
    "results": {
      "current_reading": {
        "pm2_5": 35.5,
        "pm10_0": 50.0,
        "pm1_0": 25.0,
        "temperature": 28.5,
        "humidity": 65.0,
        "pressure": 1013.25
      }
    }
  }
}
```

### Processed AQI Format (Internal)

```json
{
  "PM25": 35.5,
  "PM10": 50.0,
  "PM1": 25.0,
  "temperature": 28.5,
  "humidity": 65.0,
  "pressure": 1013.25,
  "O3": 0.05,
  "NO2": 0.03,
  "CO": 0.5
}
```

---

## Appendix C: Configuration Quick Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `PURPLEAIR_API_KEY` | `""` | Global fallback API key |
| `PURPLEAIR_SENSORS` | `[]` | JSON array of sensor configs |
| `PURPLEAIR_POLLING_INTERVAL_HOURS` | `2` | Hours between polls |
| `PURPLEAIR_RAW_DATA_DIR` | `./data/purpleair/raw` | Raw data storage path |
| `PURPLEAIR_USE_FAKE_DATA` | `False` | Enable fake data mode |

---

## Support

For additional help:
- PurpleAir Support: https://www2.purpleair.com/pages/support
- API Documentation: https://api.purpleair.com/
- AQMS Issues: Check service logs and RabbitMQ events

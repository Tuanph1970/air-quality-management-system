# Station Monitoring Feature - Implementation Summary

## Overview
This document summarizes the implementation of the Station Monitoring feature that integrates with the external environmental monitoring API (admin-qttd.tedp.vn).

## What Was Implemented

### 1. Backend Service: `station-ingestion-service`

**Location:** `/services/station-ingestion-service/`

#### Architecture
```
External API (admin-qttd.tedp.vn)
         ↓
  StationAPIClient
         ↓
  StationIngestionService
         ↓
  Repository (MySQL)
         ↓
  REST API → Frontend
```

#### Files Created

```
services/station-ingestion-service/
├── main.py                          # FastAPI application entry point
├── requirements.txt                 # Python dependencies
├── Dockerfile                       # Docker container definition
├── .env.example                     # Environment variables template
├── README.md                        # Service documentation
├── scripts/
│   ├── init_db.py                   # Database initialization
│   └── data_fetcher.py              # Background data sync scheduler
└── src/
    ├── __init__.py
    ├── core/
    │   └── config.py                # Configuration management
    ├── api/
    │   └── routes.py                # REST API endpoints
    ├── application/
    │   └── station_ingestion_service.py  # Business logic
    ├── domain/
    │   ├── entities/
    │   │   └── station.py           # Station & AirQualityReading entities
    │   └── repositories/
    │       └── station_repository.py  # Repository interface
    └── infrastructure/
        ├── external/
        │   └── station_api_client.py  # External API client
        └── persistence/
            ├── models.py            # SQLAlchemy database models
            └── station_repository_impl.py  # Repository implementation
```

#### External API Integration

**Endpoints Used:**
1. `/get-automation-stations` - Fetch station list
2. `/aqi_hours` - Fetch hourly AQI data

**Data Retrieved:**
- Station metadata (code, name, location, address)
- Air quality readings (AQI, PM2.5, PM10, CO, SO2, NO2, O3)
- Environmental data (Temperature, Humidity)

#### REST API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/stations` | GET | Get all stations with latest readings |
| `/api/v1/stations/:code` | GET | Get specific station |
| `/api/v1/stations/:code/readings` | GET | Get station readings (time range) |
| `/api/v1/readings/timeseries` | GET | Get all stations time series |
| `/api/v1/sync/stations` | POST | Trigger station sync |
| `/api/v1/sync/aqi` | POST | Trigger AQI data sync |
| `/api/v1/health` | GET | Health check |

#### Database Schema

**Tables:**
- `stations` - Station metadata
- `air_quality_readings` - Time-series readings

### 2. Frontend: Monitoring Stations Page

**Location:** `/frontend/src/`

#### Files Created/Modified

```
frontend/src/
├── pages/
│   └── StationsPage.jsx             # Main stations page (NEW)
├── components/
│   └── charts/
│       └── TimeSeriesChart.jsx      # Time series chart component (NEW)
├── services/
│   └── stationIngestionApi.js       # API client (NEW)
├── components/layout/
│   └── Sidebar.jsx                  # Added "Monitoring Stations" menu (MODIFIED)
└── App.jsx                          # Added /stations route (MODIFIED)
```

#### Features

1. **Station List View**
   - Grid layout with station cards
   - Search functionality
   - Real-time AQI display with color coding
   - Latest readings (PM2.5, PM10, O3)
   - Sync button for manual refresh

2. **Station Detail Panel**
   - Slide-out panel on station click
   - AQI badge with category (Good, Moderate, Unhealthy, etc.)
   - All pollutant values (CO, SO2, NO2, O3)
   - Environmental data (Temperature, Humidity)
   - Time series chart (24h)
   - Recent readings table

3. **Auto-refresh**
   - Background sync every 5 minutes
   - Manual sync button

### 3. Docker Compose Integration

**File Modified:** `docker-compose.yml`

Added `station-ingestion-service` service:
- Port: 8010
- Depends on: MySQL
- Health check enabled
- Auto-restart policy

### 4. Deployment Script

**File Modified:** `deploy.sh`

Added `station-ingestion-service` to health check list.

### 5. Configuration

**Files Modified:**
- `.env.example` - Added station ingestion variables
- `frontend/.env.example` (if exists) - Added VITE_STATION_INGESTION_API_URL

**Environment Variables:**
```bash
STATION_API_BASE_URL=https://admin-qttd.tedp.vn/api/partner/v1
STATION_API_KEY=c9e03048-46e1-40b0-9b6b-f12accef9f5a
STATION_INGESTION_PORT=8010
FETCH_INTERVAL_SECONDS=300
AQI_HOURS_PAGE_SIZE=100
VITE_STATION_INGESTION_API_URL=http://localhost:8010/api/v1
```

### 6. Documentation

**Files Created:**
- `documents/STATION_INGESTION_SERVICE.md` - Full service documentation
- `documents/QUICKSTART_STATION_INGESTION.md` - Quick start guide
- `services/station-ingestion-service/README.md` - Service README

## How to Use

### Deploy

```bash
# Using deploy script (recommended)
./deploy.sh

# Or start only this service
docker-compose up -d station-ingestion-service
```

### Access Frontend

1. Open browser: `http://localhost:3000/stations`
2. Click "Sync Data" to fetch initial data
3. Click any station card to view details

### API Usage

```bash
# Get all stations
curl http://localhost:8010/api/v1/stations

# Get station readings
curl "http://localhost:8010/api/v1/stations/LSOS_KHIKHO/readings"

# Trigger sync
curl -X POST http://localhost:8010/api/v1/sync/stations
curl -X POST "http://localhost:8010/api/v1/sync/aqi?hours=24"
```

## Data Flow

```
┌─────────────────────┐
│  External API       │
│  admin-qttd.tedp.vn │
└──────────┬──────────┘
           │ (every 5 min)
           ↓
┌──────────────────────────────────────┐
│  station-ingestion-service           │
│  ┌────────────────────────────────┐  │
│  │  StationAPIClient              │  │
│  │  - get_automation_stations()   │  │
│  │  - get_aqi_hours()             │  │
│  └────────────┬───────────────────┘  │
│               ↓                      │
│  ┌────────────────────────────────┐  │
│  │  StationIngestionService       │  │
│  │  - sync_stations()             │  │
│  │  - sync_aqi_data()             │  │
│  └────────────┬───────────────────┘  │
│               ↓                      │
│  ┌────────────────────────────────┐  │
│  │  Repository (MySQL)            │  │
│  │  - stations table              │  │
│  │  - air_quality_readings table  │  │
│  └────────────┬───────────────────┘  │
└───────────────┼──────────────────────┘
                │
                ↓
┌──────────────────────────────────────┐
│  Frontend (React)                    │
│  - StationsPage                      │
│  - Station Detail Panel              │
│  - TimeSeriesChart                   │
└──────────────────────────────────────┘
```

## Testing

### Verify Service Health
```bash
curl http://localhost:8010/api/v1/health
```

### Check Logs
```bash
docker-compose logs -f station-ingestion-service
```

### Test Data Sync
```bash
# Sync stations
curl -X POST http://localhost:8010/api/v1/sync/stations

# Check database
docker-compose exec mysql mysql -uroot -pMysql_2026 \
  -e "USE station_ingestion_db; SELECT COUNT(*) FROM stations;"
```

## Future Enhancements

- [ ] Add data retention policy (auto-delete old readings)
- [ ] Add station status monitoring (online/offline)
- [ ] Add alerting for high AQI values
- [ ] Add export functionality (CSV, PDF)
- [ ] Add map view for station locations
- [ ] Add historical data comparison
- [ ] Add real-time WebSocket updates

## Known Limitations

1. **Data Latency**: Data is fetched every 5 minutes (configurable)
2. **No Historical Backfill**: Only fetches last 24 hours by default
3. **Single Source**: Only integrates with admin-qttd.tedp.vn API

## Troubleshooting

See [documents/QUICKSTART_STATION_INGESTION.md](QUICKSTART_STATION_INGESTION.md) for troubleshooting guide.

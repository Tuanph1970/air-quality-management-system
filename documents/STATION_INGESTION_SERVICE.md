# Station Ingestion Service

Service for ingesting environmental monitoring station data from external APIs.

## Overview

This service fetches data from the external environmental monitoring API (admin-qttd.tedp.vn) and provides:
- Station list management
- Hourly AQI data ingestion
- REST API for frontend consumption
- Automatic data synchronization

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Station Ingestion Service                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  API Client  │───>│   Service    │───>│ Repository   │      │
│  │  (External)  │    │   Layer      │    │   (MySQL)    │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                                       │                │
│         │                                       │                │
│         v                                       v                │
│  ┌──────────────┐                        ┌──────────────┐      │
│  │ admin-qttd.  │                        │   Frontend   │      │
│  │ tedp.vn API  │                        │     API      │      │
│  └──────────────┘                        └──────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## External API Endpoints

### 1. Get Automation Stations
- **Endpoint:** `/get-automation-stations`
- **Method:** GET
- **Description:** Retrieves list of active automation stations

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| page | Integer | No | 0 | Page number (0-indexed) |
| size | Integer | No | 20 | Records per page |
| apiType | Integer | Yes | 1 | API Type |

### 2. Get Hourly AQI Data
- **Endpoint:** `/aqi_hours`
- **Method:** GET
- **Description:** Retrieves air quality data hour by hour

**Parameters:**
| Parameter | Type | Required | Format | Description |
|-----------|------|----------|--------|-------------|
| page | Integer | No | 0 | Page number |
| size | Integer | No | 100 | Records per page |
| apiType | Integer | Yes | 1 | API Type |
| from | DateTime | Yes | YYYY-MM-DDTHH:mm:ss | Start time |
| to | DateTime | Yes | YYYY-MM-DDTHH:mm:ss | End time |

## Service API Endpoints

### Station Endpoints

#### Get All Stations
```
GET /api/v1/stations
```

#### Get Station by Code
```
GET /api/v1/stations/:stationCode
```

#### Get Station Readings
```
GET /api/v1/stations/:stationCode/readings?from_time=ISO_DATE&to_time=ISO_DATE
```

#### Get Time Series (All Stations)
```
GET /api/v1/readings/timeseries?from_time=ISO_DATE&to_time=ISO_DATE
```

### Sync Endpoints

#### Sync Stations
```
POST /api/v1/sync/stations
```

#### Sync AQI Data
```
POST /api/v1/sync/aqi?hours=24
```

### Health Check
```
GET /api/v1/health
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | 0.0.0.0 | Service host |
| `PORT` | 8008 | Service port |
| `DATABASE_URL` | mysql+pymysql://... | MySQL connection URL |
| `STATION_API_BASE_URL` | https://admin-qttd.tedp.vn/api/partner/v1 | External API URL |
| `STATION_API_KEY` | c9e03048-... | External API key |
| `FETCH_INTERVAL_SECONDS` | 300 | Data fetch interval (5 min) |
| `AQI_HOURS_PAGE_SIZE` | 100 | Page size for AQI fetch |

## Running the Service

### Development

```bash
cd services/station-ingestion-service

# Install dependencies
pip install -r requirements.txt

# Initialize database
python scripts/init_db.py

# Run service
python main.py
```

### Docker

```bash
# Start with docker-compose
docker-compose up -d station-ingestion-service

# View logs
docker-compose logs -f station-ingestion-service
```

### Data Fetcher (Background Sync)

```bash
# Run continuous data fetcher
python scripts/data_fetcher.py
```

## Database Schema

### stations
| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR(36) | Primary key (UUID) |
| station_code | VARCHAR(100) | Unique station code |
| station_name | VARCHAR(255) | Display name |
| address | TEXT | Physical address |
| latitude | FLOAT | Geographic latitude |
| longitude | FLOAT | Geographic longitude |
| station_type | INT | Type code (4 = Air) |
| province_id | VARCHAR(50) | Province ID |
| is_active | BOOLEAN | Active status |
| metadata | JSON | Additional data |
| created_at | DATETIME | Creation timestamp |
| updated_at | DATETIME | Last update |

### air_quality_readings
| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR(36) | Primary key (UUID) |
| station_code | VARCHAR(100) | Foreign key |
| reading_time | DATETIME | Measurement time |
| aqi | FLOAT | Air Quality Index |
| pm25 | FLOAT | PM2.5 (µg/m³) |
| pm10 | FLOAT | PM10 (µg/m³) |
| co | FLOAT | Carbon monoxide |
| so2 | FLOAT | Sulfur dioxide |
| no2 | FLOAT | Nitrogen dioxide |
| o3 | FLOAT | Ozone |
| temperature | FLOAT | Temperature (°C) |
| humidity | FLOAT | Humidity (%) |
| created_at | DATETIME | Creation timestamp |

## Frontend Integration

The service provides data for the Monitoring Stations page:

1. **Station List:** Displays all stations with latest AQI readings
2. **Station Detail:** Shows detailed readings and time series chart
3. **Auto-refresh:** Data syncs every 5 minutes

### API Client (Frontend)

```javascript
import { stationIngestionApi } from './services/stationIngestionApi';

// Get all stations
const stations = await stationIngestionApi.getStations();

// Get station readings
const readings = await stationIngestionApi.getStationReadings('LSOS_KHIKHO', {
  from_time: '2025-01-01T00:00:00',
  to_time: '2025-01-02T00:00:00',
});

// Trigger sync
await stationIngestionApi.syncStations();
await stationIngestionApi.syncAqiData(24);
```

## Troubleshooting

### Check Service Health
```bash
curl http://localhost:8010/api/v1/health
```

### View Logs
```bash
docker-compose logs -f station-ingestion-service
```

### Manual Data Sync
```bash
# Sync stations
curl -X POST http://localhost:8010/api/v1/sync/stations

# Sync AQI data (last 24 hours)
curl -X POST "http://localhost:8010/api/v1/sync/aqi?hours=24"
```

### Database Connection Issues
```bash
# Check MySQL is running
docker-compose ps mysql

# Test connection
docker-compose exec station-ingestion-service \
  python -c "from src.core.config import config; from src.infrastructure.persistence.models import create_tables; create_tables(config.DATABASE_URL)"
```

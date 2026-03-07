# Station Service & PurpleAir Ingestion - Implementation Documentation

## Overview

This document describes the implementation of two new services in the Air Quality Management System:

1. **Station Service (Port 8007)**: Manages air quality monitoring stations and ingests data via APIs
2. **PurpleAir Ingestion Service (Port 8008)**: Receives data from PurpleAir Flex-Air Quality Monitors

---

## Architecture

### Station Service Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY (Port 8000)                           │
│                    /api/v1/stations/* → station-service:8007                │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        STATION SERVICE (Port 8007)                          │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Domain Layer (Core Business Logic)                                 │   │
│  │  - Entities: Station, PollutantReading                              │   │
│  │  - Value Objects: StationType, PollutantType, GeographicCoordinate  │   │
│  │  - Aggregates: StationAggregate                                     │   │
│  │  - Repositories: StationRepository, ReadingRepository               │   │
│  │  - Services: DataQualityValidator                                   │   │
│  │  - Events: StationCreated, StationDataReceived, etc.                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Application Layer (Use Cases)                                      │   │
│  │  - Commands: CreateStation, ConfigureAPI, RecordReadings            │   │
│  │  - Queries: GetStation, ListStations, GetReadings                   │   │
│  │  - DTOs: StationDTO, PollutantReadingDTO                            │   │
│  │  - Services: StationApplicationService                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Infrastructure Layer                                               │   │
│  │  - Persistence: MySQL (station_db)                                  │   │
│  │  - External APIs: StationAPIClient with Strategy Pattern            │   │
│  │    * BaseStationAdapter (abstract)                                  │   │
│  │    * GenericStationAdapter (concrete)                               │   │
│  │    * AdapterFactory (creates adapters by type)                      │   │
│  │  - Messaging: RabbitMQ publisher                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Interface Layer (API)                                              │   │
│  │  - REST endpoints: /api/v1/stations/*                               │   │
│  │  - Controllers: station_controller.py                               │   │
│  │  - Schemas: Pydantic request/response models                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MESSAGE BROKER (RabbitMQ)                         │
│    Events: StationDataReceived, StationReadingsCreated → AQI Recalculation  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### PurpleAir Ingestion Service Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PurpleAir Devices (WiFi/Internet)                        │
│                    Flex-Air Quality Monitors                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ HTTP POST (Webhook)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   PURPLEAIR INGESTION SERVICE (Port 8008)                   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Webhook Endpoint: POST /api/v1/purpleair/webhook                   │   │
│  │  - Accepts JSON from PurpleAir devices                              │   │
│  │  - Maps PurpleAir format to standard AQMS format                    │   │
│  │  - Publishes PurpleAirDataIngested events                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Cloud API Polling (Optional)                                       │   │
│  │  - PurpleAirAPIClient for api.purpleair.com                         │   │
│  │  - Fetches data from registered sensors                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Fake Data Generator                                                │   │
│  │  - Generates realistic PurpleAir sensor data                        │   │
│  │  - Configurable environment types (urban, suburban, rural)          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MESSAGE BROKER (RabbitMQ)                         │
│    Events: PurpleAirDataIngested → AQI Recalculation, Alert Detection       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Design Patterns Used

### 1. Strategy Pattern (Station API Adapters)

The Station Service uses the Strategy pattern to support multiple station API protocols:

```python
# Abstract strategy
class BaseStationAdapter(ABC):
    @abstractmethod
    async def fetch_data(self, config: Dict[str, Any]) -> StationDataResult:
        pass

# Concrete strategies
class GenericStationAdapter(BaseStationAdapter):
    adapter_type = "generic"
    async def fetch_data(self, config):
        # Generic HTTP API implementation

class EPAAdapter(BaseStationAdapter):
    adapter_type = "epa"
    async def fetch_data(self, config):
        # EPA-specific API implementation

# Context (uses strategy)
class StationAPIClient:
    def __init__(self, adapter_factory):
        self.adapter_factory = adapter_factory
    
    async def fetch_data(self, config):
        adapter = self.adapter_factory.create(config["adapter_type"])
        return await adapter.fetch_data(config)
```

**Benefits:**
- Easy to add new station API types without modifying existing code
- Consistent interface for all adapters
- Configuration-driven adapter selection

### 2. Domain-Driven Design (DDD)

Both services follow DDD principles:

- **Entities**: Station, PollutantReading (with identity and lifecycle)
- **Value Objects**: StationType, PollutantType, GeographicCoordinate (immutable)
- **Aggregates**: StationAggregate (consistency boundary)
- **Repositories**: Abstract interfaces in domain layer, implementations in infrastructure
- **Domain Services**: DataQualityValidator (business logic)
- **Domain Events**: StationCreated, StationDataReceived, PurpleAirDataIngested

### 3. CQRS (Command Query Responsibility Segregation)

Application layer separates write operations (Commands) from read operations (Queries):

```python
# Commands (write)
class CreateStationCommand: ...
class RecordStationReadingsCommand: ...

# Queries (read)
class GetStationQuery: ...
class GetStationReadingsQuery: ...
```

### 4. Repository Pattern

Domain layer defines repository interfaces, infrastructure provides implementations:

```python
# Domain layer
class StationRepository(ABC):
    async def get_by_id(self, station_id: UUID) -> Optional[Station]: ...

# Infrastructure layer
class SQLAlchemyStationRepository(StationRepository):
    async def get_by_id(self, station_id: UUID):
        # SQLAlchemy implementation
```

---

## API Endpoints

### Station Service (Port 8007)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/stations` | Create new station |
| GET | `/api/v1/stations` | List all stations |
| GET | `/api/v1/stations/{id}` | Get station by ID |
| GET | `/api/v1/stations/code/{code}` | Get station by external code |
| PUT | `/api/v1/stations/{id}` | Update station |
| DELETE | `/api/v1/stations/{id}` | Delete station |
| POST | `/api/v1/stations/{id}/configure-api` | Configure API endpoint |
| POST | `/api/v1/stations/{id}/activate` | Activate station |
| POST | `/api/v1/stations/{id}/deactivate` | Deactivate station |
| POST | `/api/v1/stations/{id}/record-readings` | Record readings (webhook) |
| GET | `/api/v1/stations/{id}/readings` | Get historical readings |
| GET | `/api/v1/stations/{id}/readings/latest` | Get latest readings |
| GET | `/api/v1/stations/nearby` | Find nearby stations |

### PurpleAir Ingestion Service (Port 8008)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/purpleair/webhook` | PurpleAir device webhook |
| POST | `/api/v1/purpleair/register` | Register PurpleAir sensor |
| GET | `/api/v1/purpleair/fake-data` | Generate fake data |

---

## Data Models

### Station Entity

```python
@dataclass
class Station:
    id: UUID
    station_code: str          # External identifier (e.g., EPA ID)
    name: str
    station_type: StationType  # GOVERNMENT, INDUSTRIAL, URBAN, RURAL, etc.
    location: GeographicCoordinate
    api_config: Optional[Dict]  # API endpoint configuration
    is_active: bool
    data_retention_days: int = 1  # 1 day as per requirements
    last_data_received: Optional[datetime]
```

### Pollutant Readings

Monitored pollutants:
- **SO2**: Sulfur Dioxide (µg/m³)
- **NOX**: Nitrogen Oxides (µg/m³)
- **NO2**: Nitrogen Dioxide (µg/m³)
- **CO**: Carbon Monoxide (mg/m³)
- **CO2**: Carbon Dioxide (ppm)
- **PM25**: Particulate Matter ≤2.5µm (µg/m³)
- **PM10**: Particulate Matter ≤10µm (µg/m³)
- **O3**: Ozone (µg/m³)

### PurpleAir Data Format

```json
{
  "sensor_id": 12345,
  "api_key": "your-api-key",
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
}
```

---

## Fake Data Generation

### Station Service Fake Data

The station service includes a sophisticated fake data generator that creates realistic readings with:

- **Diurnal patterns**: Traffic peaks at 8am and 6pm
- **Station type variations**: Urban, rural, industrial have different base levels
- **Pollutant correlations**: PM2.5 ≤ PM10, etc.
- **Random noise**: Gaussian noise for realism

Example usage:
```bash
docker compose exec station-service python scripts/fake_data_generator.py
```

### PurpleAir Fake Data

Generates realistic PurpleAir Flex-Air monitor data:
```bash
curl http://localhost:8008/api/v1/purpleair/fake-data?count=5
```

---

## Database Schema

### MySQL Database: `station_db`

**stations table:**
```sql
CREATE TABLE stations (
    id VARCHAR(36) PRIMARY KEY,
    station_code VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    station_type VARCHAR(50) NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    altitude FLOAT,
    is_active BOOLEAN DEFAULT FALSE,
    api_config JSON,
    data_retention_days INT DEFAULT 1,
    metadata JSON,
    created_at DATETIME,
    updated_at DATETIME,
    last_data_received DATETIME
);
```

**pollutant_readings table:**
```sql
CREATE TABLE pollutant_readings (
    id VARCHAR(36) PRIMARY KEY,
    station_id VARCHAR(36) NOT NULL,
    pollutant_type VARCHAR(20) NOT NULL,
    value FLOAT NOT NULL,
    unit VARCHAR(20) DEFAULT 'µg/m³',
    quality_flag VARCHAR(20),
    timestamp DATETIME NOT NULL,
    created_at DATETIME,
    FOREIGN KEY (station_id) REFERENCES stations(id) ON DELETE CASCADE,
    INDEX idx_station_time (station_id, timestamp),
    INDEX idx_time_pollutant (timestamp, pollutant_type)
);
```

---

## Event Flow

### Station Data → AQI Recalculation

```
1. Station Service polls API or receives webhook
         ↓
2. Validates data (DataQualityValidator)
         ↓
3. Saves readings to database
         ↓
4. Publishes StationDataReceived event
         ↓
5. Air Quality Service receives event
         ↓
6. Recalculates AQI for the area
         ↓
7. Publishes AQICalculated event
         ↓
8. Alert Service checks thresholds
```

### PurpleAir Data → AQI Recalculation

```
1. PurpleAir device pushes to webhook
   OR
   Service polls PurpleAir Cloud API
         ↓
2. Maps PurpleAir format to AQMS format
         ↓
3. Publishes PurpleAirDataIngested event
         ↓
4. Air Quality Service receives event
         ↓
5. Recalculates AQI (same as above)
```

---

## Configuration

### Environment Variables

```bash
# Station Service
STATION_SERVICE_PORT=8007
DATABASE_URL=mysql+aiomysql://root:password@mysql:3306/station_db
USE_FAKE_DATA=False
FAKE_DATA_STATION_COUNT=5
FAKE_DATA_INTERVAL_SECONDS=60

# PurpleAir Service
PURPLEAIR_INGESTION_PORT=8008
PURPLEAIR_API_KEY=your-api-key
PURPLEAIR_USE_FAKE_DATA=False
PURPLEAIR_FAKE_DATA_INTERVAL=60
```

---

## Testing

### Health Checks

```bash
# Station Service
curl http://localhost:8007/health

# PurpleAir Service
curl http://localhost:8008/health
```

### API Documentation

- Station Service: http://localhost:8007/docs
- PurpleAir Service: http://localhost:8008/docs

### Example: Create Station

```bash
curl -X POST http://localhost:8000/api/v1/stations \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Downtown Station",
    "station_code": "EPA-001",
    "station_type": "URBAN",
    "latitude": 21.0285,
    "longitude": 105.8542
  }'
```

### Example: Configure API

```bash
curl -X POST http://localhost:8000/api/v1/stations/{id}/configure-api \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint": "https://api.example.com/readings",
    "method": "GET",
    "adapter_type": "generic",
    "poll_interval_seconds": 300
  }'
```

### Example: PurpleAir Webhook

```bash
curl -X POST http://localhost:8008/api/v1/purpleair/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": 12345,
    "api_key": "test-key",
    "latitude": 21.0285,
    "longitude": 105.8542,
    "data": {
      "pm2_5": 35.5,
      "pm10_0": 50.0
    }
  }'
```

---

## Deployment

### Docker Compose

```bash
# Start all services including new ones
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f station-service
docker compose logs -f purpleair-ingestion-service
```

### Database Initialization

The station_db database is created automatically on first startup. Tables are created by SQLAlchemy.

---

## Future Enhancements

1. **Additional Station Adapters**: EPA, OpenWeatherMap, government APIs
2. **Data Quality Rules**: Advanced validation, outlier detection
3. **Forecasting**: Predictive models for air quality
4. **Alert Rules**: Customizable thresholds per station
5. **Dashboard**: Real-time monitoring UI

---

## References

- PurpleAir API: https://api.purpleair.com/
- WHO Air Quality Guidelines: https://www.who.int/news-room/fact-sheets/detail/ambient-(outdoor)-air-quality-and-health
- DDD Patterns: https://martinfowler.com/bliki/DomainDrivenDesign.html

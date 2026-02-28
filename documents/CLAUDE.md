# CLAUDE.md - Air Quality Management Information System (AQMIS)

## Project Overview

You are building an **Air Quality Management Information System** using **Microservice Architecture** and **Domain-Driven Design (DDD)** patterns. The system monitors city air quality, manages factory emissions, and enables enforcement actions.

### Data Sources (3 Types)
1. **Excel Data** - Historical air quality data, factory records
2. **Remote Sensing** - Satellite imagery (MODIS AOD, Sentinel-5P TROPOMI, Copernicus CAMS)
3. **Low-Cost Sensors** - Ground-level IoT sensors with real-time data

### Architecture Principles
- **Microservices**: Independent, loosely-coupled services
- **Domain-Driven Design**: Business logic organized by bounded contexts
- **Event-Driven**: Services communicate via events/messages
- **API Gateway**: Single entry point for all clients
- **Docker**: Containerized deployment for all services

### Tech Stack
- **Frontend**: React 18 + JavaScript + Vite + TailwindCSS
- **Backend Services**: Python FastAPI (per microservice)
- **API Gateway**: FastAPI with routing
- **Message Broker**: RabbitMQ (async communication)
- **Databases**: PostgreSQL (per service), TimescaleDB (sensor data), Redis (cache)
- **Container Orchestration**: Docker Compose
- **Remote Sensing APIs**: Copernicus CAMS, Google Earth Engine, Sentinel Hub

---

## Microservices Overview (7 Services)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                        │
│                    (Web App, Mobile App, IoT Devices)                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY                                       │
│                    (Authentication, Routing, Rate Limiting)                 │
│                           Port: 8000                                        │
└─────────────────────────────────────────────────────────────────────────────┘
       │           │           │           │           │           │
       ▼           ▼           ▼           ▼           ▼           ▼
┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐
│  FACTORY  │ │  SENSOR   │ │  REMOTE   │ │   ALERT   │ │    AIR    │ │   USER    │
│  SERVICE  │ │  SERVICE  │ │  SENSING  │ │  SERVICE  │ │  QUALITY  │ │  SERVICE  │
│  Port:8001│ │  Port:8002│ │  SERVICE  │ │  Port:8004│ │  SERVICE  │ │  Port:8006│
│           │ │           │ │  Port:8003│ │           │ │  Port:8005│ │           │
│- Factories│ │- Sensors  │ │           │ │- Violations│ │- AQI Calc │ │- Auth     │
│- Emissions│ │- Readings │ │- Satellite│ │- Alerts   │ │- Data     │ │- Users    │
│- Suspend  │ │- Calibrate│ │- MODIS    │ │- Notify   │ │  Fusion   │ │- Roles    │
│           │ │           │ │- TROPOMI  │ │           │ │- Maps     │ │           │
│           │ │           │ │- CAMS     │ │           │ │- Predict  │ │           │
│           │ │           │ │- Excel    │ │           │ │           │ │           │
└─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘
      │             │             │             │             │             │
      └─────────────┴─────────────┴──────┬──────┴─────────────┴─────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       MESSAGE BROKER (RabbitMQ)                             │
│                            Port: 5672                                       │
│  Events: SensorReading, SatelliteData, ViolationDetected, DataFused, etc.  │
└─────────────────────────────────────────────────────────────────────────────┘
       │           │           │           │           │           │
       ▼           ▼           ▼           ▼           ▼           ▼
┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐
│ PostgreSQL│ │TimescaleDB│ │ PostgreSQL│ │ PostgreSQL│ │   Redis   │ │ PostgreSQL│
│factory_db │ │ sensor_db │ │ remote_db │ │ alert_db  │ │   Cache   │ │  user_db  │
│ Port:5432 │ │ Port:5433 │ │ Port:5434 │ │ Port:5435 │ │ Port:6379 │ │ Port:5436 │
└───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘
```

---

## Service Responsibilities

### 1. Factory Service (Port 8001)
- Factory CRUD operations
- Emission permits management
- Factory suspension/resume workflow
- Emission limits tracking

### 2. Sensor Service (Port 8002)
- Low-cost sensor registration
- Real-time sensor readings (IoT)
- Sensor calibration (using satellite reference)
- TimescaleDB for time-series data

### 3. Remote Sensing Service (Port 8003) ⭐ NEW
- **Satellite data ingestion**:
  - MODIS AOD (Aerosol Optical Depth)
  - Sentinel-5P TROPOMI (NO2, SO2, O3, CO)
  - Copernicus CAMS (European air quality)
- **Excel data import** (historical records)
- **Data scheduling** (periodic satellite data fetch)
- **Reference data provider** for sensor calibration

### 4. Alert Service (Port 8004)
- Violation detection from fused data
- Alert rule configuration
- Notification dispatch (email/SMS)
- Violation lifecycle management

### 5. Air Quality Service (Port 8005) ⭐ ENHANCED
- **Data Fusion Engine** - Combines sensor + satellite + Excel data
- **Cross-validation** - Validates sensors against satellite reference
- AQI calculation (US EPA standards)
- Google Maps heatmap integration
- ML predictions and forecasting

### 6. User Service (Port 8006)
- User authentication (JWT)
- Role-based access control
- User management

---

## Data Flow: Sensor Calibration with Satellite Reference

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Remote Sensing │     │   Air Quality   │     │  Sensor Service │
│     Service     │     │    Service      │     │                 │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         │ 1. Fetch satellite    │                       │
         │    data (hourly)      │                       │
         │──────────────────────>│                       │
         │                       │                       │
         │ SatelliteDataReceived │                       │
         │                       │                       │
         │                       │ 2. Request sensor     │
         │                       │    readings for same  │
         │                       │    time/location      │
         │                       │──────────────────────>│
         │                       │                       │
         │                       │<──────────────────────│
         │                       │    SensorReadings     │
         │                       │                       │
         │                       │ 3. Cross-validate     │
         │                       │    & calibrate        │
         │                       │    (ML model)         │
         │                       │                       │
         │                       │ 4. Publish fused      │
         │                       │    data               │
         │                       │──────────────────────>│
         │                       │   CalibratedReading   │
         │                       │   CalibrationUpdated  │
```

---

## Remote Sensing Service - Detailed Design

### Satellite Data Sources

| Source | Data Type | Resolution | Update Frequency | API |
|--------|-----------|------------|------------------|-----|
| MODIS Terra/Aqua | AOD (Aerosol Optical Depth) | 10km | Daily | NASA Earthdata |
| Sentinel-5P TROPOMI | NO2, SO2, O3, CO, CH4 | 7km x 3.5km | Daily | Copernicus |
| Copernicus CAMS | PM2.5, PM10, O3, NO2 | 40km | Hourly | ECMWF |
| Google Earth Engine | Multiple products | Varies | Varies | GEE API |

### Domain Model

```python
# services/remote-sensing-service/src/domain/entities/satellite_data.py

@dataclass
class SatelliteData:
    """Entity: Satellite observation data"""
    id: UUID
    source: SatelliteSource  # MODIS, TROPOMI, CAMS
    data_type: DataType      # AOD, NO2, PM25, etc.
    observation_time: datetime
    location: GeoPolygon     # Bounding box or polygon
    grid_data: Dict[str, float]  # Grid cells with values
    quality_flag: QualityFlag
    metadata: Dict
    
    @classmethod
    def from_netcdf(cls, filepath: str, source: SatelliteSource) -> 'SatelliteData':
        """Factory method to create from NetCDF file"""
        pass

@dataclass
class ExcelImport:
    """Entity: Imported Excel data"""
    id: UUID
    filename: str
    import_time: datetime
    record_count: int
    data_type: str  # historical_readings, factory_records
    status: ImportStatus
    errors: List[str]
```

### Value Objects

```python
# services/remote-sensing-service/src/domain/value_objects/

@dataclass(frozen=True)
class SatelliteSource:
    """Enum-like value object"""
    MODIS_AOD = "modis_aod"
    TROPOMI_NO2 = "tropomi_no2"
    TROPOMI_SO2 = "tropomi_so2"
    CAMS_PM25 = "cams_pm25"
    CAMS_PM10 = "cams_pm10"

@dataclass(frozen=True)
class GeoPolygon:
    """Geographic bounding box"""
    north: float
    south: float
    east: float
    west: float
    
    def contains(self, lat: float, lon: float) -> bool:
        return (self.south <= lat <= self.north and 
                self.west <= lon <= self.east)
    
    def get_center(self) -> Tuple[float, float]:
        return ((self.north + self.south) / 2, 
                (self.east + self.west) / 2)

@dataclass(frozen=True)
class GridCell:
    """Single grid cell with satellite value"""
    lat: float
    lon: float
    value: float
    uncertainty: float
```

### Application Services

```python
# services/remote-sensing-service/src/application/services/

class SatelliteDataService:
    """Orchestrates satellite data fetching and processing"""
    
    async def fetch_modis_aod(self, date: date, bbox: GeoPolygon) -> SatelliteData:
        """Fetch MODIS AOD data for region"""
        pass
    
    async def fetch_tropomi_no2(self, date: date, bbox: GeoPolygon) -> SatelliteData:
        """Fetch Sentinel-5P TROPOMI NO2 data"""
        pass
    
    async def fetch_cams_forecast(self, bbox: GeoPolygon, hours: int = 24) -> List[SatelliteData]:
        """Fetch CAMS air quality forecast"""
        pass
    
    async def schedule_periodic_fetch(self, sources: List[SatelliteSource]) -> None:
        """Set up periodic data fetching"""
        pass

class ExcelImportService:
    """Handles Excel data import"""
    
    async def import_historical_readings(self, file: UploadFile) -> ExcelImport:
        """Import historical air quality readings from Excel"""
        pass
    
    async def import_factory_records(self, file: UploadFile) -> ExcelImport:
        """Import factory emission records from Excel"""
        pass
    
    async def validate_excel_format(self, file: UploadFile, expected_columns: List[str]) -> ValidationResult:
        """Validate Excel file format before import"""
        pass
```

### Infrastructure - External API Clients

```python
# services/remote-sensing-service/src/infrastructure/external/

class CopernicusCAMSClient:
    """Client for Copernicus Atmosphere Monitoring Service"""
    
    BASE_URL = "https://ads.atmosphere.copernicus.eu/api/v2"
    
    async def get_forecast(self, variable: str, bbox: GeoPolygon, 
                          date: date) -> Dict:
        """
        Fetch CAMS forecast data
        Variables: pm2p5, pm10, no2, o3, so2, co
        """
        pass

class NASAEarthdataClient:
    """Client for NASA Earthdata (MODIS)"""
    
    BASE_URL = "https://ladsweb.modaps.eosdis.nasa.gov/api/v2"
    
    async def get_modis_aod(self, product: str, bbox: GeoPolygon,
                           date: date) -> bytes:
        """
        Fetch MODIS AOD data
        Products: MOD04_L2 (Terra), MYD04_L2 (Aqua)
        """
        pass

class SentinelHubClient:
    """Client for Sentinel Hub (TROPOMI)"""
    
    async def get_tropomi_data(self, product: str, bbox: GeoPolygon,
                              date: date) -> Dict:
        """
        Fetch Sentinel-5P TROPOMI data
        Products: L2__NO2___, L2__SO2___, L2__O3___
        """
        pass

class GoogleEarthEngineClient:
    """Client for Google Earth Engine"""
    
    async def get_satellite_data(self, collection: str, bbox: GeoPolygon,
                                 start_date: date, end_date: date) -> Dict:
        """
        Fetch data from GEE collections
        Collections: COPERNICUS/S5P/OFFL/L3_NO2, MODIS/006/MOD04_L2
        """
        pass
```

---

## Air Quality Service - Data Fusion Engine

### Data Fusion Process

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA FUSION ENGINE                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│  │   Sensor    │  │  Satellite  │  │    Excel    │                │
│  │   Readings  │  │    Data     │  │    Import   │                │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                │
│         │                │                │                        │
│         ▼                ▼                ▼                        │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │              SPATIAL-TEMPORAL ALIGNMENT                  │      │
│  │  - Match sensor locations to satellite grid cells        │      │
│  │  - Align timestamps (sensor: minutes, satellite: hours)  │      │
│  └─────────────────────────────────────────────────────────┘      │
│                              │                                     │
│                              ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │              CROSS-VALIDATION MODULE                     │      │
│  │  - Compare sensor vs satellite values                    │      │
│  │  - Calculate correlation coefficients                    │      │
│  │  - Identify sensor drift or malfunction                  │      │
│  └─────────────────────────────────────────────────────────┘      │
│                              │                                     │
│                              ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │              CALIBRATION MODEL (ML)                      │      │
│  │  - Random Forest / Gradient Boosting                     │      │
│  │  - Features: raw_value, temperature, humidity,           │      │
│  │              satellite_aod, time_of_day, sensor_age      │      │
│  │  - Output: calibrated_value, confidence_score            │      │
│  └─────────────────────────────────────────────────────────┘      │
│                              │                                     │
│                              ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │              FUSED DATA OUTPUT                           │      │
│  │  - Calibrated sensor readings                            │      │
│  │  - Gap-filled spatial coverage                           │      │
│  │  - Uncertainty estimates                                 │      │
│  └─────────────────────────────────────────────────────────┘      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Fusion Domain Services

```python
# services/air-quality-service/src/domain/services/data_fusion.py

@dataclass
class FusedDataPoint:
    """Result of data fusion"""
    location: Location
    timestamp: datetime
    
    # Sensor data (if available)
    sensor_pm25: Optional[float]
    sensor_pm10: Optional[float]
    
    # Satellite data (if available)
    satellite_aod: Optional[float]
    satellite_pm25: Optional[float]
    
    # Calibrated/fused values
    fused_pm25: float
    fused_pm10: float
    fused_aqi: int
    
    # Quality metrics
    confidence: float  # 0-1
    data_sources: List[str]  # ['sensor', 'satellite', 'excel']

class DataFusionService:
    """Domain service for multi-source data fusion"""
    
    def __init__(self, calibration_model: CalibrationModel):
        self.calibration_model = calibration_model
    
    def fuse_data(
        self,
        sensor_readings: List[SensorReading],
        satellite_data: SatelliteData,
        excel_reference: Optional[List[ExcelRecord]] = None
    ) -> List[FusedDataPoint]:
        """
        Fuse multiple data sources into unified air quality data
        
        Algorithm:
        1. Spatial matching: Find satellite grid cell for each sensor
        2. Temporal alignment: Aggregate sensor readings to satellite time resolution
        3. Cross-validation: Compare values, flag anomalies
        4. Calibration: Apply ML model to correct sensor readings
        5. Gap filling: Use satellite data where no sensors exist
        """
        pass
    
    def cross_validate(
        self,
        sensor_value: float,
        satellite_value: float,
        tolerance: float = 0.3
    ) -> ValidationResult:
        """
        Cross-validate sensor reading against satellite reference
        Returns: correlation, bias, rmse, is_valid
        """
        pass


class CalibrationModel:
    """ML model for sensor calibration using satellite reference"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = self._load_or_create_model(model_path)
    
    def calibrate(
        self,
        raw_reading: SensorReading,
        satellite_reference: float,
        environmental_factors: Dict
    ) -> CalibratedReading:
        """
        Apply calibration model to raw sensor reading
        
        Features used:
        - raw_pm25, raw_pm10
        - temperature, humidity
        - satellite_aod (as reference)
        - hour_of_day, day_of_week
        - sensor_age_days
        """
        pass
    
    def train(
        self,
        training_data: List[Tuple[SensorReading, float]]  # (raw, reference)
    ) -> TrainingResult:
        """
        Train/retrain calibration model with new data
        Uses Random Forest or Gradient Boosting
        """
        pass
    
    def evaluate(self, test_data: List[Tuple[SensorReading, float]]) -> EvaluationMetrics:
        """Evaluate model performance: R², RMSE, MAE, bias"""
        pass
```

---

## Project Structure (Updated)

```
air-quality-system/
├── CLAUDE.md
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
│
├── services/
│   │
│   ├── api-gateway/                 # API Gateway (Port 8000)
│   │   ├── src/
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── routes/
│   │   │   └── middleware/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── factory-service/             # Factory Service (Port 8001)
│   │   ├── src/
│   │   │   ├── domain/
│   │   │   ├── application/
│   │   │   ├── infrastructure/
│   │   │   └── interfaces/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── sensor-service/              # Sensor Service (Port 8002)
│   │   ├── src/
│   │   │   ├── domain/
│   │   │   │   ├── entities/
│   │   │   │   │   ├── sensor.py
│   │   │   │   │   └── reading.py
│   │   │   │   ├── value_objects/
│   │   │   │   ├── repositories/
│   │   │   │   └── services/
│   │   │   ├── application/
│   │   │   ├── infrastructure/
│   │   │   └── interfaces/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── remote-sensing-service/      # ⭐ Remote Sensing Service (Port 8003)
│   │   ├── src/
│   │   │   ├── domain/
│   │   │   │   ├── entities/
│   │   │   │   │   ├── satellite_data.py
│   │   │   │   │   ├── excel_import.py
│   │   │   │   │   └── data_source.py
│   │   │   │   ├── value_objects/
│   │   │   │   │   ├── satellite_source.py
│   │   │   │   │   ├── geo_polygon.py
│   │   │   │   │   ├── grid_cell.py
│   │   │   │   │   └── quality_flag.py
│   │   │   │   ├── repositories/
│   │   │   │   │   ├── satellite_data_repository.py
│   │   │   │   │   └── excel_import_repository.py
│   │   │   │   ├── services/
│   │   │   │   │   └── data_processor.py
│   │   │   │   └── events/
│   │   │   │       └── remote_sensing_events.py
│   │   │   ├── application/
│   │   │   │   ├── commands/
│   │   │   │   │   ├── fetch_satellite_data_command.py
│   │   │   │   │   ├── import_excel_command.py
│   │   │   │   │   └── schedule_fetch_command.py
│   │   │   │   ├── queries/
│   │   │   │   │   ├── get_satellite_data_query.py
│   │   │   │   │   └── get_import_status_query.py
│   │   │   │   ├── dto/
│   │   │   │   └── services/
│   │   │   │       ├── satellite_data_service.py
│   │   │   │       └── excel_import_service.py
│   │   │   ├── infrastructure/
│   │   │   │   ├── persistence/
│   │   │   │   │   ├── models.py
│   │   │   │   │   └── satellite_repository_impl.py
│   │   │   │   ├── external/              # ⭐ External API Clients
│   │   │   │   │   ├── copernicus_cams_client.py
│   │   │   │   │   ├── nasa_earthdata_client.py
│   │   │   │   │   ├── sentinel_hub_client.py
│   │   │   │   │   └── google_earth_engine_client.py
│   │   │   │   ├── parsers/               # Data file parsers
│   │   │   │   │   ├── netcdf_parser.py
│   │   │   │   │   ├── geotiff_parser.py
│   │   │   │   │   └── excel_parser.py
│   │   │   │   ├── messaging/
│   │   │   │   └── scheduler/             # ⭐ Periodic data fetch
│   │   │   │       └── satellite_scheduler.py
│   │   │   └── interfaces/
│   │   │       └── api/
│   │   │           ├── routes.py
│   │   │           ├── satellite_controller.py
│   │   │           └── excel_controller.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── alert-service/               # Alert Service (Port 8004)
│   │   ├── src/
│   │   │   ├── domain/
│   │   │   ├── application/
│   │   │   ├── infrastructure/
│   │   │   └── interfaces/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── air-quality-service/         # ⭐ Air Quality Service (Port 8005) - ENHANCED
│   │   ├── src/
│   │   │   ├── domain/
│   │   │   │   ├── entities/
│   │   │   │   │   ├── air_quality_index.py
│   │   │   │   │   └── fused_data.py
│   │   │   │   ├── value_objects/
│   │   │   │   │   ├── aqi_level.py
│   │   │   │   │   └── pollutant.py
│   │   │   │   └── services/
│   │   │   │       ├── aqi_calculator.py
│   │   │   │       ├── data_fusion.py          # ⭐ Data Fusion Engine
│   │   │   │       ├── cross_validator.py      # ⭐ Cross-validation
│   │   │   │       ├── calibration_model.py    # ⭐ ML Calibration
│   │   │   │       └── prediction_service.py
│   │   │   ├── application/
│   │   │   │   ├── commands/
│   │   │   │   │   ├── fuse_data_command.py
│   │   │   │   │   └── train_calibration_command.py
│   │   │   │   ├── queries/
│   │   │   │   │   ├── get_fused_data_query.py
│   │   │   │   │   ├── get_map_data_query.py
│   │   │   │   │   └── get_validation_report_query.py
│   │   │   │   └── services/
│   │   │   │       └── air_quality_application_service.py
│   │   │   ├── infrastructure/
│   │   │   │   ├── external/
│   │   │   │   │   └── google_maps_client.py
│   │   │   │   ├── ml/                    # ⭐ ML Model storage
│   │   │   │   │   └── model_repository.py
│   │   │   │   └── cache/
│   │   │   └── interfaces/
│   │   │       └── api/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── user-service/                # User Service (Port 8006)
│   │   └── ...
│   │
│   └── shared/                      # Shared Libraries
│       ├── events/
│       │   ├── base_event.py
│       │   ├── factory_events.py
│       │   ├── sensor_events.py
│       │   ├── satellite_events.py      # ⭐ New
│       │   ├── fusion_events.py         # ⭐ New
│       │   └── alert_events.py
│       ├── messaging/
│       ├── auth/
│       └── utils/
│
├── frontend/                        # React Frontend
│   └── ...
│
└── scripts/
    ├── init-databases.sh
    ├── seed-data.py
    ├── simulate-sensors.py
    └── fetch-satellite-sample.py    # ⭐ New: Sample satellite data fetch
```

---

## Domain Events (Updated)

### Satellite/Remote Sensing Events

```python
# shared/events/satellite_events.py

@dataclass
class SatelliteDataFetched(DomainEvent):
    """Published when satellite data is successfully fetched"""
    source: str           # 'MODIS', 'TROPOMI', 'CAMS'
    data_type: str        # 'AOD', 'NO2', 'PM25'
    observation_time: datetime
    bbox: Dict            # Bounding box
    record_count: int
    event_type: str = "satellite.data.fetched"

@dataclass
class ExcelDataImported(DomainEvent):
    """Published when Excel data is imported"""
    import_id: UUID
    filename: str
    record_count: int
    data_type: str
    event_type: str = "excel.data.imported"

# shared/events/fusion_events.py

@dataclass
class DataFusionCompleted(DomainEvent):
    """Published when data fusion is completed"""
    fusion_id: UUID
    sources_used: List[str]   # ['sensor', 'satellite', 'excel']
    location_count: int
    time_range_start: datetime
    time_range_end: datetime
    average_confidence: float
    event_type: str = "fusion.completed"

@dataclass
class CalibrationUpdated(DomainEvent):
    """Published when sensor calibration is updated"""
    sensor_id: UUID
    old_params: Dict
    new_params: Dict
    r_squared: float
    event_type: str = "calibration.updated"

@dataclass
class CrossValidationAlert(DomainEvent):
    """Published when cross-validation detects anomaly"""
    sensor_id: UUID
    sensor_value: float
    satellite_value: float
    deviation_percent: float
    event_type: str = "validation.alert"
```

---

## API Endpoints (Updated)

### Remote Sensing Service APIs

```
# Satellite Data
GET    /api/v1/satellite/data                  # List satellite data
GET    /api/v1/satellite/data/{source}         # Get by source (modis, tropomi, cams)
POST   /api/v1/satellite/fetch                 # Trigger manual fetch
GET    /api/v1/satellite/schedule              # Get fetch schedule
PUT    /api/v1/satellite/schedule              # Update fetch schedule

# Excel Import
POST   /api/v1/excel/import/readings           # Import historical readings
POST   /api/v1/excel/import/factories          # Import factory records
GET    /api/v1/excel/import/{id}/status        # Get import status
GET    /api/v1/excel/templates                 # Get Excel templates
```

### Air Quality Service APIs (Enhanced)

```
# Data Fusion
GET    /api/v1/air-quality/fused               # Get fused data
POST   /api/v1/air-quality/fuse                # Trigger data fusion
GET    /api/v1/air-quality/fused/map           # Fused data for map display

# Cross-Validation
GET    /api/v1/air-quality/validation/report   # Validation report
GET    /api/v1/air-quality/validation/sensors  # Sensor validation status

# Calibration
GET    /api/v1/air-quality/calibration/status  # Calibration model status
POST   /api/v1/air-quality/calibration/train   # Retrain calibration model
GET    /api/v1/air-quality/calibration/metrics # Model performance metrics

# Existing
GET    /api/v1/air-quality/current             # Current AQI
GET    /api/v1/air-quality/forecast            # Predictions
GET    /api/v1/air-quality/heatmap/tiles       # Google Maps tiles
```

---

## Environment Variables (Updated)

```bash
# .env.example

# === Databases ===
FACTORY_DB_URL=postgresql://user:pass@factory-db:5432/factory_db
SENSOR_DB_URL=postgresql://user:pass@sensor-db:5433/sensor_db
REMOTE_SENSING_DB_URL=postgresql://user:pass@remote-db:5434/remote_db
ALERT_DB_URL=postgresql://user:pass@alert-db:5435/alert_db
USER_DB_URL=postgresql://user:pass@user-db:5436/user_db
REDIS_URL=redis://redis:6379

# === Message Broker ===
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672

# === External APIs - Remote Sensing ===
COPERNICUS_ADS_API_KEY=your-copernicus-ads-api-key
COPERNICUS_ADS_URL=https://ads.atmosphere.copernicus.eu/api/v2
NASA_EARTHDATA_TOKEN=your-nasa-earthdata-token
SENTINEL_HUB_CLIENT_ID=your-sentinel-hub-client-id
SENTINEL_HUB_CLIENT_SECRET=your-sentinel-hub-secret
GOOGLE_EARTH_ENGINE_SERVICE_ACCOUNT=your-gee-service-account

# === Google Maps ===
VITE_GOOGLE_MAPS_API_KEY=your-google-maps-api-key

# === Satellite Data Fetch Schedule ===
SATELLITE_FETCH_CRON="0 */6 * * *"   # Every 6 hours
MODIS_FETCH_ENABLED=true
TROPOMI_FETCH_ENABLED=true
CAMS_FETCH_ENABLED=true

# === Data Fusion Settings ===
FUSION_INTERVAL_MINUTES=60
CALIBRATION_RETRAIN_DAYS=7
CROSS_VALIDATION_TOLERANCE=0.3

# === Authentication ===
JWT_SECRET=your-super-secret-key
JWT_ALGORITHM=HS256

# === Frontend ===
VITE_API_URL=http://localhost:8000/api/v1
```

---

## Docker Compose Services (Updated)

```yaml
# docker-compose.yml (excerpt for new services)

services:
  # ... existing services ...

  remote-sensing-service:
    build: ./services/remote-sensing-service
    ports:
      - "8003:8003"
    environment:
      - DATABASE_URL=${REMOTE_SENSING_DB_URL}
      - RABBITMQ_URL=${RABBITMQ_URL}
      - COPERNICUS_ADS_API_KEY=${COPERNICUS_ADS_API_KEY}
      - NASA_EARTHDATA_TOKEN=${NASA_EARTHDATA_TOKEN}
      - SENTINEL_HUB_CLIENT_ID=${SENTINEL_HUB_CLIENT_ID}
      - SENTINEL_HUB_CLIENT_SECRET=${SENTINEL_HUB_CLIENT_SECRET}
    depends_on:
      - remote-db
      - rabbitmq
    volumes:
      - satellite_data:/app/data  # Store downloaded satellite files

  remote-db:
    image: postgres:15
    ports:
      - "5434:5432"
    environment:
      - POSTGRES_DB=remote_db
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - remote_db_data:/var/lib/postgresql/data

volumes:
  satellite_data:
  remote_db_data:
```

---

## Important Rules

1. **Use JavaScript** (.js, .jsx) for frontend
2. **Follow DDD layers**: Domain → Application → Infrastructure → Interface
3. **Domain layer has NO dependencies** on other layers
4. **Each service owns its database** - no shared databases
5. **Remote Sensing Service** fetches satellite data on schedule
6. **Air Quality Service** performs data fusion and calibration
7. **Cross-validation** compares sensors vs satellite reference
8. **Publish events** after significant operations
9. **API Gateway** is the single entry point

---

*This document is the single source of truth. Follow this architecture exactly.*

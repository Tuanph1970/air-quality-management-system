# Claude Code Prompts - Microservice Architecture with DDD

Ready-to-use prompts for building the Air Quality Management System with **Microservices**, **Domain-Driven Design**, **Remote Sensing Integration**, and **Data Fusion**.

---

## 🚀 Phase 0: Initial Setup

### Prompt 0.1 - Create Project Structure
```
Read CLAUDE.md and create the complete microservice project structure.

Create:
1. Root docker-compose.yml with all 7 services defined
2. services/ folder with subfolders for each microservice:
   - api-gateway (port 8000)
   - factory-service (port 8001)
   - sensor-service (port 8002)
   - remote-sensing-service (port 8003) ⭐ NEW
   - alert-service (port 8004)
   - air-quality-service (port 8005)
   - user-service (port 8006)
   - shared (shared libraries)
3. frontend/ folder for React app
4. .env.example with all environment variables including satellite API keys
5. scripts/ folder with utility scripts

For each microservice, create the DDD folder structure:
- src/domain/ (entities, value_objects, repositories, services, events)
- src/application/ (commands, queries, dto, services)
- src/infrastructure/ (persistence, messaging, external)
- src/interfaces/ (api)
- tests/
- Dockerfile
- requirements.txt
- main.py

Create placeholder __init__.py files. Do NOT implement logic yet.
```

### Prompt 0.2 - Docker Compose Configuration
```
Create the complete docker-compose.yml for development:

Services (7 microservices + infrastructure):
1. api-gateway (port 8000) - depends on all backend services
2. factory-service (port 8001) - depends on factory-db, rabbitmq
3. sensor-service (port 8002) - depends on sensor-db (TimescaleDB), rabbitmq
4. remote-sensing-service (port 8003) - depends on remote-db, rabbitmq ⭐ NEW
5. alert-service (port 8004) - depends on alert-db, rabbitmq
6. air-quality-service (port 8005) - depends on redis, rabbitmq
7. user-service (port 8006) - depends on user-db
8. frontend (port 3000) - Nginx serving React

Databases (5 PostgreSQL + 1 Redis):
- factory-db (PostgreSQL, port 5432)
- sensor-db (TimescaleDB, port 5433)
- remote-db (PostgreSQL, port 5434) ⭐ NEW for satellite data
- alert-db (PostgreSQL, port 5435)
- user-db (PostgreSQL, port 5436)
- redis (port 6379)

Message Broker:
- rabbitmq (ports 5672, 15672) with management plugin

Volumes:
- satellite_data volume for downloaded satellite files
- Data persistence volumes for all databases

Include health checks for all databases.
Also create docker-compose.prod.yml for production.
```

---

## 📦 Phase 1: Shared Libraries

### Prompt 1.1 - Shared Event Definitions (Updated)
```
Create the shared event library in services/shared/events/:

base_event.py:
- DomainEvent base dataclass
- event_id, occurred_at, event_type
- to_dict(), from_dict() methods

factory_events.py:
- FactoryCreated, FactoryUpdated, FactoryStatusChanged
- FactorySuspended, FactoryResumed

sensor_events.py:
- SensorRegistered, SensorReadingCreated
- SensorCalibrated, SensorStatusChanged

satellite_events.py: ⭐ NEW
- SatelliteDataFetched (source, data_type, observation_time, bbox, record_count)
- ExcelDataImported (import_id, filename, record_count, data_type)
- SatelliteFetchFailed (source, error_message)

fusion_events.py: ⭐ NEW
- DataFusionCompleted (fusion_id, sources_used, location_count, average_confidence)
- CalibrationUpdated (sensor_id, old_params, new_params, r_squared)
- CrossValidationAlert (sensor_id, sensor_value, satellite_value, deviation_percent)

alert_events.py:
- ViolationDetected, ViolationResolved, AlertConfigUpdated
```

### Prompt 1.2 - Shared Messaging Library
```
Create the shared messaging library in services/shared/messaging/:

publisher.py:
- RabbitMQPublisher class with aio_pika
- connect(), publish(event, exchange), close()
- Retry logic for connection failures

consumer.py:
- RabbitMQConsumer class
- subscribe(queue, handler), start_consuming()

config.py:
- Exchange names:
  - FACTORY_EXCHANGE = "factory.events"
  - SENSOR_EXCHANGE = "sensor.events"
  - SATELLITE_EXCHANGE = "satellite.events"  ⭐ NEW
  - FUSION_EXCHANGE = "fusion.events"        ⭐ NEW
  - ALERT_EXCHANGE = "alert.events"

Include reconnection logic and error handling.
```

### Prompt 1.3 - Shared Auth Library
```
Create the shared auth library in services/shared/auth/:

jwt_handler.py:
- create_access_token(user_id, role) -> str
- verify_token(token) -> dict
- decode_token(token) -> dict

dependencies.py:
- get_current_user() FastAPI dependency
- require_role(roles) decorator

exceptions.py:
- AuthenticationError, AuthorizationError
```

---

## 🏭 Phase 2: Factory Service

### Prompt 2.1 - Factory Domain Layer
```
Create Factory Service domain layer in services/factory-service/src/domain/:

entities/factory.py:
- Factory entity with id, name, registration_number, industry_type
- location (Location value object)
- emission_limits (EmissionLimits value object)
- status (FactoryStatus enum)
- Business methods: suspend(), resume(), update_status_from_emissions()
- collect_events() for domain events

value_objects/:
- location.py: Location (frozen, with validation)
- factory_status.py: FactoryStatus enum (ACTIVE, WARNING, CRITICAL, SUSPENDED)
- emission_limit.py: EmissionLimits (pm25, pm10, co2, nox limits)

repositories/factory_repository.py:
- Abstract FactoryRepository interface

events/factory_events.py:
- Import from shared/events

Domain layer must have NO external dependencies.
```

### Prompt 2.2 - Factory Application & Infrastructure
```
Create Factory Service application and infrastructure layers:

Application layer:
- commands/: create_factory, update_factory, suspend_factory, resume_factory
- queries/: get_factory, list_factories, get_factory_emissions
- dto/factory_dto.py: FactoryDTO with from_entity()
- services/factory_application_service.py: orchestrates use cases

Infrastructure layer:
- persistence/database.py: AsyncEngine, get_db()
- persistence/models.py: FactoryModel, SuspensionModel
- persistence/factory_repository_impl.py: SQLAlchemy implementation
- messaging/rabbitmq_publisher.py: EventPublisher implementation
- messaging/event_handlers.py: Handle incoming events

Create Dockerfile, requirements.txt, alembic migrations.
```

### Prompt 2.3 - Factory API & Main
```
Create Factory Service API layer:

interfaces/api/schemas.py:
- FactoryCreateRequest, FactoryUpdateRequest
- FactoryResponse, FactoryListResponse
- SuspendRequest, ResumeRequest

interfaces/api/factory_controller.py:
- POST /factories, GET /factories, GET /factories/{id}
- PUT /factories/{id}, DELETE /factories/{id}
- POST /factories/{id}/suspend, POST /factories/{id}/resume

main.py:
- FastAPI app with CORS, routes, health check
- Startup: connect RabbitMQ
- Shutdown: close connections
```

---

## 📡 Phase 3: Sensor Service

### Prompt 3.1 - Sensor Domain Layer
```
Create Sensor Service domain layer in services/sensor-service/src/domain/:

entities/sensor.py:
- Sensor entity: id, serial_number, sensor_type, model
- factory_id, location, calibration_params, status
- Methods: register(), calibrate(), update_status()

entities/reading.py:
- Reading entity (time-series data)
- time, sensor_id, pm25, pm10, co2, no2, temperature, humidity, aqi

value_objects/:
- sensor_type.py: SensorType enum (LOW_COST_PM, REFERENCE_STATION, MULTI_GAS)
- sensor_status.py: SensorStatus enum (ONLINE, OFFLINE, CALIBRATING)
- calibration_params.py: CalibrationParams (slope, intercept, r_squared per pollutant)
- air_quality_reading.py: AirQualityReading (all pollutant values)

repositories/:
- sensor_repository.py: SensorRepository interface
- reading_repository.py: ReadingRepository interface (for TimescaleDB)

services/aqi_calculator.py:
- Domain service: calculate_aqi(), get_dominant_pollutant()
```

### Prompt 3.2 - Sensor Infrastructure (TimescaleDB)
```
Create Sensor Service infrastructure with TimescaleDB:

persistence/timescale_database.py:
- TimescaleDB connection setup
- Create hypertable for sensor_readings

persistence/models.py:
- SensorModel (regular PostgreSQL table)
- SensorReadingModel (TimescaleDB hypertable)

persistence/sensor_repository_impl.py:
- SQLAlchemy implementation

persistence/reading_repository_impl.py:
- TimescaleDB-specific queries
- time_bucket() for aggregation
- Efficient time-range queries

Create alembic migration that:
1. Creates sensors table
2. Creates sensor_readings hypertable
3. Creates continuous aggregates (hourly_readings)
```

### Prompt 3.3 - Sensor API & Events
```
Create Sensor Service API and event publishing:

interfaces/api/sensor_controller.py:
- POST /sensors - register sensor
- GET /sensors - list sensors
- GET /sensors/{id} - get details
- POST /sensors/{id}/readings - submit reading (IoT endpoint)
- GET /sensors/{id}/readings - get readings with time range
- POST /sensors/{id}/calibrate - update calibration params

IMPORTANT: When a reading is submitted:
1. Calculate AQI using domain service
2. Save to TimescaleDB
3. Publish SensorReadingCreated event to RabbitMQ

This event will be consumed by:
- Alert Service (check thresholds)
- Air Quality Service (data fusion)

Create main.py, Dockerfile, requirements.txt.
```

---

## 🛰️ Phase 4: Remote Sensing Service ⭐ NEW

### Prompt 4.1 - Remote Sensing Domain Layer
```
Create Remote Sensing Service domain layer in services/remote-sensing-service/src/domain/:

entities/satellite_data.py:
- SatelliteData entity:
  - id, source (MODIS, TROPOMI, CAMS)
  - data_type (AOD, NO2, PM25, etc.)
  - observation_time
  - bbox (GeoPolygon value object)
  - grid_data (Dict of grid cells with values)
  - quality_flag
  - metadata
  - from_netcdf() factory method

entities/excel_import.py:
- ExcelImport entity:
  - id, filename, import_time
  - record_count, data_type
  - status (PENDING, PROCESSING, COMPLETED, FAILED)
  - errors list
  - validation_result

entities/data_source.py:
- DataSource entity for managing configured sources
  - id, name, source_type, api_endpoint
  - credentials, fetch_schedule, is_active

value_objects/satellite_source.py:
- SatelliteSource value object:
  - MODIS_AOD, TROPOMI_NO2, TROPOMI_SO2, TROPOMI_O3
  - CAMS_PM25, CAMS_PM10, CAMS_FORECAST

value_objects/geo_polygon.py:
- GeoPolygon (frozen): north, south, east, west
- contains(lat, lon), get_center(), area()

value_objects/grid_cell.py:
- GridCell (frozen): lat, lon, value, uncertainty

value_objects/quality_flag.py:
- QualityFlag enum: GOOD, MEDIUM, LOW, INVALID

repositories/:
- satellite_data_repository.py
- excel_import_repository.py
- data_source_repository.py

events/remote_sensing_events.py:
- Import from shared/events/satellite_events.py
```

### Prompt 4.2 - Remote Sensing External API Clients
```
Create External API clients in services/remote-sensing-service/src/infrastructure/external/:

copernicus_cams_client.py:
- CopernicusCAMSClient class
- BASE_URL = "https://ads.atmosphere.copernicus.eu/api/v2"
- authenticate() - use API key from env
- get_forecast(variable, bbox, date) - fetch CAMS forecast
- get_reanalysis(variable, bbox, date_range) - historical data
- Variables: pm2p5, pm10, no2, o3, so2, co
- Return parsed data as SatelliteData entity

nasa_earthdata_client.py:
- NASAEarthdataClient class
- BASE_URL = "https://ladsweb.modaps.eosdis.nasa.gov/api/v2"
- authenticate() - use NASA Earthdata token
- get_modis_aod(product, bbox, date) - fetch MODIS AOD
- Products: MOD04_L2 (Terra), MYD04_L2 (Aqua)
- Download NetCDF files and parse

sentinel_hub_client.py:
- SentinelHubClient class
- authenticate() - OAuth2 with client credentials
- get_tropomi_data(product, bbox, date)
- Products: L2__NO2___, L2__SO2___, L2__O3___, L2__CO___
- Handle Sentinel-5P data format

google_earth_engine_client.py:
- GoogleEarthEngineClient class
- authenticate() - service account
- get_collection_data(collection, bbox, date_range)
- Collections: COPERNICUS/S5P/OFFL/L3_NO2, MODIS/006/MOD04_L2

Each client should:
- Handle authentication
- Implement retry logic
- Parse response to domain entities
- Handle errors gracefully
```

### Prompt 4.3 - Remote Sensing Data Parsers
```
Create data file parsers in services/remote-sensing-service/src/infrastructure/parsers/:

netcdf_parser.py:
- NetCDFParser class
- parse_modis_aod(filepath) -> SatelliteData
- parse_tropomi(filepath, variable) -> SatelliteData
- parse_cams(filepath, variable) -> SatelliteData
- Extract grid data, coordinates, timestamps
- Handle different NetCDF structures
- Use xarray or netCDF4 library

geotiff_parser.py:
- GeoTIFFParser class
- parse(filepath) -> SatelliteData
- Extract raster data with coordinates
- Use rasterio library

excel_parser.py:
- ExcelParser class
- parse_historical_readings(filepath) -> List[Dict]
  - Expected columns: timestamp, location_id, pm25, pm10, etc.
- parse_factory_records(filepath) -> List[Dict]
  - Expected columns: factory_name, registration_number, lat, lng, etc.
- validate_format(filepath, expected_columns) -> ValidationResult
- Use openpyxl or pandas

Add to requirements.txt:
- xarray
- netCDF4
- rasterio
- openpyxl
- pandas
```

### Prompt 4.4 - Remote Sensing Scheduler
```
Create satellite data fetch scheduler in services/remote-sensing-service/src/infrastructure/scheduler/:

satellite_scheduler.py:
- SatelliteScheduler class
- Use APScheduler for periodic jobs
- Jobs:
  - fetch_modis_daily() - Run daily at 02:00 UTC
  - fetch_tropomi_daily() - Run daily at 03:00 UTC
  - fetch_cams_hourly() - Run every 6 hours
- Each job:
  1. Fetch data from external API
  2. Parse to domain entity
  3. Save to database
  4. Publish SatelliteDataFetched event
- Handle failures: retry 3 times, then publish SatelliteFetchFailed
- Configurable schedule via environment variables

scheduler_config.py:
- Load schedule from environment
- MODIS_FETCH_CRON, TROPOMI_FETCH_CRON, CAMS_FETCH_CRON
- Default bounding box for city

In main.py:
- Start scheduler on application startup
- Graceful shutdown of scheduler jobs
```

### Prompt 4.5 - Remote Sensing Application Services
```
Create Remote Sensing application services:

application/services/satellite_data_service.py:
- SatelliteDataService class
- fetch_modis_aod(date, bbox) -> SatelliteData
- fetch_tropomi(variable, date, bbox) -> SatelliteData
- fetch_cams_forecast(bbox, hours) -> List[SatelliteData]
- get_latest_data(source) -> SatelliteData
- get_data_for_location(lat, lon, date) -> Dict
- schedule_fetch(sources) - configure scheduled fetching

application/services/excel_import_service.py:
- ExcelImportService class
- import_historical_readings(file) -> ExcelImport
- import_factory_records(file) -> ExcelImport
- get_import_status(import_id) -> ExcelImport
- validate_and_preview(file) -> ValidationResult
- After successful import, publish ExcelDataImported event

application/commands/:
- fetch_satellite_data_command.py
- import_excel_command.py
- configure_source_command.py

application/queries/:
- get_satellite_data_query.py
- get_import_status_query.py
- list_data_sources_query.py
```

### Prompt 4.6 - Remote Sensing API
```
Create Remote Sensing Service API:

interfaces/api/satellite_controller.py:
- GET /satellite/data - List all satellite data with filters
  - Query params: source, data_type, start_date, end_date
- GET /satellite/data/{source} - Get latest by source
- GET /satellite/data/location - Get data for specific lat/lon
  - Query params: lat, lon, date
- POST /satellite/fetch - Trigger manual fetch
  - Body: { source, date, bbox }
- GET /satellite/sources - List configured data sources
- POST /satellite/sources - Add new data source
- GET /satellite/schedule - Get fetch schedule
- PUT /satellite/schedule - Update fetch schedule

interfaces/api/excel_controller.py:
- POST /excel/import/readings - Upload and import historical readings
  - Accept multipart file upload
- POST /excel/import/factories - Upload and import factory records
- GET /excel/import/{id}/status - Get import status
- GET /excel/templates/{type} - Download Excel template

interfaces/api/schemas.py:
- SatelliteDataResponse
- FetchRequest
- ExcelImportResponse
- DataSourceRequest/Response

Create main.py with:
- FastAPI app
- Start scheduler on startup
- File upload configuration
- Health check endpoint
```

---

## 🌍 Phase 5: Air Quality Service (Data Fusion) ⭐ ENHANCED

### Prompt 5.1 - Data Fusion Domain Services
```
Create Data Fusion domain services in services/air-quality-service/src/domain/services/:

data_fusion.py:
- FusedDataPoint dataclass:
  - location, timestamp
  - sensor_pm25, sensor_pm10 (optional)
  - satellite_aod, satellite_pm25 (optional)
  - fused_pm25, fused_pm10, fused_aqi
  - confidence (0-1)
  - data_sources list

- DataFusionService class:
  - fuse_data(sensor_readings, satellite_data, excel_data) -> List[FusedDataPoint]
  - Algorithm:
    1. Spatial matching: Find satellite grid cell for each sensor
    2. Temporal alignment: Aggregate to common time resolution
    3. Apply calibration model
    4. Gap filling with satellite where no sensors
    5. Calculate confidence based on data availability

cross_validator.py:
- ValidationResult dataclass:
  - sensor_id, correlation, bias, rmse, is_valid

- CrossValidationService class:
  - validate_sensor(sensor_id, sensor_readings, satellite_data) -> ValidationResult
  - batch_validate(all_sensors, satellite_data) -> List[ValidationResult]
  - detect_anomalies(readings, threshold) -> List[AnomalyAlert]
  - If deviation > threshold, publish CrossValidationAlert event

calibration_model.py:
- CalibratedReading dataclass:
  - original_value, calibrated_value, confidence

- CalibrationModel class:
  - __init__(model_path) - load or create ML model
  - calibrate(raw_reading, satellite_reference, environmental_factors) -> CalibratedReading
  - train(training_data: List[Tuple[raw, reference]]) -> TrainingResult
  - evaluate(test_data) -> EvaluationMetrics (R², RMSE, MAE)
  - save_model(path), load_model(path)
  - Use RandomForestRegressor or GradientBoostingRegressor
  - Features: raw_value, temperature, humidity, satellite_aod, hour, sensor_age
```

### Prompt 5.2 - Air Quality Application Services
```
Create Air Quality application services:

application/services/air_quality_application_service.py:
- AirQualityApplicationService class:
  - Inject: fusion_service, calibration_model, sensor_client, satellite_client
  
  - fuse_current_data(bbox) -> List[FusedDataPoint]
    1. Get latest sensor readings (call Sensor Service API)
    2. Get latest satellite data (call Remote Sensing Service API)
    3. Run data fusion
    4. Publish DataFusionCompleted event
    5. Return fused data
  
  - get_map_data(bbox, layer_type) -> MapData
    - Return data formatted for Google Maps heatmap
  
  - validate_all_sensors() -> ValidationReport
    - Cross-validate all sensors against satellite
    - Return report with status per sensor
  
  - retrain_calibration(training_window_days) -> TrainingResult
    - Collect historical data
    - Retrain ML model
    - Publish CalibrationUpdated event
  
  - get_current_aqi(lat, lon) -> AQIResponse
  - get_forecast(lat, lon, hours) -> List[ForecastPoint]

application/commands/:
- fuse_data_command.py
- train_calibration_command.py
- validate_sensors_command.py

application/queries/:
- get_fused_data_query.py
- get_map_data_query.py
- get_validation_report_query.py
- get_calibration_metrics_query.py
```

### Prompt 5.3 - Air Quality Event Consumers
```
Create event consumers for Air Quality Service:

infrastructure/messaging/event_consumers.py:

SensorReadingConsumer:
- Subscribe to "sensor.reading.created" queue
- When SensorReadingCreated received:
  1. Get corresponding satellite data for same time/location
  2. Run cross-validation
  3. If anomaly detected, publish CrossValidationAlert
  4. Store calibrated reading

SatelliteDataConsumer:
- Subscribe to "satellite.data.fetched" queue
- When SatelliteDataFetched received:
  1. Trigger data fusion for the covered area
  2. Update calibration if enough new data
  3. Cache results in Redis

Start consumers in main.py on startup.
Handle message acknowledgment properly.
```

### Prompt 5.4 - Air Quality API
```
Create Air Quality Service API:

interfaces/api/air_quality_controller.py:

Data Fusion endpoints:
- GET /air-quality/fused?bbox=&time= - Get fused data
- POST /air-quality/fuse - Trigger manual fusion
- GET /air-quality/fused/map - Data for map display

Cross-Validation endpoints:
- GET /air-quality/validation/report - Full validation report
- GET /air-quality/validation/sensors/{id} - Single sensor validation
- POST /air-quality/validation/run - Trigger validation

Calibration endpoints:
- GET /air-quality/calibration/status - Model status
- GET /air-quality/calibration/metrics - Model performance
- POST /air-quality/calibration/train - Retrain model

Standard AQI endpoints:
- GET /air-quality/current?lat=&lng= - Current AQI
- GET /air-quality/forecast?lat=&lng=&hours= - Forecast
- GET /air-quality/heatmap/tiles/{z}/{x}/{y} - Google Maps tiles

Create main.py, Dockerfile, requirements.txt.
Add scikit-learn, pandas, numpy to requirements.
```

---

## ⚠️ Phase 6: Alert Service

### Prompt 6.1 - Alert Domain Layer
```
Create Alert Service domain layer:

entities/violation.py:
- Violation entity with factory_id, sensor_id
- pollutant, measured_value, permitted_value
- severity (value object), detected_at, resolved_at

entities/alert_config.py:
- AlertConfig with thresholds (warning, high, critical)
- per pollutant configuration

services/threshold_checker.py:
- Domain service to check readings against thresholds
- Returns Violation or None

repositories/:
- violation_repository.py
- alert_config_repository.py
```

### Prompt 6.2 - Alert Event Consumer
```
Create Alert Service event consumer:

infrastructure/messaging/event_consumers.py:

FusedDataConsumer:
- Subscribe to "fusion.completed" queue
- When DataFusionCompleted received:
  1. Get fused data points
  2. For each point near a factory:
     - Get factory emission limits
     - Check against thresholds
     - Create Violation if exceeded
     - Publish ViolationDetected event

CrossValidationAlertConsumer:
- Subscribe to "validation.alert" queue
- When CrossValidationAlert received:
  - Create alert record
  - Notify operators of sensor malfunction

Start consumers on service startup.
```

### Prompt 6.3 - Alert API
```
Create Alert Service API:

interfaces/api/alert_controller.py:
- GET /violations - List with filters
- GET /violations/{id} - Details
- PUT /violations/{id}/resolve - Resolve
- GET /alerts/active - Active alerts count
- GET /alerts/config - Get configurations
- PUT /alerts/config - Update configurations

Create main.py, Dockerfile, requirements.txt.
```

---

## 👤 Phase 7: User Service

### Prompt 7.1 - User Service Complete
```
Create User Service with authentication:

domain/entities/user.py:
- User entity with email, password_hash, role
- Methods: register(), verify_password()

domain/services/auth_service.py:
- hash_password(), verify_password() using bcrypt

application/services/user_application_service.py:
- register(), login(), get_user()
- Return JWT tokens

interfaces/api/auth_controller.py:
- POST /auth/register
- POST /auth/login
- GET /auth/me
- POST /auth/refresh

Create Dockerfile, requirements.txt, migrations.
```

---

## 🚪 Phase 8: API Gateway

### Prompt 8.1 - API Gateway Implementation
```
Create API Gateway service:

src/middleware/:
- auth_middleware.py - JWT verification
- rate_limiter.py - Redis-based rate limiting
- request_logger.py - Log all requests

src/utils/service_client.py:
- ServiceClient class for HTTP calls
- Retry logic, circuit breaker

src/routes/:
- factory_routes.py - Proxy to factory-service:8001
- sensor_routes.py - Proxy to sensor-service:8002
- satellite_routes.py - Proxy to remote-sensing-service:8003 ⭐ NEW
- alert_routes.py - Proxy to alert-service:8004
- air_quality_routes.py - Proxy to air-quality-service:8005
- auth_routes.py - Proxy to user-service:8006

src/routes/dashboard_routes.py:
- GET /dashboard/summary - Aggregate from multiple services:
  - Factory counts from factory-service
  - Sensor status from sensor-service
  - Latest satellite data from remote-sensing-service ⭐ NEW
  - Violation count from alert-service
  - Current AQI from air-quality-service

Create main.py, Dockerfile, requirements.txt.
```

---

## 💻 Phase 9: Frontend

### Prompt 9.1 - Frontend Setup
```
Set up React frontend with JavaScript (NOT TypeScript):

1. Create Vite project: npm create vite@latest frontend -- --template react

2. Install dependencies:
   - react-router-dom, axios, zustand
   - recharts, @react-google-maps/api
   - lucide-react, prop-types, date-fns

3. Configure vite.config.js, tailwind.config.js

4. Create folder structure:
   - components/common/, layout/, maps/, charts/, factories/, alerts/, sensors/
   - pages/, hooks/, services/, store/, utils/

5. Create services/api.js pointing to API Gateway

Use .js and .jsx files ONLY - no TypeScript.
```

### Prompt 9.2 - Frontend Components
```
Create frontend components:

components/layout/:
- Header.jsx, Sidebar.jsx, Layout.jsx

components/common/:
- Button, Card, Modal, Badge, Table, Loading

components/maps/:
- AirQualityMap.jsx - Main map component
- HeatmapLayer.jsx - Google AQ heatmap + custom fused data layer
- FactoryMarker.jsx, SensorMarker.jsx
- DataSourceToggle.jsx ⭐ NEW - Toggle sensor/satellite/fused data

components/charts/:
- TrendChart.jsx, AQIGauge.jsx, EmissionChart.jsx
- ValidationChart.jsx ⭐ NEW - Show sensor vs satellite comparison

components/satellite/: ⭐ NEW
- SatelliteDataPanel.jsx - Show latest satellite data
- ExcelImportModal.jsx - Upload Excel files
- DataSourceStatus.jsx - Show status of each data source

pages/:
- Dashboard.jsx (include satellite data status)
- MapView.jsx (with data source toggle)
- Factories.jsx, FactoryDetail.jsx
- Sensors.jsx (with validation status)
- Alerts.jsx
- DataSources.jsx ⭐ NEW - Manage satellite sources and Excel imports
- Reports.jsx, Settings.jsx

Use PropTypes for all components.
Dark theme with TailwindCSS.
```

### Prompt 9.3 - Frontend Docker
```
Create Docker configuration for frontend:

Dockerfile:
- Stage 1: Build with Node (npm install, npm run build)
- Stage 2: Serve with Nginx

nginx.conf:
- Serve static files
- Proxy /api/* to api-gateway:8000
- Enable gzip
- SPA fallback

Update docker-compose.yml to include frontend service.
```

---

## 🧪 Phase 10: Integration Testing

### Prompt 10.1 - End-to-End Test
```
Create integration test that verifies complete data flow:

scripts/test_integration.py:

1. Import test data via Excel
   - POST /api/v1/excel/import/readings with sample file
   - Verify import completed

2. Register a sensor
   - POST /api/v1/sensors

3. Submit sensor readings
   - POST /api/v1/sensors/{id}/readings

4. Fetch satellite data (or use mock)
   - POST /api/v1/satellite/fetch

5. Trigger data fusion
   - POST /api/v1/air-quality/fuse
   - Verify DataFusionCompleted event published

6. Check cross-validation
   - GET /api/v1/air-quality/validation/report
   - Verify sensors validated against satellite

7. Verify calibration
   - GET /api/v1/air-quality/calibration/metrics
   - Check R², RMSE values

8. If violation occurred:
   - Verify ViolationDetected event
   - GET /api/v1/violations

Use httpx for async HTTP calls.
Wait for event propagation between services.
```

### Prompt 10.2 - Sample Data Scripts
```
Create sample data scripts in scripts/:

fetch-satellite-sample.py:
- Fetch sample CAMS data for test city
- Store as JSON for offline testing

simulate-sensors.py:
- Generate realistic sensor readings
- Some readings should deviate from satellite to test validation
- Submit to Sensor Service API

generate-test-excel.py:
- Create sample Excel files for import testing
- Historical readings format
- Factory records format
```

---

## 🚀 Phase 11: Production

### Prompt 11.1 - Production Configuration
```
Create production-ready configuration:

docker-compose.prod.yml:
- No port exposure except nginx (80, 443)
- Resource limits for all services
- Production environment variables
- Restart policies
- Volume mounts for persistent data

.env.prod.example:
- Strong JWT secret
- Production database passwords
- Real satellite API keys
- Production Google Maps key

scripts/deploy.sh:
- Pull latest images
- Run migrations for all services
- Rolling restart
- Health check verification
```

---

## 💡 Quick Reference

### Service URLs
| Service | Development URL | Purpose |
|---------|-----------------|---------|
| API Gateway | http://localhost:8000 | Single entry point |
| Factory Service | http://localhost:8001 | Factory management |
| Sensor Service | http://localhost:8002 | Sensors & readings |
| Remote Sensing Service | http://localhost:8003 | Satellite & Excel data |
| Alert Service | http://localhost:8004 | Violations & alerts |
| Air Quality Service | http://localhost:8005 | Fusion, calibration, AQI |
| User Service | http://localhost:8006 | Authentication |
| Frontend | http://localhost:3000 | Web application |
| RabbitMQ | http://localhost:15672 | Message broker UI |

### Data Flow Summary
```
Excel Import ─────────────┐
                          │
Satellite APIs ──────────►│ Remote Sensing Service
  - MODIS                 │         │
  - TROPOMI               │         │ SatelliteDataFetched
  - CAMS                  │         ▼
                          │    Air Quality Service
IoT Sensors ─────────────►│ Sensor Service    │
                          │         │         │
                          │         │ SensorReadingCreated
                          │         ▼         │
                          └──► Data Fusion ◄──┘
                                    │
                                    ▼
                              Alert Service
                                    │
                              ViolationDetected
                                    ▼
                              Factory Service
                              (status update)
```

### Common Fix Prompts

```
The remote-sensing-service cannot connect to Copernicus API. Check credentials and network configuration.
```

```
Data fusion is not running. Verify that SatelliteDataFetched events are being published and consumed.
```

```
Calibration model shows low R². Check if enough training data is available and features are correctly computed.
```

```
Cross-validation is flagging all sensors as anomalies. Adjust the tolerance threshold in configuration.
```

---

*Follow these prompts in order for best results.*

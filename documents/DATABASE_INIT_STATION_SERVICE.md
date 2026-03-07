# Station Service - Database Initialization Guide

## Overview

The Station Service uses MySQL database `station_db` with two main tables:
- `stations` - Station metadata and configuration
- `pollutant_readings` - Time-series air quality readings

Tables are created **automatically** on service startup via SQLAlchemy's metadata creation.

---

## Automatic Table Creation

When you start the service with Docker Compose, tables are created automatically:

```bash
docker compose up -d station-service
```

The service performs these steps on startup:

1. **Database Creation**: `station_db` is created by `scripts/init-mysql.sql` on first MySQL startup
2. **Table Creation**: SQLAlchemy creates tables via `init_database()` in the lifespan event
3. **Verification**: Logs show table creation status

### Startup Logs

You should see:
```
2024-01-15 10:00:00 | INFO     | Starting station-service...
2024-01-15 10:00:01 | INFO     | Database tables created/verified
2024-01-15 10:00:02 | INFO     | RabbitMQ publisher connected
2024-01-15 10:00:02 | INFO     | station-service started successfully
```

---

## Manual Table Creation

If you need to create tables manually:

### Option 1: Run Init Script

```bash
# From project root
docker compose exec station-service python scripts/init_tables.py
```

### Option 2: Direct SQL

```bash
# Access MySQL
docker exec -it aqms-mysql mysql -u root -pMysql_2026

# Use station database
USE station_db;

# Create stations table
CREATE TABLE IF NOT EXISTS stations (
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
    last_data_received DATETIME,
    INDEX idx_station_code (station_code),
    INDEX idx_station_active (is_active),
    INDEX idx_station_location (latitude, longitude)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

# Create pollutant_readings table
CREATE TABLE IF NOT EXISTS pollutant_readings (
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
    INDEX idx_time_pollutant (timestamp, pollutant_type),
    UNIQUE KEY uq_station_time_pollutant (station_id, timestamp, pollutant_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

## Verify Tables

### Check Tables Exist

```bash
docker exec -it aqms-mysql mysql -u root -pMysql_2026 -e "USE station_db; SHOW TABLES;"
```

Expected output:
```
Tables_in_station_db
stations
pollutant_readings
```

### Check Table Structure

```bash
# Stations table
docker exec -it aqms-mysql mysql -u root -pMysql_2026 -e "USE station_db; DESCRIBE stations;"

# Readings table
docker exec -it aqms-mysql mysql -u root -pMysql_2026 -e "USE station_db; DESCRIBE pollutant_readings;"
```

### Check Data

```bash
# List stations
docker exec -it aqms-mysql mysql -u root -pMysql_2026 -e "USE station_db; SELECT id, station_code, name, station_type, is_active FROM stations;"

# List recent readings
docker exec -it aqms-mysql mysql -u root -pMysql_2026 -e "USE station_db; SELECT station_id, pollutant_type, value, timestamp FROM pollutant_readings ORDER BY timestamp DESC LIMIT 10;"
```

---

## Sample Data

### Create Sample Stations

The initialization script can create sample stations for testing:

```bash
docker compose exec station-service python scripts/init_tables.py
```

This creates 5 sample stations:
1. Downtown Urban Station (URBAN)
2. Industrial Zone Station (INDUSTRIAL)
3. Rural Background Station (RURAL)
4. Traffic Hotspot Station (TRAFFIC)
5. Government Monitoring Station (GOVERNMENT)

### Generate Fake Readings

```bash
# Generate fake data for sample stations
docker compose exec station-service python scripts/fake_data_generator.py
```

Or via API:
```bash
# Create sample stations via API
curl -X POST http://localhost:8007/api/v1/stations \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Station",
    "station_code": "TEST-001",
    "station_type": "URBAN",
    "latitude": 21.0285,
    "longitude": 105.8542
  }'

# Submit readings
curl -X POST http://localhost:8007/api/v1/stations/{station_id}/record-readings \
  -H "Content-Type: application/json" \
  -d '{
    "readings": {
      "PM25": 35.5,
      "PM10": 50.0,
      "SO2": 10.0,
      "NOX": 40.0,
      "CO": 5.2
    },
    "source": "MANUAL"
  }'
```

---

## Database Schema

### stations Table

| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR(36) | Primary key (UUID) |
| station_code | VARCHAR(100) | Unique external identifier |
| name | VARCHAR(255) | Station name |
| station_type | VARCHAR(50) | URBAN, RURAL, INDUSTRIAL, etc. |
| latitude | FLOAT | GPS latitude |
| longitude | FLOAT | GPS longitude |
| altitude | FLOAT | Optional altitude |
| is_active | BOOLEAN | Active status |
| api_config | JSON | API configuration |
| data_retention_days | INT | Data retention period |
| metadata | JSON | Additional metadata |
| created_at | DATETIME | Creation timestamp |
| updated_at | DATETIME | Last update timestamp |
| last_data_received | DATETIME | Last data reception time |

### pollutant_readings Table

| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR(36) | Primary key (UUID) |
| station_id | VARCHAR(36) | Foreign key to stations |
| pollutant_type | VARCHAR(20) | SO2, NOX, PM25, etc. |
| value | FLOAT | Measured value |
| unit | VARCHAR(20) | Unit of measurement |
| quality_flag | VARCHAR(20) | GOOD, SUSPECT, BAD |
| timestamp | DATETIME | Measurement time |
| created_at | DATETIME | Record creation time |

---

## Data Retention

The station service implements automatic data retention:

- **Default retention**: 1 day (as per requirements)
- **Configurable**: Via `data_retention_days` per station
- **Cleanup**: Old readings are deleted automatically

### Configure Retention

```bash
# Update station retention
curl -X PUT http://localhost:8007/api/v1/stations/{station_id} \
  -H "Content-Type: application/json" \
  -d '{
    "data_retention_days": 7
  }'
```

---

## Troubleshooting

### Tables Not Created

1. **Check service logs**:
   ```bash
   docker compose logs station-service
   ```

2. **Verify database exists**:
   ```bash
   docker exec -it aqms-mysql mysql -u root -pMysql_2026 -e "SHOW DATABASES LIKE 'station_db';"
   ```

3. **Check MySQL connection**:
   ```bash
   docker compose exec station-service env | grep DATABASE
   ```

4. **Manually create tables**:
   ```bash
   docker compose exec station-service python scripts/init_tables.py
   ```

### Connection Issues

```bash
# Test database connection
docker compose exec station-service python -c "
from src.config import settings
from src.infrastructure.persistence.database import get_engine
engine = get_engine()
print('Database URL:', settings.DATABASE_URL)
print('Connection test:', engine.url)
"
```

### Reset Database

```bash
# Drop and recreate database
docker exec -it aqms-mysql mysql -u root -pMysql_2026 << EOF
DROP DATABASE IF EXISTS station_db;
CREATE DATABASE station_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EOF

# Restart service to recreate tables
docker compose restart station-service
```

---

## Migration Management

For schema changes, use Alembic:

```bash
# Generate migration
docker compose exec station-service alembic revision --autogenerate -m "Description"

# Apply migration
docker compose exec station-service alembic upgrade head

# Rollback
docker compose exec station-service alembic downgrade -1
```

---

## Performance Optimization

### Indexes

The tables include optimized indexes:
- `idx_station_code`: Fast station lookup by code
- `idx_station_location`: Geographic queries
- `idx_station_time`: Time-series queries
- `idx_time_pollutant`: Pollutant-specific time queries

### Partitioning (Future)

For large datasets, consider partitioning `pollutant_readings` by timestamp:

```sql
ALTER TABLE pollutant_readings
PARTITION BY RANGE (TO_DAYS(timestamp)) (
    PARTITION p0 VALUES LESS THAN (TO_DAYS('2024-01-01')),
    PARTITION p1 VALUES LESS THAN (TO_DAYS('2024-02-01')),
    ...
);
```

---

## Backup & Restore

### Backup

```bash
# Backup station_db
docker exec aqms-mysql mysqldump -u root -pMysql_2026 station_db > station_db_backup.sql
```

### Restore

```bash
# Restore from backup
docker exec -i aqms-mysql mysql -u root -pMysql_2026 station_db < station_db_backup.sql
```

---

## Monitoring

### Table Sizes

```bash
docker exec -it aqms-mysql mysql -u root -pMysql_2026 -e "
USE station_db;
SELECT 
    table_name,
    table_rows,
    ROUND((data_length + index_length) / 1024 / 1024, 2) AS size_mb
FROM information_schema.tables
WHERE table_schema = 'station_db';
"
```

### Recent Activity

```bash
docker exec -it aqms-mysql mysql -u root -pMysql_2026 -e "
USE station_db;
SELECT 
    DATE(timestamp) AS date,
    COUNT(*) AS readings_count,
    COUNT(DISTINCT station_id) AS stations_active
FROM pollutant_readings
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY DATE(timestamp)
ORDER BY date DESC;
"
```

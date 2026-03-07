# Database Initialization Summary

## What Happens on Docker Deployment

When you run `docker compose up -d`, the following database initialization occurs automatically:

### 1. MySQL Container Startup

**File**: `scripts/init-mysql.sql`

This script runs automatically when MySQL container starts for the first time:

```sql
CREATE DATABASE IF NOT EXISTS station_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
```

**Result**: Creates the `station_db` database with UTF-8 encoding.

---

### 2. Station Service Startup

**File**: `services/station-service/src/interfaces/api/routes.py`

The FastAPI lifespan event triggers table creation:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database (creates tables automatically)
    await init_database()
```

**What it does**:
- Connects to `station_db` database
- Creates `stations` table
- Creates `pollutant_readings` table
- Sets up indexes for performance

**Logs you'll see**:
```
INFO | Starting station-service...
INFO | Database tables created/verified
INFO | Station service started successfully
```

---

## Tables Created

### stations Table

Stores air quality monitoring station metadata:

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

**Indexes**:
- `PRIMARY KEY (id)` - Fast UUID lookups
- `UNIQUE KEY (station_code)` - Unique external codes
- `INDEX (is_active)` - Filter by status
- `INDEX (latitude, longitude)` - Geographic queries

---

### pollutant_readings Table

Stores time-series air quality measurements:

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
    FOREIGN KEY (station_id) REFERENCES stations(id) ON DELETE CASCADE
);
```

**Indexes**:
- `PRIMARY KEY (id)` - Fast UUID lookups
- `FOREIGN KEY (station_id)` - Links to stations
- `INDEX (station_id, timestamp)` - Station time-series
- `INDEX (timestamp, pollutant_type)` - Time-based queries
- `UNIQUE (station_id, timestamp, pollutant_type)` - Prevent duplicates

---

## Verification Steps

### 1. Check Databases

```bash
docker exec aqms-mysql mysql -u root -pMysql_2026 -e "SHOW DATABASES;"
```

**Expected Output**:
```
Database
factory_db
sensor_db
alert_db
user_db
remote_sensing_db
station_db
```

### 2. Check Tables

```bash
docker exec aqms-mysql mysql -u root -pMysql_2026 -e "USE station_db; SHOW TABLES;"
```

**Expected Output**:
```
Tables_in_station_db
pollutant_readings
stations
```

### 3. Check Table Structure

```bash
docker exec aqms-mysql mysql -u root -pMysql_2026 -e "USE station_db; DESCRIBE stations;"
```

**Expected Output**:
```
Field                   Type        Null    Key     Default
id                      varchar(36) NO      PRI     NULL
station_code            varchar(100)NO      UNI     NULL
name                    varchar(255)NO              NULL
station_type            varchar(50) NO              NULL
latitude                float       NO              NULL
longitude               float       NO              NULL
altitude                float       YES             NULL
is_active               tinyint(1)  NO              0
api_config              json        YES             NULL
data_retention_days     int         NO              1
metadata                json        YES             NULL
created_at              datetime    NO              NULL
updated_at              datetime    NO              NULL
last_data_received      datetime    YES             NULL
```

---

## Manual Initialization (If Needed)

If tables are not created automatically:

### Option 1: Run Init Script

```bash
docker compose exec station-service python scripts/init_tables.py
```

### Option 2: Restart Service

```bash
docker compose restart station-service
docker compose logs -f station-service
```

### Option 3: Direct SQL

```bash
docker exec -it aqms-mysql mysql -u root -pMysql_2026 << 'EOF'
USE station_db;

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
    last_data_received DATETIME
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS pollutant_readings (
    id VARCHAR(36) PRIMARY KEY,
    station_id VARCHAR(36) NOT NULL,
    pollutant_type VARCHAR(20) NOT NULL,
    value FLOAT NOT NULL,
    unit VARCHAR(20) DEFAULT 'µg/m³',
    quality_flag VARCHAR(20),
    timestamp DATETIME NOT NULL,
    created_at DATETIME,
    FOREIGN KEY (station_id) REFERENCES stations(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
EOF
```

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Docker Compose starts MySQL container                    │
│    ↓                                                         │
│ 2. init-mysql.sql runs → creates station_db                 │
│    ↓                                                         │
│ 3. Docker Compose starts station-service                    │
│    ↓                                                         │
│ 4. FastAPI lifespan event → init_database()                 │
│    ↓                                                         │
│ 5. SQLAlchemy creates tables (stations, pollutant_readings) │
│    ↓                                                         │
│ 6. Service ready to accept requests                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Problem: "Table doesn't exist"

**Solution**:
```bash
# Check service logs
docker compose logs station-service | grep -i "database"

# Manually initialize
docker compose exec station-service python scripts/init_tables.py
```

### Problem: "Database doesn't exist"

**Solution**:
```bash
# Create database manually
docker exec -it aqms-mysql mysql -u root -pMysql_2026 -e "CREATE DATABASE IF NOT EXISTS station_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Restart service
docker compose restart station-service
```

### Problem: "Connection refused"

**Solution**:
```bash
# Check MySQL is healthy
docker compose ps mysql

# Check service can connect
docker compose exec station-service python -c "
from src.config import settings
print('DB URL:', settings.DATABASE_URL)
"
```

---

## Complete Deployment Checklist

- [ ] MySQL container is running and healthy
- [ ] `station_db` database exists
- [ ] `stations` table exists with correct structure
- [ ] `pollutant_readings` table exists with correct structure
- [ ] Station service is running and healthy
- [ ] Service logs show "Database tables created/verified"
- [ ] Can access http://localhost:8007/health
- [ ] Can access http://localhost:8007/docs

---

## Related Documentation

- Full implementation: `documents/STATION_SERVICE_IMPLEMENTATION.md`
- Quick start guide: `documents/QUICKSTART_STATION_PURPLEAIR.md`
- Database details: `documents/DATABASE_INIT_STATION_SERVICE.md`
- Main deployment: `DEPLOYMENT.md`

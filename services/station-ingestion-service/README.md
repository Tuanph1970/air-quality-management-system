# Station Ingestion Service

Service for ingesting environmental monitoring station data from external APIs.

## Features

- Fetches station list from external API (admin-qttd.tedp.vn)
- Fetches hourly AQI data for all stations
- Stores data in local MySQL database
- Provides REST API for frontend consumption
- Automatic data synchronization every 5 minutes

## Quick Start

```bash
# Start the service
docker-compose up -d station-ingestion-service

# View logs
docker-compose logs -f station-ingestion-service

# Test health endpoint
curl http://localhost:8010/api/v1/health
```

## Documentation

See [documents/STATION_INGESTION_SERVICE.md](../../documents/STATION_INGESTION_SERVICE.md) for full documentation.

## API Endpoints

- `GET /api/v1/stations` - Get all stations
- `GET /api/v1/stations/:code` - Get station by code
- `GET /api/v1/stations/:code/readings` - Get station readings
- `GET /api/v1/readings/timeseries` - Get all stations time series
- `POST /api/v1/sync/stations` - Sync stations
- `POST /api/v1/sync/aqi` - Sync AQI data

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8008 | Service port |
| `DATABASE_URL` | - | MySQL connection URL |
| `STATION_API_BASE_URL` | https://admin-qttd.tedp.vn/api/partner/v1 | External API URL |
| `STATION_API_KEY` | c9e03048-... | External API key |
| `FETCH_INTERVAL_SECONDS` | 300 | Data fetch interval |

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python scripts/init_db.py

# Run service
python main.py

# Run data fetcher
python scripts/data_fetcher.py
```

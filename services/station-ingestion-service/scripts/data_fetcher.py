"""Scheduler for periodic data fetching."""
import asyncio
import logging
from datetime import datetime

from src.core.config import config
from src.infrastructure.external.station_api_client import StationAPIClient
from src.infrastructure.persistence.models import get_session
from src.infrastructure.persistence.station_repository_impl import StationRepositoryImpl
from src.application.station_ingestion_service import StationIngestionService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def run_scheduler():
    """Run the data fetching scheduler."""
    logger.info("Starting data fetch scheduler...")
    logger.info(f"Fetch interval: {config.FETCH_INTERVAL_SECONDS} seconds")

    # Initialize service
    session = get_session(config.DATABASE_URL)
    repository = StationRepositoryImpl(session)
    api_client = StationAPIClient()
    service = StationIngestionService(repository, api_client)

    iteration = 0

    while True:
        try:
            iteration += 1
            logger.info(f"=== Fetch cycle {iteration} ===")

            # Sync stations (first time only or periodically)
            if iteration == 1:
                logger.info("Initial station sync...")
                total, new = await service.sync_stations()
                logger.info(f"Stations: {total} total, {new} new")

            # Sync AQI data
            logger.info("Syncing AQI data...")
            count = await service.sync_aqi_data()
            logger.info(f"Synced {count} readings")

            logger.info(f"Cycle {iteration} completed. Next cycle in {config.FETCH_INTERVAL_SECONDS}s")

        except Exception as e:
            logger.error(f"Error in fetch cycle: {e}", exc_info=True)

        await asyncio.sleep(config.FETCH_INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        asyncio.run(run_scheduler())
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")

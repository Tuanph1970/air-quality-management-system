"""Initialize database tables for station ingestion service."""
import logging

from src.core.config import config
from src.infrastructure.persistence.models import create_tables

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Initializing database tables...")
    logger.info(f"Database URL: {config.DATABASE_URL}")

    try:
        create_tables(config.DATABASE_URL)
        logger.info("Database tables created successfully!")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise

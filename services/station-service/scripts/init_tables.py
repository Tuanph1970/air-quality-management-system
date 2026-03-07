"""Database initialization script for station service.

This script creates all necessary tables for the station service.
It runs automatically on service startup via the lifespan event.

Usage:
    python scripts/init_tables.py
"""
from __future__ import annotations

import asyncio
import logging
import sys

# Add parent directory to path
sys.path.insert(0, '.')

from src.infrastructure.persistence.database import (
    Base,
    get_engine,
    init_database,
)
from src.infrastructure.persistence.models import StationModel, PollutantReadingModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def create_tables():
    """Create database tables."""
    logger.info("Starting database initialization...")
    
    try:
        # Initialize database (creates tables)
        await init_database()
        logger.info("✓ Database tables created successfully")
        
        # Verify tables exist
        engine = get_engine()
        async with engine.begin() as conn:
            from sqlalchemy import text
            
            # Check stations table
            result = await conn.execute(
                text("SHOW TABLES LIKE 'stations'")
            )
            if result.fetchone():
                logger.info("✓ stations table exists")
            else:
                logger.error("✗ stations table not found")
            
            # Check pollutant_readings table
            result = await conn.execute(
                text("SHOW TABLES LIKE 'pollutant_readings'")
            )
            if result.fetchone():
                logger.info("✓ pollutant_readings table exists")
            else:
                logger.error("✗ pollutant_readings table not found")
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        raise


async def create_sample_stations():
    """Create sample stations for testing."""
    logger.info("Creating sample stations...")
    
    from src.config import settings
    from src.infrastructure.persistence.database import get_db_session
    from src.infrastructure.persistence.models import StationModel
    from sqlalchemy import select, text
    from datetime import datetime
    
    sample_stations = [
        {
            "station_code": "SAMPLE-URBAN-001",
            "name": "Downtown Urban Station",
            "station_type": "URBAN",
            "latitude": 21.0285,
            "longitude": 105.8542,
            "is_active": True,
        },
        {
            "station_code": "SAMPLE-IND-001",
            "name": "Industrial Zone Station",
            "station_type": "INDUSTRIAL",
            "latitude": 21.0500,
            "longitude": 105.9000,
            "is_active": True,
        },
        {
            "station_code": "SAMPLE-RURAL-001",
            "name": "Rural Background Station",
            "station_type": "RURAL",
            "latitude": 20.9500,
            "longitude": 105.7500,
            "is_active": True,
        },
        {
            "station_code": "SAMPLE-TRAFFIC-001",
            "name": "Traffic Hotspot Station",
            "station_type": "TRAFFIC",
            "latitude": 21.0350,
            "longitude": 105.8400,
            "is_active": True,
        },
        {
            "station_code": "SAMPLE-GOV-001",
            "name": "Government Monitoring Station",
            "station_type": "GOVERNMENT",
            "latitude": 21.0200,
            "longitude": 105.8600,
            "is_active": True,
        },
    ]
    
    try:
        async with get_db_session() as session:
            for station_data in sample_stations:
                # Check if station already exists
                result = await session.execute(
                    select(StationModel.id).where(
                        StationModel.station_code == station_data['station_code']
                    )
                )
                if not result.fetchone():
                    # Insert station
                    station = StationModel(
                        station_code=station_data["station_code"],
                        name=station_data["name"],
                        station_type=station_data["station_type"],
                        latitude=station_data["latitude"],
                        longitude=station_data["longitude"],
                        is_active=station_data["is_active"],
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                    session.add(station)
                    logger.info(f"  Created sample station: {station_data['name']}")
            
            await session.commit()
            logger.info("✓ Sample stations created successfully")
            
    except Exception as e:
        logger.error(f"Failed to create sample stations: {e}", exc_info=True)


async def main():
    """Main initialization function."""
    logger.info("=" * 60)
    logger.info("Station Service Database Initialization")
    logger.info("=" * 60)
    
    # Create tables
    await create_tables()
    
    # Create sample stations (optional, for demo)
    from src.config import settings
    if settings.USE_FAKE_DATA or settings.DEBUG:
        await create_sample_stations()
    
    logger.info("=" * 60)
    logger.info("Initialization Complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

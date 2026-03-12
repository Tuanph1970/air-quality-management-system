"""SQLAlchemy implementation of station repository."""
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.entities.station import AirQualityReading, Station
from src.domain.repositories.station_repository import StationRepository
from src.infrastructure.persistence.models import AirQualityReadingModel, StationModel

logger = logging.getLogger(__name__)


class StationRepositoryImpl(StationRepository):
    """SQLAlchemy implementation of StationRepository."""

    def __init__(self, session: Session):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    async def get_all_stations(self) -> List[Station]:
        """Get all stations."""
        stmt = select(StationModel)
        models = self.session.execute(stmt).scalars().all()

        return [self._to_entity(model) for model in models]

    async def get_station_by_code(self, station_code: str) -> Optional[Station]:
        """Get station by station code."""
        stmt = select(StationModel).where(StationModel.station_code == station_code)
        model = self.session.execute(stmt).scalar_one_or_none()

        if model:
            return self._to_entity(model)
        return None

    async def save_station(self, station: Station) -> Station:
        """Save or update a station."""
        # Check if exists
        existing = await self.get_station_by_code(station.station_code)

        if existing:
            # Update
            stmt = select(StationModel).where(StationModel.station_code == station.station_code)
            model = self.session.execute(stmt).scalar_one_or_none()
            if model:
                model.station_name = station.station_name
                model.address = station.address
                model.latitude = station.latitude
                model.longitude = station.longitude
                model.station_type = station.station_type
                model.province_id = station.province_id
                model.is_active = station.is_active
                model.station_metadata = station.metadata
                model.updated_at = datetime.utcnow()
        else:
            # Insert
            model = StationModel(
                id=station.id,
                station_code=station.station_code,
                station_name=station.station_name,
                address=station.address,
                latitude=station.latitude,
                longitude=station.longitude,
                station_type=station.station_type,
                province_id=station.province_id,
                is_active=station.is_active,
                station_metadata=station.metadata,
            )
            self.session.add(model)

        self.session.commit()
        self.session.refresh(model)

        return self._to_entity(model)

    async def save_stations(self, stations: List[Station]) -> List[Station]:
        """Save or update multiple stations."""
        saved = []
        for station in stations:
            saved_station = await self.save_station(station)
            saved.append(saved_station)
        return saved

    async def get_readings_by_station(
        self,
        station_code: str,
        from_time: datetime,
        to_time: datetime,
    ) -> List[AirQualityReading]:
        """Get readings for a station within time range."""
        stmt = select(AirQualityReadingModel).where(
            AirQualityReadingModel.station_code == station_code,
            AirQualityReadingModel.reading_time >= from_time,
            AirQualityReadingModel.reading_time <= to_time,
        )
        models = self.session.execute(stmt).scalars().all()

        return [self._reading_to_entity(model) for model in models]

    async def get_readings_all_stations(
        self,
        from_time: datetime,
        to_time: datetime,
    ) -> List[AirQualityReading]:
        """Get readings for all stations within time range."""
        stmt = select(AirQualityReadingModel).where(
            AirQualityReadingModel.reading_time >= from_time,
            AirQualityReadingModel.reading_time <= to_time,
        )
        models = self.session.execute(stmt).scalars().all()

        return [self._reading_to_entity(model) for model in models]

    async def save_readings(self, readings: List[AirQualityReading]) -> List[AirQualityReading]:
        """Save multiple readings."""
        if not readings:
            return []

        saved = []
        for reading in readings:
            model = AirQualityReadingModel(
                id=reading.id,
                station_code=reading.station_code,
                reading_time=reading.reading_time,
                aqi=reading.aqi,
                pm25=reading.pm25,
                pm10=reading.pm10,
                co=reading.co,
                so2=reading.so2,
                no2=reading.no2,
                o3=reading.o3,
                temperature=reading.temperature,
                humidity=reading.humidity,
            )
            self.session.add(model)
            saved.append(reading)

        self.session.commit()
        logger.info(f"Saved {len(saved)} readings")

        return saved

    def _to_entity(self, model: StationModel) -> Station:
        """Convert database model to entity."""
        return Station(
            id=model.id,
            station_code=model.station_code,
            station_name=model.station_name,
            address=model.address,
            latitude=model.latitude,
            longitude=model.longitude,
            station_type=model.station_type,
            province_id=model.province_id,
            is_active=model.is_active,
            metadata=model.station_metadata or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _reading_to_entity(self, model: AirQualityReadingModel) -> AirQualityReading:
        """Convert database model to entity."""
        return AirQualityReading(
            id=model.id,
            station_code=model.station_code,
            reading_time=model.reading_time,
            aqi=model.aqi,
            pm25=model.pm25,
            pm10=model.pm10,
            co=model.co,
            so2=model.so2,
            no2=model.no2,
            o3=model.o3,
            temperature=model.temperature,
            humidity=model.humidity,
        )

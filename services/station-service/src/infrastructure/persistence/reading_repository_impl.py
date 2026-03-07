"""SQLAlchemy implementation of ReadingRepository."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.entities.pollutant_reading import PollutantReading, StationReadingBatch
from ...domain.repositories.reading_repository import ReadingRepository
from ...domain.value_objects.pollutant_type import PollutantType
from .models import PollutantReadingModel

logger = logging.getLogger(__name__)


class SQLAlchemyReadingRepository(ReadingRepository):
    """SQLAlchemy implementation of ReadingRepository."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.
        
        Args:
            session: AsyncSession instance
        """
        self.session = session
    
    def _to_entity(self, model: PollutantReadingModel) -> PollutantReading:
        """Convert SQLAlchemy model to domain entity."""
        return PollutantReading(
            id=UUID(model.id),
            station_id=UUID(model.station_id),
            pollutant_type=PollutantType.from_string(model.pollutant_type),
            value=model.value,
            unit=model.unit,
            quality_flag=model.quality_flag,
            timestamp=model.timestamp,
            created_at=model.created_at,
        )
    
    def _to_model(self, entity: PollutantReading) -> PollutantReadingModel:
        """Convert domain entity to SQLAlchemy model."""
        return PollutantReadingModel(
            id=str(entity.id),
            station_id=str(entity.station_id),
            pollutant_type=entity.pollutant_type.value,
            value=entity.value,
            unit=entity.unit,
            quality_flag=entity.quality_flag,
            timestamp=entity.timestamp,
            created_at=entity.created_at,
        )
    
    async def save_reading(self, reading: PollutantReading) -> PollutantReading:
        """Save a single pollutant reading."""
        model = self._to_model(reading)
        self.session.add(model)
        await self.session.flush()
        return reading
    
    async def save_batch(self, batch: StationReadingBatch) -> StationReadingBatch:
        """Save a batch of readings."""
        for reading in batch.readings.values():
            model = self._to_model(reading)
            self.session.add(model)
        
        await self.session.flush()
        logger.debug(f"Saved batch of {len(batch.readings)} readings")
        return batch
    
    async def get_by_station_id(
        self,
        station_id: UUID,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        pollutant_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PollutantReading]:
        """Get readings for a station."""
        query = select(PollutantReadingModel).where(
            PollutantReadingModel.station_id == str(station_id)
        )
        
        if start_time:
            query = query.where(PollutantReadingModel.timestamp >= start_time)
        if end_time:
            query = query.where(PollutantReadingModel.timestamp <= end_time)
        if pollutant_type:
            query = query.where(PollutantReadingModel.pollutant_type == pollutant_type.upper())
        
        query = query.order_by(PollutantReadingModel.timestamp.desc()).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]
    
    async def get_latest_by_station(
        self,
        station_id: UUID,
        pollutant_types: Optional[List[str]] = None,
    ) -> Dict[str, PollutantReading]:
        """Get the latest reading for each pollutant type."""
        query = select(PollutantReadingModel).where(
            PollutantReadingModel.station_id == str(station_id)
        )
        
        if pollutant_types:
            query = query.where(
                PollutantReadingModel.pollutant_type.in_([pt.upper() for pt in pollutant_types])
            )
        
        # Order by timestamp desc and get results
        query = query.order_by(PollutantReadingModel.timestamp.desc())
        
        result = await self.session.execute(query)
        models = result.scalars().all()
        
        # Get latest for each pollutant type
        latest: Dict[str, PollutantReading] = {}
        for model in models:
            pt = model.pollutant_type
            if pt not in latest:
                latest[pt] = self._to_entity(model)
        
        return latest
    
    async def get_readings_in_timerange(
        self,
        station_ids: List[UUID],
        start_time: datetime,
        end_time: datetime,
        pollutant_types: Optional[List[str]] = None,
    ) -> List[StationReadingBatch]:
        """Get readings grouped by timestamp for multiple stations."""
        query = select(PollutantReadingModel).where(
            PollutantReadingModel.station_id.in_([str(sid) for sid in station_ids]),
            PollutantReadingModel.timestamp >= start_time,
            PollutantReadingModel.timestamp <= end_time,
        )
        
        if pollutant_types:
            query = query.where(
                PollutantReadingModel.pollutant_type.in_([pt.upper() for pt in pollutant_types])
            )
        
        query = query.order_by(PollutantReadingModel.timestamp.desc())
        
        result = await self.session.execute(query)
        models = result.scalars().all()
        
        # Group by station and timestamp
        batches: Dict[tuple, StationReadingBatch] = {}
        for model in models:
            key = (model.station_id, model.timestamp)
            if key not in batches:
                batches[key] = StationReadingBatch(
                    station_id=UUID(model.station_id),
                    timestamp=model.timestamp,
                )
            
            reading = self._to_entity(model)
            batches[key].add_reading(reading)
        
        return list(batches.values())
    
    async def delete_old_readings(self, older_than: datetime) -> int:
        """Delete readings older than specified timestamp."""
        stmt = delete(PollutantReadingModel).where(
            PollutantReadingModel.timestamp < older_than
        )
        
        result = await self.session.execute(stmt)
        await self.session.flush()
        
        deleted = result.rowcount
        logger.info(f"Deleted {deleted} readings older than {older_than}")
        return deleted

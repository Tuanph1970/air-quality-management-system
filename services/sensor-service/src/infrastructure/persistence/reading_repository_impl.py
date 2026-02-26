"""SQLAlchemy implementation of the ``ReadingRepository`` port.

Optimised for TimescaleDB time-series queries.  Uses efficient batch
inserts and time-bucketed aggregation where possible.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.entities.reading import Reading
from ...domain.repositories.reading_repository import ReadingRepository
from .models import ReadingModel

logger = logging.getLogger(__name__)


class SQLAlchemyReadingRepository(ReadingRepository):
    """Concrete repository for readings backed by TimescaleDB.

    Each public method operates within the session that was injected at
    construction time.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------
    async def save(self, reading: Reading) -> Reading:
        """Persist a single reading."""
        model = self._to_model(reading)
        merged = await self._session.merge(model)
        await self._session.flush()
        await self._session.refresh(merged)

        logger.debug("Saved reading %s for sensor %s", merged.id, merged.sensor_id)
        return self._to_entity(merged)

    async def save_batch(self, readings: List[Reading]) -> int:
        """Persist multiple readings in a single operation.

        Uses ``add_all`` for efficient batch insertion.
        Returns the number of readings saved.
        """
        if not readings:
            return 0

        models = [self._to_model(r) for r in readings]
        self._session.add_all(models)
        await self._session.flush()

        logger.debug("Batch saved %d readings", len(models))
        return len(models)

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------
    async def get_readings(
        self,
        sensor_id: UUID,
        start: datetime,
        end: datetime,
        limit: int = 1000,
    ) -> List[Reading]:
        """Return readings for a sensor within a time range.

        Ordered by timestamp descending (most recent first).
        """
        stmt = (
            select(ReadingModel)
            .where(
                ReadingModel.sensor_id == sensor_id,
                ReadingModel.timestamp >= start,
                ReadingModel.timestamp <= end,
            )
            .order_by(ReadingModel.timestamp.desc())
            .limit(limit)
        )

        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def get_latest(self, sensor_id: UUID) -> Optional[Reading]:
        """Return the most recent reading for a sensor."""
        stmt = (
            select(ReadingModel)
            .where(ReadingModel.sensor_id == sensor_id)
            .order_by(ReadingModel.timestamp.desc())
            .limit(1)
        )

        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_latest_by_factory(self, factory_id: UUID) -> Optional[Reading]:
        """Return the most recent reading from any sensor at a factory."""
        stmt = (
            select(ReadingModel)
            .where(ReadingModel.factory_id == factory_id)
            .order_by(ReadingModel.timestamp.desc())
            .limit(1)
        )

        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_average(
        self,
        sensor_id: UUID,
        start: datetime,
        end: datetime,
    ) -> Optional[Reading]:
        """Return averaged pollutant readings over a time range.

        Aggregates using SQL AVG() for efficient server-side computation.
        Returns a synthetic ``Reading`` entity with averaged values.
        """
        stmt = (
            select(
                func.avg(ReadingModel.pm25).label("pm25"),
                func.avg(ReadingModel.pm10).label("pm10"),
                func.avg(ReadingModel.co).label("co"),
                func.avg(ReadingModel.co2).label("co2"),
                func.avg(ReadingModel.no2).label("no2"),
                func.avg(ReadingModel.nox).label("nox"),
                func.avg(ReadingModel.so2).label("so2"),
                func.avg(ReadingModel.o3).label("o3"),
                func.avg(ReadingModel.temperature).label("temperature"),
                func.avg(ReadingModel.humidity).label("humidity"),
                func.avg(ReadingModel.aqi).label("aqi"),
                func.count().label("count"),
            )
            .where(
                ReadingModel.sensor_id == sensor_id,
                ReadingModel.timestamp >= start,
                ReadingModel.timestamp <= end,
            )
        )

        result = await self._session.execute(stmt)
        row = result.one_or_none()

        if row is None or row.count == 0:
            return None

        return Reading(
            id=uuid4(),
            sensor_id=sensor_id,
            pm25=float(row.pm25 or 0.0),
            pm10=float(row.pm10 or 0.0),
            co=float(row.co or 0.0),
            co2=float(row.co2 or 0.0),
            no2=float(row.no2 or 0.0),
            nox=float(row.nox or 0.0),
            so2=float(row.so2 or 0.0),
            o3=float(row.o3 or 0.0),
            temperature=float(row.temperature or 0.0),
            humidity=float(row.humidity or 0.0),
            aqi=round(float(row.aqi or 0)),
            timestamp=end,
        )

    async def count(
        self,
        sensor_id: Optional[UUID] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> int:
        """Return the number of readings, optionally filtered."""
        stmt = select(func.count()).select_from(ReadingModel)
        if sensor_id:
            stmt = stmt.where(ReadingModel.sensor_id == sensor_id)
        if start:
            stmt = stmt.where(ReadingModel.timestamp >= start)
        if end:
            stmt = stmt.where(ReadingModel.timestamp <= end)

        result = await self._session.execute(stmt)
        return result.scalar_one()

    # ------------------------------------------------------------------
    # Mapping: ORM model <-> domain entity
    # ------------------------------------------------------------------
    @staticmethod
    def _to_entity(model: ReadingModel) -> Reading:
        """Map a SQLAlchemy ``ReadingModel`` row to a domain ``Reading``."""
        return Reading(
            id=model.id,
            sensor_id=model.sensor_id,
            factory_id=model.factory_id,
            pm25=model.pm25,
            pm10=model.pm10,
            co=model.co,
            co2=model.co2,
            no2=model.no2,
            nox=model.nox,
            so2=model.so2,
            o3=model.o3,
            temperature=model.temperature,
            humidity=model.humidity,
            aqi=model.aqi,
            timestamp=model.timestamp,
        )

    @staticmethod
    def _to_model(entity: Reading) -> ReadingModel:
        """Map a domain ``Reading`` entity to a SQLAlchemy ``ReadingModel``."""
        return ReadingModel(
            id=entity.id,
            sensor_id=entity.sensor_id,
            factory_id=entity.factory_id,
            pm25=entity.pm25,
            pm10=entity.pm10,
            co=entity.co,
            co2=entity.co2,
            no2=entity.no2,
            nox=entity.nox,
            so2=entity.so2,
            o3=entity.o3,
            temperature=entity.temperature,
            humidity=entity.humidity,
            aqi=entity.aqi,
            timestamp=entity.timestamp,
        )

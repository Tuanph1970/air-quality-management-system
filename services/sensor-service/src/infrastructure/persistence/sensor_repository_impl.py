"""SQLAlchemy implementation of the ``SensorRepository`` port.

This is the *adapter* in hexagonal architecture — it translates between
the domain's ``Sensor`` entity and the relational ``SensorModel``.
"""
from __future__ import annotations

import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.entities.sensor import Sensor
from ...domain.repositories.sensor_repository import SensorRepository
from ...domain.value_objects.calibration_params import CalibrationParams
from ...domain.value_objects.sensor_status import SensorStatus
from ...domain.value_objects.sensor_type import SensorType
from .models import SensorModel

logger = logging.getLogger(__name__)


class SQLAlchemySensorRepository(SensorRepository):
    """Concrete repository backed by PostgreSQL via SQLAlchemy async.

    Each public method operates within the session that was injected at
    construction time.  The caller (application service) is responsible
    for committing or rolling back the session.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------
    async def get_by_id(self, sensor_id: UUID) -> Optional[Sensor]:
        stmt = select(SensorModel).where(SensorModel.id == sensor_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_serial_number(self, serial_number: str) -> Optional[Sensor]:
        stmt = select(SensorModel).where(
            SensorModel.serial_number == serial_number,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_by_factory(
        self,
        factory_id: UUID,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Sensor]:
        stmt = select(SensorModel).where(SensorModel.factory_id == factory_id)
        if status:
            stmt = stmt.where(SensorModel.status == status)
        stmt = stmt.order_by(SensorModel.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)

        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_all(
        self,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Sensor]:
        stmt = select(SensorModel)
        if status:
            stmt = stmt.where(SensorModel.status == status)
        stmt = stmt.order_by(SensorModel.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)

        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count(
        self,
        factory_id: Optional[UUID] = None,
        status: Optional[str] = None,
    ) -> int:
        stmt = select(func.count()).select_from(SensorModel)
        if factory_id:
            stmt = stmt.where(SensorModel.factory_id == factory_id)
        if status:
            stmt = stmt.where(SensorModel.status == status)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------
    async def save(self, sensor: Sensor) -> Sensor:
        """Persist a sensor (insert or update).

        Uses ``merge`` so both new and detached entities are handled
        transparently.  The session is flushed to ensure the model
        receives any server-generated defaults before mapping back.
        """
        model = self._to_model(sensor)
        merged = await self._session.merge(model)
        await self._session.flush()
        await self._session.refresh(merged)

        logger.debug("Saved sensor %s", merged.id)
        return self._to_entity(merged)

    async def delete(self, sensor_id: UUID) -> bool:
        stmt = delete(SensorModel).where(SensorModel.id == sensor_id)
        result = await self._session.execute(stmt)
        await self._session.flush()
        deleted = result.rowcount > 0
        if deleted:
            logger.debug("Deleted sensor %s", sensor_id)
        return deleted

    # ------------------------------------------------------------------
    # Mapping: ORM model <-> domain entity
    # ------------------------------------------------------------------
    @staticmethod
    def _to_entity(model: SensorModel) -> Sensor:
        """Map a SQLAlchemy ``SensorModel`` row to a domain ``Sensor``."""
        cal = (
            CalibrationParams.from_dict(model.calibration_params)
            if model.calibration_params
            else CalibrationParams()
        )
        return Sensor(
            id=model.id,
            serial_number=model.serial_number,
            sensor_type=SensorType(model.sensor_type),
            model=model.model,
            factory_id=model.factory_id,
            latitude=model.latitude,
            longitude=model.longitude,
            calibration_params=cal,
            status=SensorStatus(model.status),
            installation_date=model.installation_date,
            last_calibration=model.last_calibration,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _to_model(entity: Sensor) -> SensorModel:
        """Map a domain ``Sensor`` entity to a SQLAlchemy ``SensorModel``."""
        return SensorModel(
            id=entity.id,
            serial_number=entity.serial_number,
            sensor_type=entity.sensor_type.value,
            model=entity.model,
            factory_id=entity.factory_id,
            latitude=entity.latitude,
            longitude=entity.longitude,
            calibration_params=entity.calibration_params.to_dict(),
            status=entity.status.value,
            installation_date=entity.installation_date,
            last_calibration=entity.last_calibration,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

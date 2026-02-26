"""SQLAlchemy implementation of ViolationRepository.

Maps between the ``Violation`` domain entity and the ``ViolationModel``
ORM model.  All database access is asynchronous via ``AsyncSession``.
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.entities.violation import Violation
from ...domain.repositories.violation_repository import ViolationRepository
from ...domain.value_objects.severity import Severity
from .models import ViolationModel


class SQLAlchemyViolationRepository(ViolationRepository):
    """Concrete repository backed by PostgreSQL via SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------
    async def get_by_id(self, violation_id: UUID) -> Optional[Violation]:
        result = await self.session.execute(
            select(ViolationModel).where(ViolationModel.id == violation_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_by_factory(
        self,
        factory_id: UUID,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Violation]:
        stmt = select(ViolationModel).where(
            ViolationModel.factory_id == factory_id
        )
        if status:
            stmt = stmt.where(ViolationModel.status == status)
        stmt = (
            stmt.order_by(ViolationModel.detected_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_open(
        self,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Violation]:
        stmt = (
            select(ViolationModel)
            .where(ViolationModel.status == "OPEN")
            .order_by(ViolationModel.detected_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_sensor(
        self,
        sensor_id: UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Violation]:
        stmt = (
            select(ViolationModel)
            .where(ViolationModel.sensor_id == sensor_id)
            .order_by(ViolationModel.detected_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_severity(
        self,
        severity: str,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Violation]:
        stmt = (
            select(ViolationModel)
            .where(ViolationModel.severity == severity)
            .order_by(ViolationModel.detected_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count(
        self,
        factory_id: Optional[UUID] = None,
        status: Optional[str] = None,
    ) -> int:
        stmt = select(func.count(ViolationModel.id))
        if factory_id:
            stmt = stmt.where(ViolationModel.factory_id == factory_id)
        if status:
            stmt = stmt.where(ViolationModel.status == status)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------
    async def save(self, violation: Violation) -> Violation:
        model = self._to_model(violation)
        merged = await self.session.merge(model)
        await self.session.commit()
        await self.session.refresh(merged)
        return self._to_entity(merged)

    async def delete(self, violation_id: UUID) -> bool:
        result = await self.session.execute(
            select(ViolationModel).where(ViolationModel.id == violation_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return False
        await self.session.delete(model)
        await self.session.commit()
        return True

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _to_entity(model: ViolationModel) -> Violation:
        """Map a database model to a domain entity."""
        return Violation(
            id=model.id,
            factory_id=model.factory_id,
            sensor_id=model.sensor_id,
            pollutant=model.pollutant,
            measured_value=model.measured_value,
            permitted_value=model.permitted_value,
            exceedance_percentage=model.exceedance_percentage,
            severity=Severity(model.severity),
            status=model.status,
            detected_at=model.detected_at,
            resolved_at=model.resolved_at,
            action_taken=model.action_taken,
            notes=model.notes,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _to_model(entity: Violation) -> ViolationModel:
        """Map a domain entity to a database model."""
        return ViolationModel(
            id=entity.id,
            factory_id=entity.factory_id,
            sensor_id=entity.sensor_id,
            pollutant=entity.pollutant,
            measured_value=entity.measured_value,
            permitted_value=entity.permitted_value,
            exceedance_percentage=entity.exceedance_percentage,
            severity=entity.severity.value
            if hasattr(entity.severity, "value")
            else str(entity.severity),
            status=entity.status,
            detected_at=entity.detected_at,
            resolved_at=entity.resolved_at,
            action_taken=entity.action_taken,
            notes=entity.notes,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

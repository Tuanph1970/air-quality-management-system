"""SQLAlchemy implementation of AlertConfigRepository.

Maps between the ``AlertConfig`` domain entity and the
``AlertConfigModel`` ORM model.
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.entities.alert_config import AlertConfig
from ...domain.repositories.alert_config_repository import AlertConfigRepository
from .models import AlertConfigModel


class SQLAlchemyAlertConfigRepository(AlertConfigRepository):
    """Concrete repository backed by PostgreSQL via SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------
    async def get_by_id(self, config_id: UUID) -> Optional[AlertConfig]:
        result = await self.session.execute(
            select(AlertConfigModel).where(AlertConfigModel.id == config_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_pollutant(self, pollutant: str) -> Optional[AlertConfig]:
        result = await self.session.execute(
            select(AlertConfigModel).where(
                AlertConfigModel.pollutant == pollutant,
                AlertConfigModel.is_active.is_(True),
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_active(self) -> List[AlertConfig]:
        result = await self.session.execute(
            select(AlertConfigModel)
            .where(AlertConfigModel.is_active.is_(True))
            .order_by(AlertConfigModel.pollutant)
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 20,
    ) -> List[AlertConfig]:
        stmt = (
            select(AlertConfigModel)
            .order_by(AlertConfigModel.pollutant)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------
    async def save(self, config: AlertConfig) -> AlertConfig:
        model = self._to_model(config)
        merged = await self.session.merge(model)
        await self.session.commit()
        await self.session.refresh(merged)
        return self._to_entity(merged)

    async def delete(self, config_id: UUID) -> bool:
        result = await self.session.execute(
            select(AlertConfigModel).where(AlertConfigModel.id == config_id)
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
    def _to_entity(model: AlertConfigModel) -> AlertConfig:
        """Map a database model to a domain entity."""
        return AlertConfig(
            id=model.id,
            name=model.name,
            pollutant=model.pollutant,
            warning_threshold=model.warning_threshold,
            high_threshold=model.high_threshold,
            critical_threshold=model.critical_threshold,
            duration_minutes=model.duration_minutes,
            is_active=model.is_active,
            notify_email=model.notify_email,
            notify_sms=model.notify_sms,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _to_model(entity: AlertConfig) -> AlertConfigModel:
        """Map a domain entity to a database model."""
        return AlertConfigModel(
            id=entity.id,
            name=entity.name,
            pollutant=entity.pollutant,
            warning_threshold=entity.warning_threshold,
            high_threshold=entity.high_threshold,
            critical_threshold=entity.critical_threshold,
            duration_minutes=entity.duration_minutes,
            is_active=entity.is_active,
            notify_email=entity.notify_email,
            notify_sms=entity.notify_sms,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

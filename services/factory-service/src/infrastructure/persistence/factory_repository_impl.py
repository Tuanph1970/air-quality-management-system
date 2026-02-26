"""SQLAlchemy implementation of the ``FactoryRepository`` port.

This is the *adapter* in hexagonal architecture — it translates between
the domain's ``Factory`` entity and the relational ``FactoryModel``.
"""
from __future__ import annotations

import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.entities.factory import Factory
from ...domain.repositories.factory_repository import FactoryRepository
from ...domain.value_objects.emission_limit import EmissionLimits
from ...domain.value_objects.factory_status import FactoryStatus
from ...domain.value_objects.location import Location
from .models import FactoryModel

logger = logging.getLogger(__name__)


class SQLAlchemyFactoryRepository(FactoryRepository):
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
    async def get_by_id(self, factory_id: UUID) -> Optional[Factory]:
        stmt = select(FactoryModel).where(FactoryModel.id == factory_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_registration_number(
        self, reg_number: str,
    ) -> Optional[Factory]:
        stmt = select(FactoryModel).where(
            FactoryModel.registration_number == reg_number,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_all(
        self,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Factory]:
        stmt = select(FactoryModel)
        if status:
            stmt = stmt.where(FactoryModel.status == status)
        stmt = stmt.order_by(FactoryModel.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)

        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count(self, status: Optional[str] = None) -> int:
        stmt = select(func.count()).select_from(FactoryModel)
        if status:
            stmt = stmt.where(FactoryModel.status == status)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------
    async def save(self, factory: Factory) -> Factory:
        """Persist a factory (insert or update).

        Uses ``merge`` so both new and detached entities are handled
        transparently.  The session is flushed to ensure the model
        receives any server-generated defaults before mapping back.
        """
        model = self._to_model(factory)
        merged = await self._session.merge(model)
        await self._session.flush()
        await self._session.refresh(merged)

        logger.debug("Saved factory %s", merged.id)
        return self._to_entity(merged)

    async def delete(self, factory_id: UUID) -> bool:
        stmt = delete(FactoryModel).where(FactoryModel.id == factory_id)
        result = await self._session.execute(stmt)
        await self._session.flush()
        deleted = result.rowcount > 0
        if deleted:
            logger.debug("Deleted factory %s", factory_id)
        return deleted

    # ------------------------------------------------------------------
    # Mapping: ORM model ↔ domain entity
    # ------------------------------------------------------------------
    @staticmethod
    def _to_entity(model: FactoryModel) -> Factory:
        """Map a SQLAlchemy ``FactoryModel`` row to a domain ``Factory``."""
        return Factory(
            id=model.id,
            name=model.name,
            registration_number=model.registration_number,
            industry_type=model.industry_type,
            location=Location(
                latitude=model.latitude,
                longitude=model.longitude,
            ),
            emission_limits=EmissionLimits.from_dict(model.emission_limits or {}),
            status=FactoryStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _to_model(entity: Factory) -> FactoryModel:
        """Map a domain ``Factory`` entity to a SQLAlchemy ``FactoryModel``."""
        return FactoryModel(
            id=entity.id,
            name=entity.name,
            registration_number=entity.registration_number,
            industry_type=entity.industry_type,
            latitude=entity.location.latitude,
            longitude=entity.location.longitude,
            emission_limits=entity.emission_limits.to_dict(),
            status=entity.status.value,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

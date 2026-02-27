"""SQLAlchemy implementation of UserRepository."""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.entities.user import User
from ...domain.repositories.user_repository import UserRepository
from ...domain.value_objects.email import Email
from ...domain.value_objects.role import Role
from .models import UserModel


class SQLAlchemyUserRepository(UserRepository):
    """Concrete repository backed by PostgreSQL via SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(
            select(UserModel).where(UserModel.email == email.lower().strip())
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 20,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[User]:
        stmt = select(UserModel)
        if role:
            stmt = stmt.where(UserModel.role == role.upper())
        if is_active is not None:
            stmt = stmt.where(UserModel.is_active == is_active)
        stmt = stmt.order_by(UserModel.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count(
        self,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> int:
        stmt = select(func.count(UserModel.id))
        if role:
            stmt = stmt.where(UserModel.role == role.upper())
        if is_active is not None:
            stmt = stmt.where(UserModel.is_active == is_active)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def exists_by_email(self, email: str) -> bool:
        result = await self.session.execute(
            select(func.count(UserModel.id)).where(
                UserModel.email == email.lower().strip()
            )
        )
        count = result.scalar_one()
        return count > 0

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------
    async def save(self, user: User) -> User:
        model = self._to_model(user)
        merged = await self.session.merge(model)
        await self.session.commit()
        await self.session.refresh(merged)
        return self._to_entity(merged)

    async def delete(self, user_id: UUID) -> bool:
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == user_id)
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
    def _to_entity(model: UserModel) -> User:
        """Map a database model to a domain entity."""
        return User(
            id=model.id,
            email=Email(model.email),
            password_hash=model.password_hash,
            full_name=model.full_name,
            role=Role(model.role),
            organization=model.organization,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_login_at=model.last_login_at,
        )

    @staticmethod
    def _to_model(entity: User) -> UserModel:
        """Map a domain entity to a database model."""
        return UserModel(
            id=entity.id,
            email=str(entity.email),
            password_hash=entity.password_hash,
            full_name=entity.full_name,
            role=entity.role.value,
            organization=entity.organization,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            last_login_at=entity.last_login_at,
        )

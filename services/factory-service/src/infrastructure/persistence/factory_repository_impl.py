"""SQLAlchemy implementation of FactoryRepository."""
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.repositories.factory_repository import FactoryRepository


class SQLAlchemyFactoryRepository(FactoryRepository):
    """Repository Implementation (Adapter) - in infrastructure layer."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, factory_id):
        pass

    async def get_by_registration_number(self, reg_number):
        pass

    async def list_all(self, status=None, skip=0, limit=20):
        pass

    async def save(self, factory):
        pass

    async def delete(self, factory_id):
        pass

"""SQLAlchemy implementation of ViolationRepository."""
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.repositories.violation_repository import ViolationRepository


class SQLAlchemyViolationRepository(ViolationRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, violation_id):
        pass

    async def list_by_factory(self, factory_id):
        pass

    async def list_open(self):
        pass

    async def save(self, violation):
        pass

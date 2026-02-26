"""SQLAlchemy implementation of UserRepository."""
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.repositories.user_repository import UserRepository


class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id):
        pass

    async def get_by_email(self, email):
        pass

    async def list_all(self, skip=0, limit=20):
        pass

    async def save(self, user):
        pass

    async def delete(self, user_id):
        pass

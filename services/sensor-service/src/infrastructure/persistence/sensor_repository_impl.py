"""SQLAlchemy implementation of sensor repositories."""
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.repositories.sensor_repository import SensorRepository
from ...domain.repositories.reading_repository import ReadingRepository


class SQLAlchemySensorRepository(SensorRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, sensor_id):
        pass

    async def list_by_factory(self, factory_id):
        pass

    async def save(self, sensor):
        pass

    async def delete(self, sensor_id):
        pass


class SQLAlchemyReadingRepository(ReadingRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, reading):
        pass

    async def get_by_sensor(self, sensor_id, start, end):
        pass

    async def get_latest_by_factory(self, factory_id):
        pass

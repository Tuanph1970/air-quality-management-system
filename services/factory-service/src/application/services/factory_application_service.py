"""Factory application service - orchestrates use cases."""


class FactoryApplicationService:
    """Orchestrates factory-related use cases."""

    def __init__(self, factory_repository, event_publisher):
        self.factory_repository = factory_repository
        self.event_publisher = event_publisher

    async def create_factory(self, command):
        pass

    async def update_factory(self, command):
        pass

    async def suspend_factory(self, command):
        pass

    async def resume_factory(self, command):
        pass

    async def get_factory(self, factory_id):
        pass

    async def list_factories(self, status=None, skip=0, limit=20):
        pass

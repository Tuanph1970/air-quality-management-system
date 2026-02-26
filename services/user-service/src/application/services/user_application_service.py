"""User application service."""


class UserApplicationService:
    """Orchestrates user-related use cases."""

    def __init__(self, user_repository, auth_service, event_publisher=None):
        self.user_repository = user_repository
        self.auth_service = auth_service
        self.event_publisher = event_publisher

    async def register_user(self, command):
        pass

    async def login(self, command):
        pass

    async def get_user(self, user_id):
        pass

    async def list_users(self, skip=0, limit=20):
        pass

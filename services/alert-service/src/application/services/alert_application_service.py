"""Alert application service."""


class AlertApplicationService:
    """Orchestrates alert-related use cases."""

    def __init__(self, violation_repository, event_publisher, notification_service):
        self.violation_repository = violation_repository
        self.event_publisher = event_publisher
        self.notification_service = notification_service

    async def create_violation(self, command):
        pass

    async def resolve_violation(self, command):
        pass

    async def get_violations(self, query):
        pass

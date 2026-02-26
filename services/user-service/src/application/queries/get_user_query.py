"""Query to get a user."""
from dataclasses import dataclass
from uuid import UUID


@dataclass
class GetUserQuery:
    user_id: UUID

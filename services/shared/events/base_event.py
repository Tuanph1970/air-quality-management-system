"""Base domain event definition.

All domain events inherit from DomainEvent and gain serialization
support via to_dict()/from_dict() for RabbitMQ message transport.
"""
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime, timezone
from typing import Any, Dict, Type, TypeVar
from uuid import UUID, uuid4

T = TypeVar("T", bound="DomainEvent")


@dataclass
class DomainEvent:
    """Base class for all domain events.

    Provides identity, timestamp, type discriminator, and serialization
    so every event can be published to and consumed from RabbitMQ as a
    plain dict / JSON payload.
    """

    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str = ""

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        """Serialize the event to a JSON-compatible dictionary.

        UUIDs are converted to strings and datetimes to ISO-8601 so the
        result can be passed straight to ``json.dumps``.
        """
        raw = asdict(self)
        return self._convert_values(raw)

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Reconstruct an event instance from a dictionary.

        Only keys that match declared dataclass fields are forwarded to
        the constructor so stale / extra keys in stored messages are
        silently ignored.
        """
        valid_fields = {f.name for f in fields(cls)}
        filtered: Dict[str, Any] = {}

        for key, value in data.items():
            if key not in valid_fields:
                continue
            filtered[key] = cls._restore_value(key, value, cls)

        return cls(**filtered)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _convert_values(data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively convert non-JSON-native types."""
        converted: Dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, UUID):
                converted[key] = str(value)
            elif isinstance(value, datetime):
                converted[key] = value.isoformat()
            elif isinstance(value, dict):
                converted[key] = DomainEvent._convert_values(value)
            else:
                converted[key] = value
        return converted

    @classmethod
    def _restore_value(cls, key: str, value: Any, target_cls: type) -> Any:
        """Coerce a single value back to its declared field type."""
        if value is None:
            return None

        # Look up the field's declared type by name
        field_type = None
        for f in fields(target_cls):
            if f.name == key:
                field_type = f.type
                break

        if field_type is None:
            return value

        # UUID fields
        if field_type is UUID or field_type == "UUID":
            return UUID(value) if isinstance(value, str) else value

        # datetime fields
        if field_type is datetime or field_type == "datetime":
            if isinstance(value, str):
                return datetime.fromisoformat(value)
            return value

        return value

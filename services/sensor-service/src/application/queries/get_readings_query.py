"""Query to get sensor readings."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class GetReadingsQuery:
    sensor_id: Optional[UUID] = None
    factory_id: Optional[UUID] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = 100

"""Domain events for satellite / remote-sensing and Excel import operations."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional
from uuid import UUID

from .base_event import DomainEvent


@dataclass
class SatelliteDataFetched(DomainEvent):
    """Published when satellite data is successfully fetched."""

    source: str = ""                # 'MODIS', 'TROPOMI', 'CAMS'
    data_type: str = ""             # 'AOD', 'NO2', 'PM25'
    observation_time: datetime = None
    bbox: Dict = None               # {north, south, east, west}
    record_count: int = 0
    file_path: Optional[str] = None
    event_type: str = "satellite.data.fetched"


@dataclass
class SatelliteFetchFailed(DomainEvent):
    """Published when satellite data fetch fails."""

    source: str = ""
    error_message: str = ""
    retry_count: int = 0
    event_type: str = "satellite.fetch.failed"


@dataclass
class ExcelDataImported(DomainEvent):
    """Published when Excel data is imported."""

    import_id: UUID = None
    filename: str = ""
    record_count: int = 0
    data_type: str = ""             # 'historical_readings', 'factory_records'
    event_type: str = "excel.data.imported"


@dataclass
class ExcelImportFailed(DomainEvent):
    """Published when Excel import fails."""

    import_id: UUID = None
    filename: str = ""
    error_message: str = ""
    event_type: str = "excel.import.failed"

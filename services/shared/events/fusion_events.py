"""Domain events for data fusion and cross-validation operations."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from .base_event import DomainEvent


@dataclass
class DataFusionCompleted(DomainEvent):
    """Published when data fusion completes."""

    fusion_id: UUID = None
    sources_used: List[str] = None   # ['sensor', 'satellite', 'excel']
    location_count: int = 0
    time_range_start: datetime = None
    time_range_end: datetime = None
    average_confidence: float = 0.0
    event_type: str = "fusion.completed"


@dataclass
class CalibrationUpdated(DomainEvent):
    """Published when sensor calibration model is updated."""

    sensor_id: Optional[UUID] = None  # None if global model
    model_version: str = ""
    r_squared: float = 0.0
    rmse: float = 0.0
    training_samples: int = 0
    event_type: str = "calibration.updated"


@dataclass
class CrossValidationAlert(DomainEvent):
    """Published when cross-validation detects anomaly."""

    sensor_id: UUID = None
    sensor_value: float = 0.0
    satellite_value: float = 0.0
    deviation_percent: float = 0.0
    pollutant: str = ""
    event_type: str = "validation.alert"

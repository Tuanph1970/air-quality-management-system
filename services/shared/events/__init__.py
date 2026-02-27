"""Shared domain events for inter-service communication via RabbitMQ."""

from .base_event import DomainEvent

from .factory_events import (
    FactoryCreated,
    FactoryUpdated,
    FactoryStatusChanged,
    FactorySuspended,
    FactoryResumed,
)

from .sensor_events import (
    SensorRegistered,
    SensorReadingCreated,
    SensorCalibrated,
    SensorStatusChanged,
)

from .alert_events import (
    ViolationDetected,
    ViolationResolved,
    AlertConfigUpdated,
)

from .satellite_events import (
    SatelliteDataFetched,
    SatelliteFetchFailed,
    ExcelDataImported,
    ExcelImportFailed,
)

from .fusion_events import (
    DataFusionCompleted,
    CalibrationUpdated,
    CrossValidationAlert,
)

__all__ = [
    "DomainEvent",
    # Factory
    "FactoryCreated",
    "FactoryUpdated",
    "FactoryStatusChanged",
    "FactorySuspended",
    "FactoryResumed",
    # Sensor
    "SensorRegistered",
    "SensorReadingCreated",
    "SensorCalibrated",
    "SensorStatusChanged",
    # Alert
    "ViolationDetected",
    "ViolationResolved",
    "AlertConfigUpdated",
    # Satellite / Remote Sensing
    "SatelliteDataFetched",
    "SatelliteFetchFailed",
    "ExcelDataImported",
    "ExcelImportFailed",
    # Fusion / Calibration
    "DataFusionCompleted",
    "CalibrationUpdated",
    "CrossValidationAlert",
]

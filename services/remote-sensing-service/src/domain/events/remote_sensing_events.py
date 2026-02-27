"""Remote sensing domain events.

This service primarily uses shared events defined in:
- shared.events.satellite_events (SatelliteDataFetched, ExcelDataImported, etc.)
- shared.events.fusion_events (DataFusionCompleted, CalibrationUpdated, CrossValidationAlert)

Events are emitted by domain entities and services, then published
via the infrastructure messaging layer to RabbitMQ.
"""

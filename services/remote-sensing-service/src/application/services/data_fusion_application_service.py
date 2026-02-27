"""Application service for data fusion and cross-validation.

Orchestrates domain services (DataFusionService, CalibrationService,
CrossValidationService) with repository and event-publishing concerns.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from ...domain.entities.fused_data import FusedData
from ...domain.entities.satellite_data import SatelliteData
from ...domain.repositories.fused_data_repository import FusedDataRepository
from ...domain.repositories.satellite_data_repository import SatelliteDataRepository
from ...domain.services.calibration_service import (
    CalibrationResult,
    CalibrationService,
)
from ...domain.services.cross_validation_service import (
    CrossValidationService,
    ValidationResult,
)
from ...domain.services.data_fusion_service import (
    DataFusionService,
    ExcelRecord,
    SensorReading,
)
from ...domain.value_objects.geo_polygon import GeoPolygon
from ...domain.value_objects.satellite_source import SatelliteSource
from ...infrastructure.external.sensor_service_client import SensorServiceClient
from ..dto.fusion_dto import FusedDataDTO
from shared.messaging.publisher import RabbitMQPublisher
from shared.messaging.config import FUSION_EXCHANGE

logger = logging.getLogger(__name__)


class DataFusionApplicationService:
    """Application service for data fusion and cross-validation."""

    def __init__(
        self,
        satellite_repo: SatelliteDataRepository,
        fused_repo: FusedDataRepository,
        fusion_service: DataFusionService,
        calibration_service: CalibrationService,
        cross_validation_service: CrossValidationService,
        sensor_client: SensorServiceClient,
        event_publisher: RabbitMQPublisher,
    ):
        self.satellite_repo = satellite_repo
        self.fused_repo = fused_repo
        self.fusion_service = fusion_service
        self.calibration_service = calibration_service
        self.cross_validation_service = cross_validation_service
        self.sensor_client = sensor_client
        self.event_publisher = event_publisher

    # ------------------------------------------------------------------
    # Fusion
    # ------------------------------------------------------------------
    async def run_fusion(
        self,
        bbox: GeoPolygon,
        time_range: Tuple[datetime, datetime],
        pollutant: str = "PM25",
        sources: Optional[List[SatelliteSource]] = None,
    ) -> FusedDataDTO:
        """Run data fusion for the specified area and time range.

        1. Fetch recent satellite data from the repository.
        2. Fetch recent sensor readings from the sensor service.
        3. Invoke the domain fusion service.
        4. Persist the fused result and publish events.
        """
        start, end = time_range

        # Gather satellite data.
        satellite_data: List[SatelliteData] = []
        target_sources = sources or list(SatelliteSource)
        for source in target_sources:
            data_list = await self.satellite_repo.get_by_time_range(
                source, start, end, bbox
            )
            satellite_data.extend(data_list)

        # Gather sensor readings from sensor-service.
        raw_readings = await self.sensor_client.get_readings_by_time_range(
            start, end
        )
        sensor_readings = [
            SensorReading(
                sensor_id=str(r.get("sensor_id", "")),
                lat=float(r.get("latitude", r.get("lat", 0))),
                lon=float(r.get("longitude", r.get("lon", 0))),
                value=float(r.get("value", r.get("pm25", 0))),
                timestamp=datetime.fromisoformat(str(r["timestamp"])),
                pollutant=pollutant,
            )
            for r in raw_readings
            if r.get("timestamp")
        ]

        # Domain fusion.
        fused = self.fusion_service.fuse(
            satellite_data=satellite_data,
            sensor_readings=sensor_readings,
            excel_records=[],
            bbox=bbox,
            time_range=time_range,
            pollutant=pollutant,
        )

        # Persist.
        saved = await self.fused_repo.save(fused)

        # Publish events.
        for event in saved.collect_events():
            await self.event_publisher.publish(event, FUSION_EXCHANGE)

        logger.info(
            "Fusion completed: id=%s points=%d confidence=%.2f",
            saved.id,
            len(saved.data_points),
            saved.average_confidence,
        )

        return FusedDataDTO.from_entity(saved, include_points=True)

    # ------------------------------------------------------------------
    # Cross-validation
    # ------------------------------------------------------------------
    async def run_cross_validation(
        self,
        source: SatelliteSource,
        start_time: datetime,
        end_time: datetime,
        pollutant: str = "PM25",
    ) -> List[Dict]:
        """Run cross-validation between sensor readings and satellite data.

        Returns a list of validation result dicts.  Any anomalous results
        are published as ``CrossValidationAlert`` events.
        """
        satellite_data = await self.satellite_repo.get_by_time_range(
            source, start_time, end_time
        )
        raw_readings = await self.sensor_client.get_readings_by_time_range(
            start_time, end_time
        )

        # Adapt raw readings to the dict format expected by the domain service.
        readings_for_cv = []
        for r in raw_readings:
            if not r.get("timestamp"):
                continue
            readings_for_cv.append(
                {
                    "sensor_id": r.get("sensor_id"),
                    "lat": float(r.get("latitude", r.get("lat", 0))),
                    "lon": float(r.get("longitude", r.get("lon", 0))),
                    "value": float(r.get("value", r.get("pm25", 0))),
                    "timestamp": datetime.fromisoformat(str(r["timestamp"])),
                }
            )

        results = self.cross_validation_service.validate_readings(
            readings_for_cv, satellite_data, pollutant
        )

        # Publish alerts for anomalies.
        anomalies = [r for r in results if r.is_anomalous]
        if anomalies:
            events = self.cross_validation_service.build_alert_events(anomalies)
            for event in events:
                await self.event_publisher.publish(event, FUSION_EXCHANGE)
            logger.warning(
                "Cross-validation: %d anomalies detected out of %d readings",
                len(anomalies),
                len(results),
            )

        return [
            {
                "sensor_id": str(r.sensor_id),
                "sensor_value": r.sensor_value,
                "satellite_value": r.satellite_value,
                "deviation_percent": round(r.deviation_percent, 2),
                "is_anomalous": r.is_anomalous,
                "pollutant": r.pollutant,
                "timestamp": r.timestamp.isoformat(),
            }
            for r in results
        ]

    # ------------------------------------------------------------------
    # Calibration
    # ------------------------------------------------------------------
    async def run_calibration(
        self,
        source: SatelliteSource,
        start_time: datetime,
        end_time: datetime,
        sensor_id: Optional[UUID] = None,
    ) -> Dict:
        """Run sensor calibration against satellite observations.

        Returns calibration model parameters.
        """
        satellite_data = await self.satellite_repo.get_by_time_range(
            source, start_time, end_time
        )
        raw_readings = await self.sensor_client.get_readings_by_time_range(
            start_time, end_time
        )

        readings_for_cal = [
            {
                "sensor_id": r.get("sensor_id"),
                "lat": float(r.get("latitude", r.get("lat", 0))),
                "lon": float(r.get("longitude", r.get("lon", 0))),
                "value": float(r.get("value", r.get("pm25", 0))),
                "timestamp": datetime.fromisoformat(str(r["timestamp"])),
            }
            for r in raw_readings
            if r.get("timestamp")
        ]

        pairs = self.calibration_service.match_pairs(
            readings_for_cal, satellite_data
        )

        if len(pairs) < 2:
            return {"error": "Insufficient matched pairs for calibration", "pairs": len(pairs)}

        result = self.calibration_service.compute_calibration(
            pairs, sensor_id=sensor_id
        )

        logger.info(
            "Calibration completed: slope=%.4f intercept=%.4f R²=%.4f",
            result.slope,
            result.intercept,
            result.r_squared,
        )

        return {
            "sensor_id": str(result.sensor_id) if result.sensor_id else None,
            "slope": round(result.slope, 6),
            "intercept": round(result.intercept, 6),
            "r_squared": round(result.r_squared, 6),
            "rmse": round(result.rmse, 6),
            "training_samples": result.training_samples,
            "model_version": result.model_version,
            "computed_at": result.computed_at.isoformat(),
        }

    # ------------------------------------------------------------------
    # Query operations
    # ------------------------------------------------------------------
    async def get_fused_data(
        self, fusion_id: UUID
    ) -> Optional[FusedDataDTO]:
        """Get fused data by ID."""
        fused = await self.fused_repo.get_by_id(fusion_id)
        return FusedDataDTO.from_entity(fused, include_points=True) if fused else None

    async def get_latest_fusion(
        self, pollutant: str = ""
    ) -> Optional[FusedDataDTO]:
        """Get the most recent fusion result."""
        fused = await self.fused_repo.get_latest(pollutant)
        return FusedDataDTO.from_entity(fused) if fused else None

    async def cleanup_old_fusions(self, days: int = 30) -> int:
        """Remove fused data older than the given number of days."""
        deleted = await self.fused_repo.delete_older_than(days)
        logger.info("Cleaned up %d fusion records older than %d days", deleted, days)
        return deleted

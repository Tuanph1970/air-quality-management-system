"""Sensor application service — orchestrates use cases.

This is the primary entry point for all sensor-related operations.  Each
public method represents a single use case and follows the pattern:

    1. Validate input (command / query)
    2. Load or create the domain entity
    3. Execute domain logic
    4. Persist changes
    5. Publish domain events
    6. Return a DTO

**CRITICAL FLOW — reading submission**:
    1. Validate the incoming reading data.
    2. Verify the sensor exists and is online.
    3. Calculate the AQI using the domain ``AQICalculator`` service.
    4. Create the ``Reading`` domain entity.
    5. Save the reading to TimescaleDB.
    6. Publish a ``SensorReadingCreated`` event (consumed by Alert Service).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from ...domain.entities.reading import Reading
from ...domain.entities.sensor import Sensor
from ...domain.exceptions.sensor_exceptions import (
    SensorAlreadyExistsError,
    SensorNotFoundError,
    SensorOfflineError,
)
from ...domain.repositories.reading_repository import ReadingRepository
from ...domain.repositories.sensor_repository import SensorRepository
from ...domain.services.aqi_calculator import AQICalculator
from ..commands.calibrate_sensor_command import CalibrateSensorCommand
from ..commands.register_sensor_command import RegisterSensorCommand
from ..commands.submit_reading_command import SubmitReadingCommand
from ..dto.reading_dto import ReadingDTO, ReadingListDTO
from ..dto.sensor_dto import SensorDTO, SensorListDTO
from ..interfaces.event_publisher import EventPublisher
from ..queries.get_readings_query import GetReadingAverageQuery, GetReadingsQuery
from ..queries.get_sensor_query import GetSensorQuery, ListSensorsQuery

logger = logging.getLogger(__name__)


class SensorApplicationService:
    """Orchestrates sensor-related use cases.

    Depends on three ports injected at construction time:

    * ``sensor_repository`` — sensor persistence (domain layer)
    * ``reading_repository`` — reading persistence (domain layer)
    * ``event_publisher`` — messaging abstraction (application layer)
    """

    def __init__(
        self,
        sensor_repository: SensorRepository,
        reading_repository: ReadingRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._sensor_repo = sensor_repository
        self._reading_repo = reading_repository
        self._publisher = event_publisher

    # ------------------------------------------------------------------
    # Command handlers (write operations)
    # ------------------------------------------------------------------
    async def register_sensor(self, command: RegisterSensorCommand) -> SensorDTO:
        """Use case: register a new sensor.

        Steps:
            1. Validate the command payload.
            2. Check for duplicate serial number.
            3. Create the domain entity (emits ``SensorRegistered``).
            4. Persist via repository.
            5. Publish events.
            6. Return DTO.
        """
        command.validate()

        existing = await self._sensor_repo.get_by_serial_number(
            command.serial_number,
        )
        if existing:
            raise SensorAlreadyExistsError(command.serial_number)

        sensor = Sensor.register(
            serial_number=command.serial_number,
            sensor_type=command.sensor_type,
            model=command.model,
            latitude=command.latitude,
            longitude=command.longitude,
            factory_id=command.factory_id,
            calibration_params=command.calibration_params or None,
        )

        saved = await self._sensor_repo.save(sensor)
        await self._publish_events(saved)

        logger.info(
            "Sensor registered: %s (serial=%s)", saved.id, saved.serial_number,
        )
        return SensorDTO.from_entity(saved)

    async def submit_reading(self, command: SubmitReadingCommand) -> ReadingDTO:
        """Use case: submit a sensor reading.

        **Critical flow** consumed by the Alert Service:

            1. Validate the command payload.
            2. Load the sensor and verify it is online.
            3. Calculate the AQI from pollutant concentrations.
            4. Create a ``Reading`` domain entity.
            5. Save the reading to TimescaleDB.
            6. Publish ``SensorReadingCreated`` event.
            7. Return DTO.
        """
        command.validate()

        # 1. Load and verify sensor
        sensor = await self._get_sensor_or_raise(command.sensor_id)
        if not sensor.status.can_submit_reading:
            raise SensorOfflineError(str(sensor.id))

        # 2. Calculate AQI using domain service
        pollutant_readings = {
            "pm25": command.pm25,
            "pm10": command.pm10,
            "co": command.co,
            "no2": command.no2,
            "so2": command.so2,
            "o3": command.o3,
        }
        aqi = AQICalculator.calculate_aqi(pollutant_readings)

        # 3. Create reading entity
        reading = Reading.create(
            sensor_id=command.sensor_id,
            factory_id=sensor.factory_id,
            pm25=command.pm25,
            pm10=command.pm10,
            co=command.co,
            co2=command.co2,
            no2=command.no2,
            nox=command.nox,
            so2=command.so2,
            o3=command.o3,
            temperature=command.temperature,
            humidity=command.humidity,
            aqi=aqi,
            timestamp=command.timestamp,
        )

        # 4. Save to TimescaleDB
        saved_reading = await self._reading_repo.save(reading)

        # 5. Publish SensorReadingCreated event
        from shared.events.sensor_events import SensorReadingCreated

        event = SensorReadingCreated(
            sensor_id=sensor.id,
            factory_id=sensor.factory_id,
            pm25=command.pm25,
            pm10=command.pm10,
            aqi=aqi,
            timestamp=saved_reading.timestamp,
        )
        try:
            await self._publisher.publish(event)
        except Exception:
            logger.exception(
                "Failed to publish SensorReadingCreated for sensor %s",
                sensor.id,
            )

        logger.info(
            "Reading submitted: sensor=%s aqi=%d", sensor.id, aqi,
        )
        return ReadingDTO.from_entity(saved_reading)

    async def calibrate_sensor(self, command: CalibrateSensorCommand) -> SensorDTO:
        """Use case: calibrate a sensor.

        Steps:
            1. Validate the command.
            2. Load the sensor.
            3. Apply calibration via domain method.
            4. Persist.
            5. Publish ``SensorCalibrated`` event.
            6. Return DTO.
        """
        command.validate()

        sensor = await self._get_sensor_or_raise(command.sensor_id)
        sensor.calibrate(
            params=command.calibration_params,
            calibrated_by=command.calibrated_by,
        )

        saved = await self._sensor_repo.save(sensor)
        await self._publish_events(saved)

        logger.info("Sensor calibrated: %s", saved.id)
        return SensorDTO.from_entity(saved)

    async def update_sensor_status(
        self, sensor_id: UUID, new_status: str, reason: str = "",
    ) -> SensorDTO:
        """Use case: update sensor operational status.

        Steps:
            1. Load the sensor.
            2. Apply status change via domain method.
            3. Persist.
            4. Publish ``SensorStatusChanged`` event.
            5. Return DTO.
        """
        sensor = await self._get_sensor_or_raise(sensor_id)
        sensor.update_status(new_status=new_status, reason=reason)

        saved = await self._sensor_repo.save(sensor)
        await self._publish_events(saved)

        logger.info(
            "Sensor status updated: %s → %s", saved.id, new_status,
        )
        return SensorDTO.from_entity(saved)

    async def delete_sensor(self, sensor_id: UUID) -> bool:
        """Use case: permanently delete a sensor.

        Raises ``SensorNotFoundError`` if the sensor does not exist.
        """
        await self._get_sensor_or_raise(sensor_id)

        deleted = await self._sensor_repo.delete(sensor_id)
        if deleted:
            logger.info("Sensor deleted: %s", sensor_id)
        return deleted

    # ------------------------------------------------------------------
    # Query handlers (read operations)
    # ------------------------------------------------------------------
    async def get_sensor(self, sensor_id: UUID) -> SensorDTO:
        """Use case: get a single sensor by ID.

        Raises ``SensorNotFoundError`` if the sensor does not exist.
        """
        sensor = await self._get_sensor_or_raise(sensor_id)
        return SensorDTO.from_entity(sensor)

    async def list_sensors(self, query: ListSensorsQuery) -> SensorListDTO:
        """Use case: list sensors with optional filters and pagination."""
        query.validate()

        if query.factory_id:
            sensors = await self._sensor_repo.list_by_factory(
                factory_id=query.factory_id,
                status=query.status,
                skip=query.skip,
                limit=query.limit,
            )
            total = await self._sensor_repo.count(
                factory_id=query.factory_id,
                status=query.status,
            )
        else:
            sensors = await self._sensor_repo.list_all(
                status=query.status,
                skip=query.skip,
                limit=query.limit,
            )
            total = await self._sensor_repo.count(status=query.status)

        return SensorListDTO(
            items=[SensorDTO.from_entity(s) for s in sensors],
            total=total,
            skip=query.skip,
            limit=query.limit,
        )

    async def get_readings(self, query: GetReadingsQuery) -> ReadingListDTO:
        """Use case: get readings with optional filters and time range."""
        query.validate()

        now = datetime.now(timezone.utc)
        start = query.start_time or datetime(2000, 1, 1, tzinfo=timezone.utc)
        end = query.end_time or now

        if query.sensor_id:
            readings = await self._reading_repo.get_readings(
                sensor_id=query.sensor_id,
                start=start,
                end=end,
                limit=query.limit,
            )
            total = await self._reading_repo.count(
                sensor_id=query.sensor_id,
                start=start,
                end=end,
            )
        else:
            # Get latest reading for each sensor in the factory
            latest = await self._reading_repo.get_latest_by_factory(
                query.factory_id,
            )
            readings = [latest] if latest else []
            total = len(readings)

        return ReadingListDTO(
            items=[ReadingDTO.from_entity(r) for r in readings],
            total=total,
            skip=query.skip,
            limit=query.limit,
        )

    async def get_latest_reading(self, sensor_id: UUID) -> Optional[ReadingDTO]:
        """Use case: get the most recent reading for a sensor."""
        reading = await self._reading_repo.get_latest(sensor_id)
        return ReadingDTO.from_entity(reading) if reading else None

    async def get_reading_average(
        self, query: GetReadingAverageQuery,
    ) -> Optional[ReadingDTO]:
        """Use case: get an averaged reading over a time range."""
        query.validate()

        reading = await self._reading_repo.get_average(
            sensor_id=query.sensor_id,
            start=query.start_time,
            end=query.end_time,
        )
        return ReadingDTO.from_entity(reading) if reading else None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _get_sensor_or_raise(self, sensor_id: UUID) -> Sensor:
        """Load a sensor by ID or raise ``SensorNotFoundError``."""
        sensor = await self._sensor_repo.get_by_id(sensor_id)
        if sensor is None:
            raise SensorNotFoundError(str(sensor_id))
        return sensor

    async def _publish_events(self, sensor: Sensor) -> None:
        """Collect and publish all pending domain events from the entity."""
        for event in sensor.collect_events():
            try:
                await self._publisher.publish(event)
            except Exception:
                logger.exception(
                    "Failed to publish event %s for sensor %s",
                    type(event).__name__,
                    sensor.id,
                )

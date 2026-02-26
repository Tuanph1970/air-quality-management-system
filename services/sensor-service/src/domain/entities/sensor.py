"""Sensor entity — the core aggregate root of the sensor bounded context.

Encapsulates identity, lifecycle state, calibration data, and domain event
emission for air-quality sensor devices.  All state mutations go through
explicit methods that enforce invariants and record events for downstream
consumers.

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from ..events.sensor_events import (
    SensorCalibrated,
    SensorRegistered,
    SensorStatusChanged,
)
from ..exceptions.sensor_exceptions import (
    InvalidSensorStatusError,
    SensorAlreadyOnlineError,
    SensorOfflineError,
)
from ..value_objects.calibration_params import CalibrationParams
from ..value_objects.sensor_status import SensorStatus
from ..value_objects.sensor_type import SensorType


@dataclass
class Sensor:
    """Aggregate root representing an air-quality sensor device.

    Identity is defined by ``id`` (UUID).  ``serial_number`` is a
    natural key that must be unique across the system.
    """

    id: UUID = field(default_factory=uuid4)
    serial_number: str = ""
    sensor_type: SensorType = SensorType.LOW_COST_PM
    model: str = ""
    factory_id: Optional[UUID] = None
    latitude: float = 0.0
    longitude: float = 0.0
    calibration_params: CalibrationParams = field(
        default_factory=CalibrationParams,
    )
    status: SensorStatus = SensorStatus.ONLINE
    installation_date: Optional[datetime] = None
    last_calibration: Optional[datetime] = None
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    _events: List = field(default_factory=list, repr=False)

    # ------------------------------------------------------------------
    # Factory method (named-constructor pattern)
    # ------------------------------------------------------------------
    @classmethod
    def register(
        cls,
        serial_number: str,
        sensor_type: str | SensorType,
        model: str,
        latitude: float,
        longitude: float,
        factory_id: Optional[UUID] = None,
        calibration_params: Optional[dict] = None,
    ) -> Sensor:
        """Register a new sensor device.

        Parameters
        ----------
        serial_number:
            Unique hardware identifier (e.g. ``SN-2024-001``).
        sensor_type:
            Classification string or ``SensorType`` enum member.
        model:
            Hardware model name (e.g. ``PMS5003``).
        latitude, longitude:
            Installation coordinates.
        factory_id:
            Optional factory this sensor is associated with.
        calibration_params:
            Optional initial calibration dictionary.

        Raises
        ------
        ValueError
            If ``serial_number`` is empty or coordinates are invalid.
        """
        if not serial_number or not serial_number.strip():
            raise ValueError("serial_number must not be empty")
        if not model or not model.strip():
            raise ValueError("model must not be empty")
        if not -90.0 <= latitude <= 90.0:
            raise ValueError(f"Latitude must be between -90 and 90, got {latitude}")
        if not -180.0 <= longitude <= 180.0:
            raise ValueError(f"Longitude must be between -180 and 180, got {longitude}")

        # Coerce string to enum
        if isinstance(sensor_type, str):
            sensor_type = SensorType(sensor_type)

        cal = (
            CalibrationParams.from_dict(calibration_params)
            if calibration_params
            else CalibrationParams()
        )

        now = datetime.now(timezone.utc)
        sensor = cls(
            id=uuid4(),
            serial_number=serial_number.strip(),
            sensor_type=sensor_type,
            model=model.strip(),
            factory_id=factory_id,
            latitude=latitude,
            longitude=longitude,
            calibration_params=cal,
            status=SensorStatus.ONLINE,
            installation_date=now,
            last_calibration=None,
            created_at=now,
            updated_at=now,
        )

        sensor._events.append(
            SensorRegistered(
                sensor_id=sensor.id,
                factory_id=factory_id,
                sensor_type=sensor_type.value,
                latitude=latitude,
                longitude=longitude,
            )
        )
        return sensor

    # ------------------------------------------------------------------
    # Command methods (state mutations)
    # ------------------------------------------------------------------
    def calibrate(
        self,
        params: dict | CalibrationParams,
        calibrated_by: Optional[UUID] = None,
    ) -> None:
        """Apply new calibration parameters.

        Parameters
        ----------
        params:
            Either a ``CalibrationParams`` instance or a dictionary
            that ``CalibrationParams.from_dict()`` can parse.
        calibrated_by:
            UUID of the user who performed the calibration.

        Raises
        ------
        InvalidSensorStatusError
            If the sensor is offline.
        """
        if self.status == SensorStatus.OFFLINE:
            raise InvalidSensorStatusError(
                current=self.status.value,
                target="CALIBRATING",
            )

        old_status = self.status
        self.status = SensorStatus.CALIBRATING

        if isinstance(params, dict):
            self.calibration_params = CalibrationParams.from_dict(params)
        else:
            self.calibration_params = params

        now = datetime.now(timezone.utc)
        self.last_calibration = now
        self.updated_at = now

        # Return to previous active state after calibration
        self.status = old_status if old_status == SensorStatus.ONLINE else SensorStatus.ONLINE

        self._events.append(
            SensorCalibrated(
                sensor_id=self.id,
                calibrated_by=calibrated_by,
                offset=self.calibration_params.offset,
                scale_factor=self.calibration_params.scale_factor,
            )
        )

    def update_status(self, new_status: str | SensorStatus, reason: str = "") -> None:
        """Transition the sensor to a new operational status.

        Parameters
        ----------
        new_status:
            Target status (string or ``SensorStatus`` enum).
        reason:
            Human-readable reason for the transition.

        Raises
        ------
        SensorAlreadyOnlineError
            If the sensor is already in the requested status.
        InvalidSensorStatusError
            If the transition is not permitted.
        """
        if isinstance(new_status, str):
            new_status = SensorStatus(new_status)

        if self.status == new_status:
            raise SensorAlreadyOnlineError() if new_status == SensorStatus.ONLINE else InvalidSensorStatusError(
                current=self.status.value,
                target=new_status.value,
            )

        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)

        self._events.append(
            SensorStatusChanged(
                sensor_id=self.id,
                factory_id=self.factory_id,
                old_status=old_status.value,
                new_status=new_status.value,
                reason=reason,
            )
        )

    def go_offline(self, reason: str = "") -> None:
        """Convenience method to take the sensor offline."""
        self.update_status(SensorStatus.OFFLINE, reason=reason)

    def go_online(self, reason: str = "") -> None:
        """Convenience method to bring the sensor online."""
        self.update_status(SensorStatus.ONLINE, reason=reason)

    def start_maintenance(self, reason: str = "") -> None:
        """Put the sensor into maintenance mode."""
        if self.status == SensorStatus.OFFLINE:
            raise InvalidSensorStatusError(
                current=self.status.value,
                target=SensorStatus.MAINTENANCE.value,
            )
        self.update_status(SensorStatus.MAINTENANCE, reason=reason)

    def update(
        self,
        model: Optional[str] = None,
        factory_id: Optional[UUID] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> None:
        """Update mutable sensor metadata.

        Only non-``None`` arguments are applied.
        """
        changed = False

        if model is not None and model != self.model:
            if not model.strip():
                raise ValueError("model must not be empty")
            self.model = model.strip()
            changed = True

        if factory_id is not None and factory_id != self.factory_id:
            self.factory_id = factory_id
            changed = True

        if latitude is not None and latitude != self.latitude:
            if not -90.0 <= latitude <= 90.0:
                raise ValueError(f"Latitude must be between -90 and 90, got {latitude}")
            self.latitude = latitude
            changed = True

        if longitude is not None and longitude != self.longitude:
            if not -180.0 <= longitude <= 180.0:
                raise ValueError(f"Longitude must be between -180 and 180, got {longitude}")
            self.longitude = longitude
            changed = True

        if changed:
            self.updated_at = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    @property
    def is_online(self) -> bool:
        """Return ``True`` if the sensor is currently online."""
        return self.status == SensorStatus.ONLINE

    @property
    def is_calibrated(self) -> bool:
        """Return ``True`` if the sensor has been calibrated at least once."""
        return self.last_calibration is not None

    # ------------------------------------------------------------------
    # Event collection
    # ------------------------------------------------------------------
    def collect_events(self) -> List:
        """Return and clear accumulated domain events."""
        events = self._events.copy()
        self._events.clear()
        return events

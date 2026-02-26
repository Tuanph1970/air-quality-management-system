"""Reading entity — time-series air-quality measurement.

Represents a single snapshot of pollutant concentrations captured by a
sensor at a specific point in time.  Readings are the highest-volume
entities in the system and are typically stored in TimescaleDB for
efficient time-series queries.

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from ..exceptions.sensor_exceptions import InvalidReadingError
from ..value_objects.air_quality_reading import AirQualityReading


@dataclass
class Reading:
    """A single air-quality measurement from a sensor.

    Identity is defined by ``id`` (UUID).  The ``timestamp`` indicates
    when the measurement was taken (not when it was persisted).
    """

    id: UUID = field(default_factory=uuid4)
    sensor_id: UUID = None
    factory_id: Optional[UUID] = None

    # Pollutant concentrations (ug/m3 unless noted)
    pm25: float = 0.0
    pm10: float = 0.0
    co: float = 0.0        # mg/m3
    co2: float = 0.0       # ppm
    no2: float = 0.0
    nox: float = 0.0
    so2: float = 0.0
    o3: float = 0.0

    # Environmental parameters
    temperature: float = 0.0   # Celsius
    humidity: float = 0.0      # %RH

    # Calculated AQI (0-500 scale)
    aqi: int = 0

    # Measurement timestamp
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    # ------------------------------------------------------------------
    # Factory method
    # ------------------------------------------------------------------
    @classmethod
    def create(
        cls,
        sensor_id: UUID,
        pm25: float = 0.0,
        pm10: float = 0.0,
        co: float = 0.0,
        co2: float = 0.0,
        no2: float = 0.0,
        nox: float = 0.0,
        so2: float = 0.0,
        o3: float = 0.0,
        temperature: float = 0.0,
        humidity: float = 0.0,
        aqi: int = 0,
        factory_id: Optional[UUID] = None,
        timestamp: Optional[datetime] = None,
    ) -> Reading:
        """Create a new reading with validation.

        Parameters
        ----------
        sensor_id:
            The sensor that produced this reading.
        pm25, pm10, co, co2, no2, nox, so2, o3:
            Pollutant concentration values.
        temperature, humidity:
            Environmental parameters.
        aqi:
            Pre-calculated AQI value (0-500).
        factory_id:
            Optional factory association.
        timestamp:
            When the reading was taken (defaults to now).

        Raises
        ------
        InvalidReadingError
            If any reading value is negative or out of range.
        """
        if sensor_id is None:
            raise InvalidReadingError("sensor_id is required")

        # Validate non-negative pollutant values
        pollutants = {
            "pm25": pm25, "pm10": pm10, "co": co, "co2": co2,
            "no2": no2, "nox": nox, "so2": so2, "o3": o3,
        }
        for name, value in pollutants.items():
            if value < 0.0:
                raise InvalidReadingError(
                    f"{name} must be non-negative, got {value}"
                )

        if not 0 <= aqi <= 500:
            raise InvalidReadingError(
                f"AQI must be between 0 and 500, got {aqi}"
            )

        if humidity < 0.0 or humidity > 100.0:
            raise InvalidReadingError(
                f"Humidity must be between 0 and 100, got {humidity}"
            )

        return cls(
            id=uuid4(),
            sensor_id=sensor_id,
            factory_id=factory_id,
            pm25=pm25,
            pm10=pm10,
            co=co,
            co2=co2,
            no2=no2,
            nox=nox,
            so2=so2,
            o3=o3,
            temperature=temperature,
            humidity=humidity,
            aqi=aqi,
            timestamp=timestamp or datetime.now(timezone.utc),
        )

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    def to_air_quality_reading(self) -> AirQualityReading:
        """Convert to an immutable ``AirQualityReading`` value object."""
        return AirQualityReading(
            pm25=self.pm25,
            pm10=self.pm10,
            co=self.co,
            co2=self.co2,
            no2=self.no2,
            nox=self.nox,
            so2=self.so2,
            o3=self.o3,
            temperature=self.temperature,
            humidity=self.humidity,
        )

    def pollutant_dict(self) -> Dict[str, float]:
        """Return pollutant concentrations as a dictionary."""
        return {
            "pm25": self.pm25,
            "pm10": self.pm10,
            "co": self.co,
            "no2": self.no2,
            "so2": self.so2,
            "o3": self.o3,
        }

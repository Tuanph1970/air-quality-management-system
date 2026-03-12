"""Station entity for environmental monitoring stations."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class Station:
    """Environmental monitoring station entity.

    Attributes:
        id: Unique identifier (UUID)
        station_code: Station code from external API (e.g., "LSOS_KHIKHO")
        station_name: Display name of the station
        address: Physical address
        latitude: Geographic latitude
        longitude: Geographic longitude
        station_type: Type code (4 = Air quality)
        province_id: Province/city ID
        is_active: Whether station is actively reporting
        metadata: Additional metadata from API
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: str
    station_code: str
    station_name: str
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    station_type: Optional[int] = None
    province_id: Optional[str] = None
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def from_api_data(cls, api_data: Dict[str, Any]) -> "Station":
        """Create station from external API response.

        Args:
            api_data: Station data from external API

        Returns:
            Station entity
        """
        import uuid

        return cls(
            id=str(uuid.uuid4()),
            station_code=api_data.get("stationCode", ""),
            station_name=api_data.get("stationName", ""),
            address=api_data.get("address"),
            latitude=api_data.get("latitude"),
            longitude=api_data.get("longitude"),
            station_type=api_data.get("stationType"),
            province_id=api_data.get("provinceId"),
            is_active=True,
            metadata=api_data,
        )

    def update_from_api(self, api_data: Dict[str, Any]) -> None:
        """Update station from external API data.

        Args:
            api_data: Station data from external API
        """
        self.station_name = api_data.get("stationName", self.station_name)
        self.address = api_data.get("address", self.address)
        self.latitude = api_data.get("latitude", self.latitude)
        self.longitude = api_data.get("longitude", self.longitude)
        self.station_type = api_data.get("stationType", self.station_type)
        self.province_id = api_data.get("provinceId", self.province_id)
        self.metadata = api_data
        self.updated_at = datetime.utcnow()


@dataclass
class AirQualityReading:
    """Air quality reading entity.

    Attributes:
        id: Unique identifier
        station_code: Station code this reading belongs to
        reading_time: When the measurement was taken
        aqi: Air Quality Index
        pm25: PM2.5 concentration (µg/m³)
        pm10: PM10 concentration (µg/m³)
        co: Carbon monoxide concentration
        so2: Sulfur dioxide concentration
        no2: Nitrogen dioxide concentration
        o3: Ozone concentration
        temperature: Temperature (°C)
        humidity: Relative humidity (%)
        created_at: Creation timestamp
    """

    id: str
    station_code: str
    reading_time: datetime
    aqi: Optional[float] = None
    pm25: Optional[float] = None
    pm10: Optional[float] = None
    co: Optional[float] = None
    so2: Optional[float] = None
    no2: Optional[float] = None
    o3: Optional[float] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def from_api_data(
        cls,
        station_code: str,
        reading_data: Dict[str, Any],
    ) -> "AirQualityReading":
        """Create reading from external API response.

        Args:
            station_code: Station code
            reading_data: Reading data from API

        Returns:
            AirQualityReading entity
        """
        import uuid

        data = reading_data.get("data", {})
        reading_time_str = reading_data.get("getTime")

        try:
            reading_time = datetime.fromisoformat(reading_time_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            reading_time = datetime.utcnow()

        return cls(
            id=str(uuid.uuid4()),
            station_code=station_code,
            reading_time=reading_time,
            aqi=data.get("aqi"),
            pm25=data.get("PM2.5"),
            pm10=data.get("PM10"),
            co=data.get("CO"),
            so2=data.get("SO2"),
            no2=data.get("NO2"),
            o3=data.get("O3"),
            temperature=data.get("Temp"),
            humidity=data.get("RH"),
        )

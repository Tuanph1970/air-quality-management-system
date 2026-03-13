"""Fake data seeder for development/testing.

This module provides fake station and AQI data for development
when the external API is unavailable.
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

from src.domain.entities.station import AirQualityReading, Station

logger = logging.getLogger(__name__)


# Fake stations data (based on real Vietnam monitoring stations)
FAKE_STATIONS: List[Dict[str, Any]] = [
    {
        "stationCode": "GLHN_KHINVC",
        "stationName": "Hà Nội: 556 Nguyễn Văn Cừ (KK)",
        "address": "556 Nguyễn Văn Cừ, Long Biên, Hà Nội",
        "latitude": 21.0285,
        "longitude": 105.8477,
        "stationType": 4,
        "provinceId": "01",
    },
    {
        "stationCode": "HN_BKHN_KHIKXQ",
        "stationName": "Hà Nội: Bách Khoa (KK)",
        "address": "Đại học Bách Khoa, Hà Nội",
        "latitude": 21.0069,
        "longitude": 105.8477,
        "stationType": 4,
        "provinceId": "01",
    },
    {
        "stationCode": "HN_CVTX_KHIKXQ",
        "stationName": "Hà Nội: Cầu Giấy (KK)",
        "address": "Cầu Giấy, Hà Nội",
        "latitude": 21.0285,
        "longitude": 105.7965,
        "stationType": 4,
        "provinceId": "01",
    },
    {
        "stationCode": "HCM_THDI_KHIKXQ",
        "stationName": "TP.HCM: Thủ Đức (KK)",
        "address": "Thủ Đức, TP. Hồ Chí Minh",
        "latitude": 10.8539,
        "longitude": 106.7717,
        "stationType": 4,
        "provinceId": "79",
    },
    {
        "stationCode": "LSOS_KHIKHO",
        "stationName": "Khánh Hòa: Vĩnh Hòa - Nha Trang (KK)",
        "address": "Làng trẻ em SOS Nha Trang",
        "latitude": 12.284358,
        "longitude": 109.192524,
        "stationType": 4,
        "provinceId": "56",
    },
]


def create_fake_stations() -> List[Station]:
    """Create fake station entities."""
    stations = []
    for data in FAKE_STATIONS:
        station = Station(
            id=str(uuid.uuid4()),
            station_code=data["stationCode"],
            station_name=data["stationName"],
            address=data["address"],
            latitude=data["latitude"],
            longitude=data["longitude"],
            station_type=data["stationType"],
            province_id=data["provinceId"],
            is_active=True,
            metadata=data,
        )
        stations.append(station)
    return stations


def create_fake_readings(station_codes: List[str], hours: int = 24) -> List[AirQualityReading]:
    """Create fake AQI readings for the last N hours.
    
    Args:
        station_codes: List of station codes to create readings for
        hours: Number of hours of historical data
        
    Returns:
        List of fake readings
    """
    import random
    
    readings = []
    now = datetime.utcnow()
    
    for station_code in station_codes:
        for h in range(hours):
            reading_time = now - timedelta(hours=h)
            
            # Generate realistic AQI values (varies by station)
            base_aqi = random.randint(50, 200)
            
            reading = AirQualityReading(
                id=str(uuid.uuid4()),
                station_code=station_code,
                reading_time=reading_time,
                aqi=base_aqi + random.uniform(-10, 10),
                pm25=base_aqi * 0.7 + random.uniform(-5, 5) if random.random() > 0.3 else None,
                pm10=base_aqi * 0.9 + random.uniform(-10, 10) if random.random() > 0.2 else None,
                co=random.uniform(0.5, 2.0) if random.random() > 0.5 else None,
                so2=random.uniform(0.5, 5.0) if random.random() > 0.6 else None,
                no2=random.uniform(5, 30) if random.random() > 0.4 else None,
                o3=random.uniform(2, 15) if random.random() > 0.5 else None,
                temperature=random.uniform(20, 35) if random.random() > 0.3 else None,
                humidity=random.uniform(40, 90) if random.random() > 0.3 else None,
            )
            readings.append(reading)
    
    return readings

"""Fake data generator for PurpleAir sensors."""
from __future__ import annotations

import random
from datetime import datetime
from typing import Any, Dict, List


class PurpleAirFakeDataGenerator:
    """Generate realistic fake data for PurpleAir sensors.
    
    PurpleAir Flex-Air monitors measure:
    - PM1.0, PM2.5, PM10 (particulate matter)
    - Temperature
    - Humidity
    - Pressure
    - O3 (ozone)
    - NO2 (nitrogen dioxide)
    - CO (carbon monoxide)
    """
    
    # Base levels for different environments
    BASE_LEVELS = {
        "urban": {
            "pm2_5": 35.0, "pm10_0": 60.0, "pm1_0": 25.0,
            "temperature": 25.0, "humidity": 60.0, "pressure": 1013.0,
            "ozone": 0.05, "no2": 0.03, "co": 0.5,
        },
        "suburban": {
            "pm2_5": 20.0, "pm10_0": 40.0, "pm1_0": 15.0,
            "temperature": 23.0, "humidity": 55.0, "pressure": 1015.0,
            "ozone": 0.06, "no2": 0.02, "co": 0.3,
        },
        "rural": {
            "pm2_5": 10.0, "pm10_0": 25.0, "pm1_0": 8.0,
            "temperature": 20.0, "humidity": 50.0, "pressure": 1018.0,
            "ozone": 0.07, "no2": 0.01, "co": 0.2,
        },
    }
    
    def __init__(self, environment: str = "urban", seed: int = None):
        """Initialize generator.
        
        Args:
            environment: Environment type (urban, suburban, rural)
            seed: Optional random seed
        """
        self.environment = environment.lower()
        self.base = self.BASE_LEVELS.get(environment, self.BASE_LEVELS["urban"])
        
        if seed is not None:
            random.seed(seed)
    
    def generate_reading(self) -> Dict[str, Any]:
        """Generate a complete sensor reading.
        
        Returns:
            Dictionary with all sensor measurements
        """
        # Add variability to base levels
        reading = {}
        
        # Particulate matter (µg/m³)
        reading["pm2_5"] = max(0, self.base["pm2_5"] * random.gauss(1.0, 0.3))
        reading["pm10_0"] = max(0, self.base["pm10_0"] * random.gauss(1.0, 0.3))
        reading["pm1_0"] = max(0, self.base["pm1_0"] * random.gauss(1.0, 0.3))
        
        # Ensure PM1 <= PM2.5 <= PM10
        if reading["pm1_0"] > reading["pm2_5"]:
            reading["pm1_0"] = reading["pm2_5"] * 0.8
        if reading["pm2_5"] > reading["pm10_0"]:
            reading["pm2_5"] = reading["pm10_0"] * 0.7
        
        # Environmental
        reading["temperature"] = self.base["temperature"] + random.gauss(0, 5)
        reading["humidity"] = max(0, min(100, self.base["humidity"] + random.gauss(0, 15)))
        reading["pressure"] = self.base["pressure"] + random.gauss(0, 5)
        
        # Gases
        reading["ozone"] = max(0, self.base["ozone"] * random.gauss(1.0, 0.3))
        reading["no2"] = max(0, self.base["no2"] * random.gauss(1.0, 0.3))
        reading["co"] = max(0, self.base["co"] * random.gauss(1.0, 0.3))
        
        # Round values
        for key in reading:
            if key in ("temperature", "humidity", "pressure"):
                reading[key] = round(reading[key], 1)
            elif key in ("ozone", "no2", "co"):
                reading[key] = round(reading[key], 3)
            else:
                reading[key] = round(reading[key], 2)
        
        # Add metadata
        reading["timestamp"] = datetime.utcnow().isoformat()
        reading["environment"] = self.environment
        
        return reading
    
    def generate_sensor_data(
        self,
        sensor_id: int,
        latitude: float,
        longitude: float,
    ) -> Dict[str, Any]:
        """Generate complete sensor data packet.
        
        Args:
            sensor_id: PurpleAir sensor ID
            latitude: Sensor latitude
            longitude: Sensor longitude
            
        Returns:
            Complete sensor data structure
        """
        reading = self.generate_reading()
        
        return {
            "sensor_id": sensor_id,
            "api_key": "fake-api-key",
            "latitude": latitude,
            "longitude": longitude,
            "data": reading,
        }


def generate_fake_sensor_readings(count: int = 5) -> List[Dict[str, Any]]:
    """Generate fake readings for multiple sensors.
    
    Args:
        count: Number of sensors to generate
        
    Returns:
        List of sensor data dictionaries
    """
    generators = [
        PurpleAirFakeDataGenerator("urban"),
        PurpleAirFakeDataGenerator("suburban"),
        PurpleAirFakeDataGenerator("rural"),
    ]
    
    # Sample locations (Hanoi area)
    locations = [
        (21.0285, 105.8542),  # Downtown
        (21.0500, 105.9000),  # Industrial zone
        (20.9500, 105.7500),  # Rural
        (21.0350, 105.8400),  # Traffic area
        (21.0200, 105.8600),  # Government area
    ]
    
    readings = []
    for i in range(count):
        gen = generators[i % len(generators)]
        lat, lng = locations[i % len(locations)]
        sensor_id = 10000 + i  # Fake sensor IDs
        
        data = gen.generate_sensor_data(sensor_id, lat, lng)
        readings.append(data)
    
    return readings

"""Fake data generator for station service.

Generates realistic air quality readings with:
- Diurnal patterns (traffic peaks, industrial activity)
- Station type variations (urban, rural, industrial)
- Pollutant correlations (PM2.5/PM10 ratios, etc.)
- Random noise for realism
"""
from __future__ import annotations

import logging
import math
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


class StationFakeDataGenerator:
    """Generate realistic fake air quality data for stations.
    
    Features:
    - Diurnal patterns (daily cycles)
    - Station type variations
    - Pollutant correlations
    - Configurable pollution levels
    """
    
    # Base pollution levels by station type (µg/m³ unless noted)
    BASE_LEVELS = {
        "URBAN": {
            "PM25": 35.0, "PM10": 60.0, "SO2": 15.0, "NOX": 50.0, "NO2": 40.0,
            "CO": 3.0, "O3": 50.0, "CO2": 450.0,
        },
        "RURAL": {
            "PM25": 15.0, "PM10": 30.0, "SO2": 5.0, "NOX": 15.0, "NO2": 12.0,
            "CO": 1.0, "O3": 70.0, "CO2": 420.0,
        },
        "INDUSTRIAL": {
            "PM25": 60.0, "PM10": 100.0, "SO2": 40.0, "NOX": 80.0, "NO2": 60.0,
            "CO": 8.0, "O3": 40.0, "CO2": 600.0,
        },
        "TRAFFIC": {
            "PM25": 50.0, "PM10": 80.0, "SO2": 10.0, "NOX": 100.0, "NO2": 80.0,
            "CO": 6.0, "O3": 35.0, "CO2": 500.0,
        },
        "GOVERNMENT": {
            "PM25": 25.0, "PM10": 45.0, "SO2": 10.0, "NOX": 35.0, "NO2": 30.0,
            "CO": 2.0, "O3": 55.0, "CO2": 430.0,
        },
        "BACKGROUND": {
            "PM25": 10.0, "PM10": 20.0, "SO2": 3.0, "NOX": 10.0, "NO2": 8.0,
            "CO": 0.5, "O3": 65.0, "CO2": 415.0,
        },
    }
    
    # Diurnal pattern multipliers (hour of day -> multiplier)
    # Traffic peaks at 8am and 6pm
    DIURNAL_TRAFFIC = {
        0: 0.5, 1: 0.4, 2: 0.3, 3: 0.3, 4: 0.3, 5: 0.5,
        6: 0.8, 7: 1.3, 8: 1.8, 9: 1.5, 10: 1.3, 11: 1.2,
        12: 1.1, 13: 1.1, 14: 1.2, 15: 1.3, 16: 1.4, 17: 1.6,
        18: 1.9, 19: 1.5, 20: 1.2, 21: 1.0, 22: 0.8, 23: 0.6,
    }
    
    # Ozone peaks in afternoon (photochemical)
    DIURNAL_O3 = {
        0: 0.5, 1: 0.4, 2: 0.4, 3: 0.4, 4: 0.4, 5: 0.5,
        6: 0.6, 7: 0.7, 8: 0.8, 9: 0.9, 10: 1.1, 11: 1.2,
        12: 1.3, 13: 1.4, 14: 1.5, 15: 1.4, 16: 1.3, 17: 1.1,
        18: 0.9, 19: 0.8, 20: 0.7, 21: 0.6, 22: 0.5, 23: 0.5,
    }
    
    def __init__(
        self,
        station_type: str = "URBAN",
        variability: float = 0.3,
        seed: Optional[int] = None,
    ):
        """Initialize fake data generator.
        
        Args:
            station_type: Type of station (URBAN, RURAL, INDUSTRIAL, etc.)
            variability: Random variability factor (0.0 - 1.0)
            seed: Optional random seed for reproducibility
        """
        self.station_type = station_type.upper()
        self.variability = min(max(variability, 0.1), 0.5)
        
        if seed is not None:
            random.seed(seed)
        
        self.base_levels = self.BASE_LEVELS.get(
            self.station_type, self.BASE_LEVELS["URBAN"]
        )
    
    def get_diurnal_multiplier(self, pollutant: str, hour: int) -> float:
        """Get diurnal pattern multiplier for pollutant at given hour.
        
        Args:
            pollutant: Pollutant type
            hour: Hour of day (0-23)
            
        Returns:
            Multiplier value
        """
        if pollutant in ("O3", "OZONE"):
            pattern = self.DIURNAL_O3
        else:
            pattern = self.DIURNAL_TRAFFIC
        
        return pattern.get(hour, 1.0)
    
    def generate_reading(
        self,
        pollutant: str,
        hour: Optional[int] = None,
        include_noise: bool = True,
    ) -> float:
        """Generate a realistic reading for a pollutant.
        
        Args:
            pollutant: Pollutant type (PM25, PM10, SO2, etc.)
            hour: Hour of day (defaults to current hour)
            include_noise: Whether to add random noise
            
        Returns:
            Generated reading value
        """
        if hour is None:
            hour = datetime.now().hour
        
        # Get base level
        base = self.base_levels.get(pollutant.upper(), 25.0)
        
        # Apply diurnal pattern
        diurnal = self.get_diurnal_multiplier(pollutant, hour)
        value = base * diurnal
        
        # Add random noise
        if include_noise:
            noise = random.gauss(1.0, self.variability / 3)
            value *= noise
        
        # Ensure non-negative
        value = max(0.0, value)
        
        return round(value, 2)
    
    def generate_all_readings(
        self,
        hour: Optional[int] = None,
    ) -> Dict[str, float]:
        """Generate readings for all pollutants.
        
        Args:
            hour: Hour of day (defaults to current hour)
            
        Returns:
            Dictionary of pollutant -> value
        """
        readings = {}
        
        for pollutant in self.base_levels.keys():
            readings[pollutant] = self.generate_reading(pollutant, hour)
        
        # Ensure PM2.5 <= PM10 (with small tolerance)
        if readings.get("PM25", 0) > readings.get("PM10", 100) * 1.05:
            readings["PM25"] = readings["PM10"] * 0.9
        
        return readings
    
    def generate_time_series(
        self,
        num_hours: int = 24,
        start_hour: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Generate a time series of readings.
        
        Args:
            num_hours: Number of hours to generate
            start_hour: Starting hour (defaults to 0)
            
        Returns:
            List of {hour, readings} dictionaries
        """
        if start_hour is None:
            start_hour = 0
        
        series = []
        for i in range(num_hours):
            hour = (start_hour + i) % 24
            readings = self.generate_all_readings(hour)
            series.append({
                "hour": hour,
                "readings": readings,
            })
        
        return series


class StationFakeDataSimulator:
    """Simulate continuous fake data generation for multiple stations.
    
    This simulator can:
    - Generate data for multiple stations
    - Submit readings via HTTP API
    - Run continuously in background
    """
    
    def __init__(
        self,
        api_base_url: str = "http://localhost:8007",
        use_fake_stations: bool = True,
    ):
        """Initialize simulator.
        
        Args:
            api_base_url: Station service API base URL
            use_fake_stations: Whether to create fake stations
        """
        self.api_base_url = api_base_url.rstrip("/")
        self.use_fake_stations = use_fake_stations
        self.generators: Dict[UUID, StationFakeDataGenerator] = {}
        self.station_ids: List[UUID] = []
    
    async def initialize_stations(
        self,
        station_configs: Optional[List[Dict[str, Any]]] = None,
    ) -> List[UUID]:
        """Initialize stations for simulation.
        
        Args:
            station_configs: Optional list of station configurations
            
        Returns:
            List of station IDs
        """
        import httpx
        
        if station_configs is None:
            # Default fake stations
            station_configs = [
                {"name": "Downtown Urban Station", "station_code": "FAKE-URBAN-001", "station_type": "URBAN", "latitude": 21.0285, "longitude": 105.8542},
                {"name": "Industrial Zone Station", "station_code": "FAKE-IND-001", "station_type": "INDUSTRIAL", "latitude": 21.0500, "longitude": 105.9000},
                {"name": "Rural Background Station", "station_code": "FAKE-RURAL-001", "station_type": "RURAL", "latitude": 20.9500, "longitude": 105.7500},
                {"name": "Traffic Hotspot Station", "station_code": "FAKE-TRAFFIC-001", "station_type": "TRAFFIC", "latitude": 21.0350, "longitude": 105.8400},
                {"name": "Government Monitoring Station", "station_code": "FAKE-GOV-001", "station_type": "GOVERNMENT", "latitude": 21.0200, "longitude": 105.8600},
            ]
        
        station_ids = []
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for config in station_configs:
                try:
                    # Create station
                    response = await client.post(
                        f"{self.api_base_url}/api/v1/stations",
                        json=config,
                    )
                    
                    if response.status_code == 201:
                        data = response.json()
                        station_id = UUID(data["id"])
                        station_ids.append(station_id)
                        
                        # Create generator for this station
                        self.generators[station_id] = StationFakeDataGenerator(
                            station_type=config["station_type"]
                        )
                        
                        logger.info(f"Created fake station: {config['name']}")
                    elif response.status_code == 409:
                        # Station already exists, get it by code
                        response = await client.get(
                            f"{self.api_base_url}/api/v1/stations/code/{config['station_code']}"
                        )
                        if response.status_code == 200:
                            data = response.json()
                            station_id = UUID(data["id"])
                            station_ids.append(station_id)
                            self.generators[station_id] = StationFakeDataGenerator(
                                station_type=config["station_type"]
                            )
                            logger.info(f"Using existing station: {config['name']}")
                    else:
                        logger.warning(f"Failed to create station: {response.text}")
                        
                except Exception as e:
                    logger.error(f"Error creating station: {e}")
        
        self.station_ids = station_ids
        return station_ids
    
    async def submit_readings(
        self,
        station_id: UUID,
        readings: Dict[str, float],
        source: str = "FAKE",
    ) -> bool:
        """Submit readings for a station.
        
        Args:
            station_id: Station UUID
            readings: Pollutant readings
            source: Data source identifier
            
        Returns:
            True if successful
        """
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.api_base_url}/api/v1/stations/{station_id}/record-readings",
                    json={
                        "readings": readings,
                        "source": source,
                    },
                )
                
                if response.status_code in (200, 201):
                    logger.debug(f"Submitted readings for station {station_id}")
                    return True
                else:
                    logger.warning(f"Failed to submit readings: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error submitting readings: {e}")
            return False
    
    async def simulate_cycle(self) -> Dict[UUID, bool]:
        """Simulate one cycle of data collection for all stations.
        
        Returns:
            Dictionary of station_id -> success
        """
        results = {}
        
        for station_id in self.station_ids:
            generator = self.generators.get(station_id)
            if not generator:
                continue
            
            # Generate readings
            readings = generator.generate_all_readings()
            
            # Submit readings
            success = await self.submit_readings(station_id, readings)
            results[station_id] = success
        
        return results
    
    async def run_continuous(
        self,
        interval_seconds: int = 60,
        max_cycles: Optional[int] = None,
    ) -> None:
        """Run continuous simulation.
        
        Args:
            interval_seconds: Time between data submissions
            max_cycles: Maximum number of cycles (None for infinite)
        """
        import asyncio
        
        logger.info(f"Starting continuous simulation (interval={interval_seconds}s)")
        
        cycle = 0
        while max_cycles is None or cycle < max_cycles:
            results = await self.simulate_cycle()
            
            success_count = sum(1 for v in results.values() if v)
            logger.info(
                f"Simulation cycle {cycle + 1}: {success_count}/{len(results)} stations successful"
            )
            
            cycle += 1
            
            if max_cycles is None or cycle < max_cycles:
                await asyncio.sleep(interval_seconds)
        
        logger.info(f"Simulation completed after {cycle} cycles")


# CLI entry point
if __name__ == "__main__":
    import asyncio
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    
    async def main():
        simulator = StationFakeDataSimulator(
            api_base_url="http://localhost:8007",
        )
        
        # Initialize stations
        await simulator.initialize_stations()
        
        # Run 10 cycles for demo
        await simulator.run_continuous(interval_seconds=30, max_cycles=10)
    
    asyncio.run(main())

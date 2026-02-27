"""Air Quality application service.

Orchestrates AQI-related use cases:
- Get current AQI for a location
- Get map data for visualization
- Get AQI forecast

**Application layer**: Coordinates between domain services, repositories,
and infrastructure. Contains no business rules.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, AsyncGenerator

from ...config import settings
from ...domain.services.aqi_calculator import AQICalculator, AQIResult
from ...domain.services.prediction_service import PredictionService, SensorDataPoint
from ...domain.value_objects.aqi_category import get_category_for_aqi
from ..queries.get_current_aqi_query import GetCurrentAQIQuery, GetCurrentAQIResult
from ..queries.get_forecast_query import GetForecastQuery, GetForecastResult, ForecastDataPoint
from ..queries.get_map_data_query import GetMapDataQuery, GetMapDataResult, MapGridCell
from ..infrastructure.cache.redis_cache import RedisCache
from ..infrastructure.external.google_maps_client import GoogleMapsClient

logger = logging.getLogger(__name__)


class AirQualityApplicationService:
    """Application service for air quality operations.

    Coordinates between:
    - AQI Calculator (domain service)
    - Prediction Service (domain service)
    - Redis Cache (infrastructure)
    - Google Maps API (infrastructure)
    - Sensor repositories (infrastructure)
    """

    def __init__(
        self,
        aqi_calculator: AQICalculator,
        prediction_service: PredictionService,
        cache: RedisCache,
        google_client: GoogleMapsClient,
        sensor_client: Optional[Any] = None,
    ):
        """Initialize the application service.

        Parameters
        ----------
        aqi_calculator:
            Domain service for AQI calculations
        prediction_service:
            Domain service for forecasting
        cache:
            Redis cache for data caching
        google_client:
            Google Maps API client
        sensor_client:
            Sensor Service client (optional)
        """
        self.aqi_calculator = aqi_calculator
        self.prediction_service = prediction_service
        self.cache = cache
        self.google_client = google_client
        self.sensor_client = sensor_client

    async def get_current_aqi(
        self,
        query: GetCurrentAQIQuery,
    ) -> GetCurrentAQIResult:
        """Get current AQI for a location.

        Flow:
        1. Check cache for recent data
        2. If not cached, fetch from sensor repository
        3. Calculate AQI using domain service
        4. Cache the result
        5. Return formatted result

        Parameters
        ----------
        query:
            Query with location and options

        Returns
        -------
        GetCurrentAQIResult
            Current AQI data with category and health messages
        """
        # Try cache first
        cached = await self.cache.get_aqi(
            query.latitude,
            query.longitude,
            query.radius_km,
        )
        if cached:
            logger.debug("Cache hit for AQI at (%.3f, %.3f)", query.latitude, query.longitude)
            return self._result_from_cache(cached)

        # Fetch sensor data from repository
        pollutants = await self._get_pollutants_for_location(
            query.latitude,
            query.longitude,
            query.radius_km,
        )

        if not pollutants:
            # Return default/empty result
            return self._empty_result(query.latitude, query.longitude)

        # Calculate AQI
        aqi_result = self.aqi_calculator.calculate_composite_aqi(pollutants)

        # Build result
        result = GetCurrentAQIResult(
            location_lat=query.latitude,
            location_lng=query.longitude,
            aqi_value=aqi_result.aqi_value,
            level=aqi_result.level.value,
            category=aqi_result.category,
            color=aqi_result.color,
            dominant_pollutant=aqi_result.dominant_pollutant,
            pollutants=self._format_pollutants(pollutants, query.include_pollutants),
            health_message=aqi_result.health_message,
            caution_message=aqi_result.caution_message,
            timestamp=datetime.utcnow().isoformat(),
            data_source="sensor",
        )

        # Cache the result
        await self.cache.set_aqi(
            query.latitude,
            query.longitude,
            query.radius_km,
            self._result_to_dict(result),
        )

        return result

    async def get_map_data(
        self,
        query: GetMapDataQuery,
    ) -> GetMapDataResult:
        """Get aggregated AQI data for map visualization.

        Flow:
        1. Check cache for map data
        2. If not cached, query sensors in bounding box
        3. Aggregate into grid cells
        4. Cache the result
        5. Return grid data

        Parameters
        ----------
        query:
            Query with bounds and zoom level

        Returns
        -------
        GetMapDataResult
            Grid cells with AQI data for rendering
        """
        # Try cache first
        cached = await self.cache.get_map_data(
            query.min_lat,
            query.min_lng,
            query.max_lat,
            query.max_lng,
            query.zoom_level,
        )
        if cached:
            logger.debug("Cache hit for map data at zoom %d", query.zoom_level)
            return self._map_result_from_cache(cached, query)

        # Generate grid cells
        grid_cells = await self._generate_grid_cells(query)

        # Build result
        result = GetMapDataResult(
            grid_cells=grid_cells,
            min_lat=query.min_lat,
            min_lng=query.min_lng,
            max_lat=query.max_lat,
            max_lng=query.max_lng,
            zoom_level=query.zoom_level,
            generated_at=datetime.utcnow().isoformat(),
        )

        # Cache the result
        await self.cache.set_map_data(
            query.min_lat,
            query.min_lng,
            query.max_lat,
            query.max_lng,
            query.zoom_level,
            [self._grid_cell_to_dict(cell) for cell in grid_cells],
        )

        return result

    async def get_forecast(
        self,
        query: GetForecastQuery,
    ) -> GetForecastResult:
        """Get AQI forecast for a location.

        Flow:
        1. Check cache for forecast
        2. If not cached, get historical sensor data
        3. Run prediction service
        4. Cache the result
        5. Return forecast

        Parameters
        ----------
        query:
            Query with location and forecast options

        Returns
        -------
        GetForecastResult
            Forecast data points with confidence levels
        """
        # Try cache first
        cached = await self.cache.get_forecast(
            query.latitude,
            query.longitude,
            query.hours,
        )
        if cached:
            logger.debug("Cache hit for forecast at (%.3f, %.3f)", query.latitude, query.longitude)
            return self._forecast_result_from_cache(cached)

        # Get historical sensor data
        sensor_data = await self._get_historical_sensor_data(
            query.latitude,
            query.longitude,
        )

        # Generate forecast
        forecast = self.prediction_service.predict_next_hours(
            sensor_data=sensor_data,
            hours=query.hours,
            interval_hours=query.interval_hours,
        )

        # Get current AQI for baseline
        current_aqi = 0
        if sensor_data:
            current_aqi = sensor_data[-1].aqi

        # Build forecast data points
        forecast_points = []
        for dp in forecast.data_points:
            category = get_category_for_aqi(dp.predicted_aqi)
            forecast_points.append(
                ForecastDataPoint(
                    timestamp=dp.timestamp,
                    predicted_aqi=dp.predicted_aqi,
                    min_aqi=dp.min_aqi,
                    max_aqi=dp.max_aqi,
                    confidence=dp.confidence,
                    trend=dp.trend,
                    level=category.level.value,
                )
            )

        # Build result
        summary = self.prediction_service.get_forecast_summary(forecast)
        result = GetForecastResult(
            location_lat=query.latitude,
            location_lng=query.longitude,
            generated_at=datetime.utcnow(),
            forecast_hours=query.hours,
            current_aqi=current_aqi,
            data_points=forecast_points,
            average_aqi=forecast.average_aqi,
            max_aqi=forecast.max_aqi,
            overall_trend=forecast.overall_trend,
            health_recommendation=summary.get("recommendation", ""),
        )

        # Cache the result
        await self.cache.set_forecast(
            query.latitude,
            query.longitude,
            query.hours,
            self._forecast_to_dict(result),
        )

        return result

    # =====================================================================
    # Helper Methods
    # =====================================================================

    async def _get_pollutants_for_location(
        self,
        lat: float,
        lng: float,
        radius_km: float,
    ) -> Dict[str, float]:
        """Get pollutant concentrations for a location.

        Aggregates data from nearby sensors via Sensor Service API.
        """
        if not self.sensor_client:
            # Return sample data for development
            return {
                "pm25": 35.0,
                "pm10": 50.0,
                "o3": 60.0,
                "no2": 30.0,
            }

        try:
            # Query Sensor Service for nearby readings
            readings = await self.sensor_client.get_recent_readings(
                lat, lng, radius_km
            )

            if not readings:
                return {}

            # Aggregate readings (average)
            pollutants: Dict[str, List[float]] = {}
            for reading in readings:
                for pollutant, value in [
                    ("pm25", reading.pm25),
                    ("pm10", reading.pm10),
                    ("co", reading.co),
                    ("no2", reading.no2),
                    ("so2", reading.so2),
                    ("o3", reading.o3),
                ]:
                    if value > 0:
                        if pollutant not in pollutants:
                            pollutants[pollutant] = []
                        pollutants[pollutant].append(value)

            return {k: sum(v) / len(v) for k, v in pollutants.items() if v}

        except Exception as e:
            logger.warning(f"Error fetching sensor data: {e}")
            return {}

    async def _generate_grid_cells(
        self,
        query: GetMapDataQuery,
    ) -> List[MapGridCell]:
        """Generate grid cells for map visualization."""
        cells = []

        # Calculate grid dimensions
        lat_step = query.grid_size or 0.1
        lng_step = query.grid_size or 0.1

        lat = query.min_lat
        while lat <= query.max_lat:
            lng = query.min_lng
            while lng <= query.max_lng:
                # Get AQI for grid center
                pollutants = await self._get_pollutants_for_location(
                    lat, lng, lat_step * 50  # Approximate radius
                )

                if pollutants:
                    aqi_result = self.aqi_calculator.calculate_composite_aqi(pollutants)
                    category = get_category_for_aqi(aqi_result.aqi_value)

                    cells.append(
                        MapGridCell(
                            lat=lat,
                            lng=lng,
                            aqi_value=aqi_result.aqi_value,
                            level=category.level.value,
                            color=category.color_hex,
                            sensor_count=1,  # Would be calculated from actual data
                            last_updated=datetime.utcnow().isoformat(),
                        )
                    )

                lng += lng_step
            lat += lat_step

        return cells

    async def _get_historical_sensor_data(
        self,
        lat: float,
        lng: float,
    ) -> List[SensorDataPoint]:
        """Get historical sensor data for forecasting."""
        if not self.sensor_repository:
            # Generate sample data for development
            now = datetime.utcnow()
            return [
                SensorDataPoint(
                    timestamp=now - timedelta(hours=i),
                    pollutants={"pm25": 30 + i * 2, "pm10": 50},
                    aqi=50 + i * 3,
                )
                for i in range(12, 0, -1)
            ]

        # Query repository for historical data
        return await self.sensor_repository.get_historical(lat, lng, hours=24)

    def _empty_result(self, lat: float, lng: float) -> GetCurrentAQIResult:
        """Create an empty result when no data is available."""
        return GetCurrentAQIResult(
            location_lat=lat,
            location_lng=lng,
            aqi_value=0,
            level="GOOD",
            category="Good",
            color="#00E400",
            dominant_pollutant="none",
            pollutants={},
            health_message="No air quality data available for this location.",
            caution_message="None",
            timestamp=datetime.utcnow().isoformat(),
            data_source="none",
        )

    def _format_pollutants(
        self,
        pollutants: Dict[str, float],
        include_aqi: bool = True,
    ) -> Dict:
        """Format pollutants for response."""
        result = {"concentrations": pollutants}
        if include_aqi:
            result["individual_aqis"] = self.aqi_calculator.get_all_pollutant_aqis(pollutants)
        return result

    def _result_to_dict(self, result: GetCurrentAQIResult) -> Dict:
        """Convert result to dictionary for caching."""
        return {
            "location_lat": result.location_lat,
            "location_lng": result.location_lng,
            "aqi_value": result.aqi_value,
            "level": result.level,
            "category": result.category,
            "color": result.color,
            "dominant_pollutant": result.dominant_pollutant,
            "pollutants": result.pollutants,
            "health_message": result.health_message,
            "caution_message": result.caution_message,
            "timestamp": result.timestamp,
            "data_source": result.data_source,
        }

    def _result_from_cache(self, cached: Dict) -> GetCurrentAQIResult:
        """Create result from cached data."""
        return GetCurrentAQIResult(
            location_lat=cached["location_lat"],
            location_lng=cached["location_lng"],
            aqi_value=cached["aqi_value"],
            level=cached["level"],
            category=cached["category"],
            color=cached["color"],
            dominant_pollutant=cached["dominant_pollutant"],
            pollutants=cached.get("pollutants", {}),
            health_message=cached.get("health_message", ""),
            caution_message=cached.get("caution_message", ""),
            timestamp=cached.get("timestamp", ""),
            data_source=cached.get("data_source", "cache"),
        )

    def _map_result_from_cache(
        self,
        cached: List[Dict],
        query: GetMapDataQuery,
    ) -> GetMapDataResult:
        """Create map result from cached data."""
        cells = [
            MapGridCell(
                lat=cell["lat"],
                lng=cell["lng"],
                aqi_value=cell["aqi_value"],
                level=cell["level"],
                color=cell["color"],
                sensor_count=cell.get("sensor_count", 0),
                last_updated=cell.get("last_updated", ""),
            )
            for cell in cached
        ]
        return GetMapDataResult(
            grid_cells=cells,
            min_lat=query.min_lat,
            min_lng=query.min_lng,
            max_lat=query.max_lat,
            max_lng=query.max_lng,
            zoom_level=query.zoom_level,
            generated_at=datetime.utcnow().isoformat(),
        )

    def _grid_cell_to_dict(self, cell: MapGridCell) -> Dict:
        """Convert grid cell to dictionary for caching."""
        return {
            "lat": cell.lat,
            "lng": cell.lng,
            "aqi_value": cell.aqi_value,
            "level": cell.level,
            "color": cell.color,
            "sensor_count": cell.sensor_count,
            "last_updated": cell.last_updated,
        }

    def _forecast_to_dict(self, result: GetForecastResult) -> Dict:
        """Convert forecast to dictionary for caching."""
        return {
            "location_lat": result.location_lat,
            "location_lng": result.location_lng,
            "generated_at": result.generated_at.isoformat(),
            "forecast_hours": result.forecast_hours,
            "current_aqi": result.current_aqi,
            "average_aqi": result.average_aqi,
            "max_aqi": result.max_aqi,
            "overall_trend": result.overall_trend,
            "health_recommendation": result.health_recommendation,
            "data_points": [
                {
                    "timestamp": dp.timestamp.isoformat(),
                    "predicted_aqi": dp.predicted_aqi,
                    "min_aqi": dp.min_aqi,
                    "max_aqi": dp.max_aqi,
                    "confidence": dp.confidence,
                    "trend": dp.trend,
                    "level": dp.level,
                }
                for dp in result.data_points
            ],
        }

    def _forecast_result_from_cache(self, cached: Dict) -> GetForecastResult:
        """Create forecast result from cached data."""
        from datetime import datetime

        return GetForecastResult(
            location_lat=cached["location_lat"],
            location_lng=cached["location_lng"],
            generated_at=datetime.fromisoformat(cached["generated_at"]),
            forecast_hours=cached["forecast_hours"],
            current_aqi=cached.get("current_aqi", 0),
            average_aqi=cached.get("average_aqi", 0),
            max_aqi=cached.get("max_aqi", 0),
            overall_trend=cached.get("overall_trend", "STABLE"),
            health_recommendation=cached.get("health_recommendation", ""),
            data_points=[
                ForecastDataPoint(
                    timestamp=datetime.fromisoformat(dp["timestamp"]),
                    predicted_aqi=dp["predicted_aqi"],
                    min_aqi=dp["min_aqi"],
                    max_aqi=dp["max_aqi"],
                    confidence=dp["confidence"],
                    trend=dp["trend"],
                    level=dp["level"],
                )
                for dp in cached.get("data_points", [])
            ],
        )


# =============================================================================
# Dependency Injection for FastAPI
# =============================================================================


def get_air_quality_service() -> AsyncGenerator[AirQualityApplicationService, None]:
    """FastAPI dependency that yields an AirQualityApplicationService instance.

    Usage::

        @router.get("/aqi/current")
        async def get_current_aqi(
            service: AirQualityApplicationService = Depends(get_air_quality_service)
        ):
            ...
    """
    from ...infrastructure.cache.redis_cache import RedisCache
    from ...infrastructure.external.google_maps_client import GoogleMapsClient
    from ...infrastructure.external.sensor_service_client import SensorServiceClient

    async def _generate():
        # Initialize infrastructure
        cache = RedisCache()
        await cache.connect()

        google_client = GoogleMapsClient()
        await google_client.connect()

        sensor_client = SensorServiceClient()
        await sensor_client.connect()

        # Initialize domain services
        aqi_calculator = AQICalculator()
        prediction_service = PredictionService()

        service = AirQualityApplicationService(
            aqi_calculator=aqi_calculator,
            prediction_service=prediction_service,
            cache=cache,
            google_client=google_client,
            sensor_client=sensor_client,
        )
        try:
            yield service
        finally:
            await cache.close()
            await google_client.close()
            await sensor_client.close()

    return _generate()

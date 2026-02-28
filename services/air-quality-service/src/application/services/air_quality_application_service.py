"""Air Quality application service.

Orchestrates AQI-related use cases:
- Get current AQI for a location
- Get map data for visualization
- Get AQI forecast
- Data fusion (sensor + satellite)
- Cross-validation of sensors
- Calibration model management

**Application layer**: Coordinates between domain services, repositories,
and infrastructure. Contains no business rules.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, AsyncGenerator
from uuid import UUID

from ...config import settings
from ...domain.services.aqi_calculator import AQICalculator, AQIResult
from ...domain.services.calibration_model import CalibrationModel
from ...domain.services.cross_validator import CrossValidationService
from ...domain.services.data_fusion import DataFusionService
from ...domain.services.prediction_service import PredictionService, SensorDataPoint
from ...domain.value_objects.aqi_category import get_category_for_aqi
from ..queries.get_current_aqi_query import GetCurrentAQIQuery, GetCurrentAQIResult
from ..queries.get_forecast_query import GetForecastQuery, GetForecastResult, ForecastDataPoint
from ..queries.get_map_data_query import GetMapDataQuery, GetMapDataResult, MapGridCell

logger = logging.getLogger(__name__)


class AirQualityApplicationService:
    """Application service for air quality operations.

    Coordinates between:
    - AQI Calculator (domain service)
    - Prediction Service (domain service)
    - Calibration Model (domain service)
    - Cross Validation Service (domain service)
    - Data Fusion Service (domain service)
    - Redis Cache (infrastructure)
    - Google Maps API (infrastructure)
    - Sensor Service client (infrastructure)
    """

    def __init__(
        self,
        aqi_calculator: AQICalculator,
        prediction_service: PredictionService,
        cache: Any,
        google_client: Any,
        sensor_client: Optional[Any] = None,
        calibration_model: Optional[CalibrationModel] = None,
        cross_validator: Optional[CrossValidationService] = None,
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
        calibration_model:
            ML calibration model (optional)
        cross_validator:
            Cross-validation service (optional)
        """
        self.aqi_calculator = aqi_calculator
        self.prediction_service = prediction_service
        self.cache = cache
        self.google_client = google_client
        self.sensor_client = sensor_client
        self.calibration_model = calibration_model or CalibrationModel()
        self.cross_validator = cross_validator or CrossValidationService()

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
    # Data Fusion Use Cases
    # =====================================================================

    async def get_fused_data(
        self,
        bbox: Dict[str, float],
        timestamp: Optional[datetime] = None,
    ) -> List[Dict]:
        """Get fused air quality data for a bounding box.

        Fetches nearby sensor readings and cached satellite data, then
        runs data fusion with calibration.

        Parameters
        ----------
        bbox:
            Bounding box with keys: north, south, east, west
        timestamp:
            Observation timestamp (defaults to now)

        Returns
        -------
        list[dict]
            Fused data points with calibrated values and confidence.
        """
        ts = timestamp or datetime.utcnow()
        center_lat = (bbox["north"] + bbox["south"]) / 2
        center_lon = (bbox["east"] + bbox["west"]) / 2

        # Fetch sensor readings
        sensor_readings = await self._fetch_sensor_readings(
            center_lat, center_lon, radius_km=50.0
        )

        # Fetch cached satellite data
        satellite_data = await self._fetch_satellite_cache(center_lat, center_lon)

        # Run fusion
        fusion_service = DataFusionService(self.calibration_model)
        fused_points = fusion_service.fuse_data(
            sensor_readings=sensor_readings,
            satellite_data=satellite_data,
            timestamp=ts,
        )

        # Filter to bounding box
        results = []
        for point in fused_points:
            if (
                bbox["south"] <= point.location.latitude <= bbox["north"]
                and bbox["west"] <= point.location.longitude <= bbox["east"]
            ):
                results.append({
                    "latitude": point.location.latitude,
                    "longitude": point.location.longitude,
                    "timestamp": ts.isoformat(),
                    "sensor_pm25": point.sensor_pm25,
                    "sensor_pm10": point.sensor_pm10,
                    "satellite_aod": point.satellite_aod,
                    "fused_pm25": point.fused_pm25,
                    "fused_pm10": point.fused_pm10,
                    "fused_aqi": point.fused_aqi,
                    "confidence": point.confidence,
                    "data_sources": point.data_sources,
                })

        return results

    async def trigger_fusion(self) -> int:
        """Manually trigger data fusion for the current time.

        Returns
        -------
        int
            Number of data points fused.
        """
        ts = datetime.utcnow()

        # Get all active sensors
        sensor_readings = await self._fetch_sensor_readings(
            latitude=0, longitude=0, radius_km=1000.0
        )

        if not sensor_readings:
            return 0

        # Get satellite data from cache
        satellite_data = await self._fetch_satellite_cache(0, 0)

        # Run fusion
        fusion_service = DataFusionService(self.calibration_model)
        fused_points = fusion_service.fuse_data(
            sensor_readings=sensor_readings,
            satellite_data=satellite_data,
            timestamp=ts,
        )

        # Cache fused results
        for point in fused_points:
            if point.fused_aqi is not None and self.cache:
                aqi_data = {
                    "location_lat": point.location.latitude,
                    "location_lng": point.location.longitude,
                    "aqi_value": point.fused_aqi,
                    "fused_pm25": point.fused_pm25,
                    "fused_pm10": point.fused_pm10,
                    "confidence": point.confidence,
                    "data_sources": point.data_sources,
                    "timestamp": ts.isoformat(),
                }
                await self.cache.set_aqi(
                    point.location.latitude,
                    point.location.longitude,
                    10.0,
                    aqi_data,
                )

        return len(fused_points)

    async def get_fused_map_data(self, bbox: Dict[str, float]) -> Dict:
        """Get fused data formatted for map visualization.

        Parameters
        ----------
        bbox:
            Bounding box with keys: north, south, east, west

        Returns
        -------
        dict
            Map visualization data with grid cells.
        """
        fused_data = await self.get_fused_data(bbox)

        grid_cells = []
        for point in fused_data:
            if point.get("fused_aqi") is not None:
                category = get_category_for_aqi(point["fused_aqi"])
                grid_cells.append({
                    "lat": point["latitude"],
                    "lng": point["longitude"],
                    "aqi_value": point["fused_aqi"],
                    "level": category.level.value,
                    "color": category.color_hex,
                    "confidence": point["confidence"],
                    "data_sources": point["data_sources"],
                    "fused_pm25": point.get("fused_pm25"),
                })

        return {
            "grid_cells": grid_cells,
            "total": len(grid_cells),
            "bbox": bbox,
            "generated_at": datetime.utcnow().isoformat(),
        }

    # =====================================================================
    # Cross-Validation Use Cases
    # =====================================================================

    async def get_validation_report(self) -> Dict:
        """Get cross-validation report for all sensors.

        Returns
        -------
        dict
            Validation report with per-sensor results and summary.
        """
        # Get active sensors
        sensors = await self._get_active_sensors()

        sensor_results = []
        for sensor in sensors:
            sensor_id = sensor.get("sensor_id", sensor.get("id", ""))
            result = await self.get_sensor_validation(UUID(sensor_id) if sensor_id else None)
            if result:
                sensor_results.append(result)

        valid = [s for s in sensor_results if s.get("is_valid", False)]
        correlations = [s["correlation"] for s in sensor_results if "correlation" in s]
        biases = [s["bias"] for s in sensor_results if "bias" in s]

        return {
            "total_sensors": len(sensor_results),
            "valid_sensors": len(valid),
            "invalid_sensors": len(sensor_results) - len(valid),
            "average_correlation": (
                sum(correlations) / len(correlations) if correlations else 0.0
            ),
            "average_bias": (
                sum(biases) / len(biases) if biases else 0.0
            ),
            "sensors": sensor_results,
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def get_sensor_validation(
        self, sensor_id: Optional[UUID]
    ) -> Optional[Dict]:
        """Get validation status for a specific sensor.

        Parameters
        ----------
        sensor_id:
            Sensor UUID

        Returns
        -------
        dict or None
            Validation metrics or None if sensor not found.
        """
        if not sensor_id:
            return None

        # Get sensor readings
        sensor_values = []
        satellite_values = []

        if self.sensor_client:
            try:
                end = datetime.utcnow()
                start = end - timedelta(days=7)
                readings = await self.sensor_client.get_sensor_readings(
                    str(sensor_id), start, end, limit=100
                )

                for reading in readings:
                    if reading.pm25 > 0:
                        sensor_values.append(reading.pm25)
                        # Look up satellite value from cache
                        cached = await self.cache.get_aqi(
                            reading.latitude, reading.longitude, 10.0
                        )
                        if cached and cached.get("fused_pm25") is not None:
                            satellite_values.append(cached["fused_pm25"])
                        else:
                            # Remove the sensor value too to keep arrays aligned
                            sensor_values.pop()
            except Exception as e:
                logger.warning("Error fetching sensor data for validation: %s", e)

        if len(sensor_values) < 3:
            return {
                "sensor_id": str(sensor_id),
                "sample_count": len(sensor_values),
                "correlation": 0.0,
                "bias": 0.0,
                "rmse": 0.0,
                "mae": 0.0,
                "is_valid": False,
                "status": "insufficient_data",
            }

        result = self.cross_validator.validate_sensor(
            sensor_id=sensor_id,
            sensor_values=sensor_values,
            satellite_values=satellite_values,
        )

        return {
            "sensor_id": str(result.sensor_id),
            "sample_count": result.sample_count,
            "correlation": round(result.correlation, 4),
            "bias": round(result.bias, 2),
            "rmse": round(result.rmse, 2),
            "mae": round(result.mae, 2),
            "is_valid": result.is_valid,
            "status": result.status,
        }

    async def run_validation(self) -> int:
        """Trigger cross-validation for all active sensors.

        Returns
        -------
        int
            Number of sensors validated.
        """
        sensors = await self._get_active_sensors()
        count = 0

        for sensor in sensors:
            sensor_id = sensor.get("sensor_id", sensor.get("id", ""))
            if sensor_id:
                try:
                    await self.get_sensor_validation(UUID(sensor_id))
                    count += 1
                except Exception as e:
                    logger.warning("Validation failed for sensor %s: %s", sensor_id, e)

        return count

    # =====================================================================
    # Calibration Use Cases
    # =====================================================================

    async def get_calibration_status(self) -> Dict:
        """Get calibration model status.

        Returns
        -------
        dict
            Model status including training state and feature names.
        """
        model_exists = os.path.exists(self.calibration_model.model_path)
        last_trained = None

        if model_exists:
            try:
                mtime = os.path.getmtime(self.calibration_model.model_path)
                last_trained = datetime.fromtimestamp(mtime).isoformat()
            except OSError:
                pass

        return {
            "is_trained": self.calibration_model.is_trained,
            "model_path": self.calibration_model.model_path,
            "feature_names": CalibrationModel.FEATURE_NAMES,
            "last_trained": last_trained,
        }

    async def get_calibration_metrics(self) -> Dict:
        """Get calibration model performance metrics.

        Evaluates the model on recent matched sensor-satellite data.

        Returns
        -------
        dict
            R-squared, RMSE, MAE, bias, and feature importance.
        """
        if not self.calibration_model.is_trained:
            return {
                "r_squared": 0.0,
                "rmse": 0.0,
                "mae": 0.0,
                "bias": 0.0,
                "feature_importance": {},
            }

        # Get evaluation data
        test_data = await self._get_training_pairs(days=7)
        if len(test_data) < 3:
            return {
                "r_squared": 0.0,
                "rmse": 0.0,
                "mae": 0.0,
                "bias": 0.0,
                "feature_importance": {},
            }

        metrics = self.calibration_model.evaluate(test_data)

        # Get feature importance from the model
        importance = {}
        if hasattr(self.calibration_model.model, "feature_importances_"):
            importance = dict(
                zip(
                    CalibrationModel.FEATURE_NAMES,
                    [float(v) for v in self.calibration_model.model.feature_importances_],
                )
            )

        return {
            "r_squared": round(metrics.r_squared, 4),
            "rmse": round(metrics.rmse, 2),
            "mae": round(metrics.mae, 2),
            "bias": round(metrics.bias, 2),
            "feature_importance": importance,
        }

    async def retrain_calibration(
        self, days: int = 30, min_samples: int = 50
    ) -> Dict:
        """Retrain calibration model with recent matched data.

        Parameters
        ----------
        days:
            Number of days of training data to use.
        min_samples:
            Minimum samples required for training.

        Returns
        -------
        dict
            Training result with model version and metrics.

        Raises
        ------
        HTTPException
            If insufficient training data is available.
        """
        from fastapi import HTTPException

        training_data = await self._get_training_pairs(days=days)

        if len(training_data) < min_samples:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Insufficient training data: {len(training_data)} samples "
                    f"(need at least {min_samples})"
                ),
            )

        result = self.calibration_model.train(training_data)

        return {
            "model_version": result.model_version,
            "r_squared": round(result.r_squared, 4),
            "rmse": round(result.rmse, 2),
            "mae": round(result.mae, 2),
            "training_samples": result.training_samples,
            "feature_importance": {
                k: round(v, 4) for k, v in result.feature_importance.items()
            },
        }

    # =====================================================================
    # Helper Methods
    # =====================================================================

    async def _fetch_sensor_readings(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 50.0,
    ) -> List[Dict]:
        """Fetch sensor readings from Sensor Service as fusion-ready dicts."""
        if not self.sensor_client:
            return []

        try:
            readings = await self.sensor_client.get_recent_readings(
                latitude, longitude, radius_km, limit=100
            )
            return [
                {
                    "latitude": r.latitude,
                    "longitude": r.longitude,
                    "pm25": r.pm25,
                    "pm10": r.pm10,
                    "temperature": 25.0,
                    "humidity": 50.0,
                }
                for r in readings
            ]
        except Exception as e:
            logger.warning("Error fetching sensor readings: %s", e)
            return []

    async def _fetch_satellite_cache(
        self, latitude: float, longitude: float
    ) -> Dict:
        """Fetch satellite data from Redis cache."""
        if not self.cache:
            return {"grid_cells": []}

        cached = await self.cache.get_aqi(latitude, longitude, 50.0)
        if cached and cached.get("fused_pm25") is not None:
            return {
                "grid_cells": [
                    {
                        "lat": cached.get("location_lat", latitude),
                        "lon": cached.get("location_lng", longitude),
                        "value": cached["fused_pm25"],
                    }
                ]
            }
        return {"grid_cells": []}

    async def _get_active_sensors(self) -> List[Dict]:
        """Get list of active sensors from Sensor Service."""
        if not self.sensor_client:
            return []

        try:
            return await self.sensor_client.get_all_active_sensors()
        except Exception as e:
            logger.warning("Error fetching active sensors: %s", e)
            return []

    async def _get_training_pairs(
        self, days: int = 30
    ) -> List[tuple]:
        """Get matched sensor-satellite pairs for training/evaluation.

        Returns list of (feature_dict, satellite_reference_value) tuples.
        """
        pairs = []

        if not self.sensor_client:
            return pairs

        try:
            sensors = await self.sensor_client.get_all_active_sensors()
            end = datetime.utcnow()
            start = end - timedelta(days=days)

            for sensor in sensors[:20]:  # Limit to 20 sensors for performance
                sensor_id = sensor.get("sensor_id", sensor.get("id", ""))
                if not sensor_id:
                    continue

                readings = await self.sensor_client.get_sensor_readings(
                    sensor_id, start, end, limit=100
                )

                for reading in readings:
                    if reading.pm25 <= 0:
                        continue

                    # Look up satellite reference from cache
                    cached = await self.cache.get_aqi(
                        reading.latitude, reading.longitude, 10.0
                    )
                    if not cached or cached.get("fused_pm25") is None:
                        continue

                    features = {
                        "raw_pm25": reading.pm25,
                        "temperature": 25.0,
                        "humidity": 50.0,
                        "satellite_aod": 0.5,
                        "hour": reading.timestamp.hour,
                        "day_of_week": reading.timestamp.weekday(),
                    }
                    pairs.append((features, cached["fused_pm25"]))

        except Exception as e:
            logger.warning("Error collecting training pairs: %s", e)

        return pairs

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
        if not self.sensor_client:
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
        return await self.sensor_client.get_historical(lat, lng, hours=24)

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

    .. deprecated::
        Prefer ``src.interfaces.api.dependencies.get_air_quality_service``
        which reuses lifespan-managed singletons instead of creating new
        connections per request.

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
        cache = RedisCache()
        await cache.connect()

        google_client = GoogleMapsClient()
        await google_client.connect()

        sensor_client = SensorServiceClient()
        await sensor_client.connect()

        aqi_calculator = AQICalculator()
        prediction_service = PredictionService()

        service = AirQualityApplicationService(
            aqi_calculator=aqi_calculator,
            prediction_service=prediction_service,
            cache=cache,
            google_client=google_client,
            sensor_client=sensor_client,
            calibration_model=CalibrationModel(),
            cross_validator=CrossValidationService(),
        )
        try:
            yield service
        finally:
            await cache.close()
            await google_client.close()
            await sensor_client.close()

    return _generate()

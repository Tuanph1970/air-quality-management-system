"""Dashboard routes.

Aggregates data from multiple services for dashboard views.
These endpoints call multiple backend services and combine results.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from ..config import settings
from ..middleware.auth_middleware import require_auth
from ..utils.service_client import ServiceClient, registry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


def get_service_clients() -> Dict[str, ServiceClient]:
    """Get all service clients from registry."""
    return {
        "factory": ServiceClient(settings.FACTORY_SERVICE_URL, "factory-service"),
        "sensor": ServiceClient(settings.SENSOR_SERVICE_URL, "sensor-service"),
        "alert": ServiceClient(settings.ALERT_SERVICE_URL, "alert-service"),
        "air_quality": ServiceClient(settings.AIR_QUALITY_SERVICE_URL, "air-quality-service"),
    }


@router.get("/summary")
async def get_dashboard_summary(
    user: dict = Depends(require_auth),
) -> Dict[str, Any]:
    """Get dashboard summary with aggregated data from all services.

    Combines data from:
    - Factory service: factory counts
    - Sensor service: sensor counts
    - Alert service: violation counts
    - Air quality service: current AQI

    Requires authentication.
    """
    clients = get_service_clients()
    results = {
        "factories": {"total": 0, "active": 0},
        "sensors": {"total": 0, "active": 0},
        "violations": {"total": 0, "open": 0, "critical": 0},
        "air_quality": {"average_aqi": 0, "status": "unknown"},
    }

    async def fetch_factories():
        try:
            client = clients["factory"]
            if client._client is None:
                await client.connect()
            response = await client.get("/api/v1/factories")
            data = response.json()
            factories = data.get("data", []) if isinstance(data, dict) else data
            results["factories"]["total"] = len(factories) if isinstance(factories, list) else data.get("total", 0)
            results["factories"]["active"] = sum(
                1 for f in factories if isinstance(factories, list) and f.get("is_active", True)
            ) if isinstance(factories, list) else 0
        except Exception as e:
            logger.warning(f"Failed to fetch factories: {e}")

    async def fetch_sensors():
        try:
            client = clients["sensor"]
            if client._client is None:
                await client.connect()
            response = await client.get("/api/v1/sensors")
            data = response.json()
            sensors = data.get("data", []) if isinstance(data, dict) else data
            results["sensors"]["total"] = len(sensors) if isinstance(sensors, list) else data.get("total", 0)
            results["sensors"]["active"] = sum(
                1 for s in sensors if isinstance(sensors, list) and s.get("status") == "ACTIVE"
            ) if isinstance(sensors, list) else 0
        except Exception as e:
            logger.warning(f"Failed to fetch sensors: {e}")

    async def fetch_violations():
        try:
            client = clients["alert"]
            if client._client is None:
                await client.connect()
            # Get total violations
            response = await client.get("/api/v1/violations?limit=1")
            data = response.json()
            results["violations"]["total"] = data.get("total", 0)

            # Get open violations
            response = await client.get("/api/v1/violations?status=OPEN&limit=1")
            data = response.json()
            results["violations"]["open"] = data.get("total", 0)

            # Get critical violations
            response = await client.get("/api/v1/violations?severity=CRITICAL&limit=1")
            data = response.json()
            results["violations"]["critical"] = data.get("total", 0)
        except Exception as e:
            logger.warning(f"Failed to fetch violations: {e}")

    async def fetch_air_quality():
        try:
            client = clients["air_quality"]
            if client._client is None:
                await client.connect()
            # Get current AQI for a default location (could be made configurable)
            response = await client.get("/api/v1/aqi/current?latitude=21.0285&longitude=105.8542")
            data = response.json()
            results["air_quality"]["average_aqi"] = data.get("aqi_value", 0)
            results["air_quality"]["status"] = data.get("category", "unknown")
        except Exception as e:
            logger.warning(f"Failed to fetch air quality: {e}")

    # Fetch all data concurrently
    await asyncio.gather(
        fetch_factories(),
        fetch_sensors(),
        fetch_violations(),
        fetch_air_quality(),
    )

    return {
        "summary": results,
        "user": user,
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
    }


@router.get("/factories")
async def get_factories_dashboard(
    user: dict = Depends(require_auth),
) -> Dict[str, Any]:
    """Get factory-specific dashboard data."""
    try:
        client = ServiceClient(settings.FACTORY_SERVICE_URL, "factory-service")
        if client._client is None:
            await client.connect()

        response = await client.get("/api/v1/factories")
        data = response.json()

        return {
            "factories": data.get("data", []) if isinstance(data, dict) else data,
            "total": data.get("total", 0) if isinstance(data, dict) else len(data),
        }
    except Exception as e:
        logger.error(f"Failed to fetch factories dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Factory service unavailable: {str(e)}",
        )


@router.get("/alerts")
async def get_alerts_dashboard(
    user: dict = Depends(require_auth),
) -> Dict[str, Any]:
    """Get alerts/violations dashboard data."""
    try:
        client = ServiceClient(settings.ALERT_SERVICE_URL, "alert-service")
        if client._client is None:
            await client.connect()

        # Get active alerts count
        response = await client.get("/api/v1/alerts/active")
        alerts_data = response.json()

        # Get recent violations
        response = await client.get("/api/v1/violations?limit=10")
        violations_data = response.json()

        return {
            "active_alerts": alerts_data,
            "recent_violations": violations_data.get("data", []) if isinstance(violations_data, dict) else violations_data[:10],
        }
    except Exception as e:
        logger.error(f"Failed to fetch alerts dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Alert service unavailable: {str(e)}",
        )


@router.get("/air-quality")
async def get_air_quality_dashboard(
    user: dict = Depends(require_auth),
) -> Dict[str, Any]:
    """Get air quality dashboard data."""
    try:
        client = ServiceClient(settings.AIR_QUALITY_SERVICE_URL, "air-quality-service")
        if client._client is None:
            await client.connect()

        # Get AQI categories for reference
        response = await client.get("/api/v1/aqi/categories")
        categories = response.json()

        return {
            "categories": categories.get("categories", []),
            "health_recommendations": "Check current AQI for specific recommendations",
        }
    except Exception as e:
        logger.error(f"Failed to fetch air quality dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Air quality service unavailable: {str(e)}",
        )

"""Sensor service routes.

Proxies all /api/v1/sensors/* requests to the sensor-service.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..config import settings
from ..utils.service_client import ServiceClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/sensors", tags=["sensors"])

_sensor_client: ServiceClient | None = None


def get_sensor_client() -> ServiceClient:
    """Get or create sensor service client."""
    global _sensor_client
    if _sensor_client is None:
        _sensor_client = ServiceClient(
            base_url=settings.SENSOR_SERVICE_URL,
            service_name="sensor-service",
        )
    return _sensor_client


@router.api_route("", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_sensor_request(request: Request, path: str = "") -> JSONResponse:
    """Proxy all sensor service requests."""
    client = get_sensor_client()

    try:
        if client._client is None:
            await client.connect()

        url = f"/api/v1/sensors/{path}" if path else "/api/v1/sensors"

        body = None
        if request.method in ("POST", "PUT", "PATCH"):
            body = await request.body()
            if body:
                import json
                try:
                    body = json.loads(body)
                except:
                    pass

        response = await client.request(
            method=request.method,
            path=url,
            params=dict(request.query_params),
            json=body,
        )

        return JSONResponse(
            status_code=response.status_code,
            content=response.json() if response.content else {},
        )

    except Exception as e:
        logger.error(f"Sensor service error: {e}")
        return JSONResponse(
            status_code=503,
            content={"detail": f"Sensor service unavailable: {str(e)}"},
        )

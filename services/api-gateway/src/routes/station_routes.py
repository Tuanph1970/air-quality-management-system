"""Station service routes — proxy requests to station-service."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from ..config import settings
from ..utils.service_client import ServiceClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/stations", tags=["stations"])

_station_client: ServiceClient | None = None


def get_station_client() -> ServiceClient:
    """Get or create station service client."""
    global _station_client
    if _station_client is None:
        _station_client = ServiceClient(
            base_url=settings.STATION_SERVICE_URL,
            service_name="station-service",
        )
    return _station_client


@router.api_route("", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_station_request(
    request: Request,
    path: str = "",
) -> Response:
    """Proxy all station service requests."""
    client = get_station_client()

    try:
        if client._client is None:
            await client.connect()

        url = f"/api/v1/stations/{path}" if path else "/api/v1/stations"

        forward_headers = {}
        for key, value in request.headers.items():
            if key.lower() not in ("host", "content-length", "transfer-encoding"):
                forward_headers[key] = value

        body = None
        if request.method in ("POST", "PUT", "PATCH"):
            body = await request.body()
            if body:
                import json
                try:
                    body = json.loads(body)
                except Exception:
                    pass

        response = await client.request(
            method=request.method,
            path=url,
            params=dict(request.query_params),
            json=body,
            headers=forward_headers,
        )

        return JSONResponse(
            status_code=response.status_code,
            content=response.json() if response.content else {},
            headers=dict(response.headers),
        )

    except Exception as e:
        logger.error(f"Station service error: {e}")
        return JSONResponse(
            status_code=503,
            content={"detail": f"Station service unavailable: {str(e)}"},
        )

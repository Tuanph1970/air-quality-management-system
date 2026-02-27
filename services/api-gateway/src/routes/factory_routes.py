"""Factory service routes.

Proxies all /api/v1/factories/* requests to the factory-service.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from ..config import settings
from ..utils.service_client import ServiceClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/factories", tags=["factories"])

# Service client for factory-service
_factory_client: ServiceClient | None = None


def get_factory_client() -> ServiceClient:
    """Get or create factory service client."""
    global _factory_client
    if _factory_client is None:
        _factory_client = ServiceClient(
            base_url=settings.FACTORY_SERVICE_URL,
            service_name="factory-service",
        )
    return _factory_client


@router.api_route("", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_factory_request(
    request: Request,
    path: str = "",
) -> Response:
    """Proxy all factory service requests.

    Forwards requests to the factory-service and returns the response.
    """
    client = get_factory_client()

    try:
        # Ensure client is connected
        if client._client is None:
            await client.connect()

        # Build request
        url = f"/api/v1/factories/{path}" if path else "/api/v1/factories"

        # Forward headers (excluding hop-by-hop headers)
        forward_headers = {}
        for key, value in request.headers.items():
            if key.lower() not in ("host", "content-length", "transfer-encoding"):
                forward_headers[key] = value

        # Get request body
        body = None
        if request.method in ("POST", "PUT", "PATCH"):
            body = await request.body()
            if body:
                import json
                try:
                    body = json.loads(body)
                except:
                    pass

        # Make request to factory service
        response = await client.request(
            method=request.method,
            path=url,
            params=dict(request.query_params),
            json=body,
            headers=forward_headers,
        )

        # Return response
        return JSONResponse(
            status_code=response.status_code,
            content=response.json() if response.content else {},
            headers=dict(response.headers),
        )

    except Exception as e:
        logger.error(f"Factory service error: {e}")
        return JSONResponse(
            status_code=503,
            content={"detail": f"Factory service unavailable: {str(e)}"},
        )

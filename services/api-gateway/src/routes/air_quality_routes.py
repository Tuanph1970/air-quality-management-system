"""Air quality service routes.

Proxies all /api/v1/air-quality/* requests to the air-quality-service.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from ..config import settings
from ..utils.service_client import ServiceClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/air-quality", tags=["air-quality"])

_aq_client: ServiceClient | None = None


def get_aq_client() -> ServiceClient:
    """Get or create air quality service client."""
    global _aq_client
    if _aq_client is None:
        _aq_client = ServiceClient(
            base_url=settings.AIR_QUALITY_SERVICE_URL,
            service_name="air-quality-service",
        )
    return _aq_client


@router.api_route("", methods=["GET", "POST"])
@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_aq_request(request: Request, path: str = "") -> Response:
    """Proxy all air quality service requests."""
    client = get_aq_client()

    try:
        if client._client is None:
            await client.connect()

        # Reconstruct path
        if path:
            url = f"/api/v1/air-quality/{path}"
        else:
            url = "/api/v1/air-quality"

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

        # Handle different response types
        content_type = response.headers.get("content-type", "")
        if "image" in content_type:
            return Response(
                content=response.content,
                status_code=response.status_code,
                media_type=content_type,
            )

        return JSONResponse(
            status_code=response.status_code,
            content=response.json() if response.content else {},
        )

    except Exception as e:
        logger.error(f"Air quality service error: {e}")
        return JSONResponse(
            status_code=503,
            content={"detail": f"Air quality service unavailable: {str(e)}"},
        )

"""Alert service routes.

Proxies all /api/v1/alerts/* and /api/v1/violations/* requests to the alert-service.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..config import settings
from ..utils.service_client import ServiceClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["alerts", "violations"])

_alert_client: ServiceClient | None = None


def get_alert_client() -> ServiceClient:
    """Get or create alert service client."""
    global _alert_client
    if _alert_client is None:
        _alert_client = ServiceClient(
            base_url=settings.ALERT_SERVICE_URL,
            service_name="alert-service",
        )
    return _alert_client


@router.api_route("/alerts/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
@router.api_route("/violations/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_alert_request(request: Request, path: str = "") -> JSONResponse:
    """Proxy all alert service requests."""
    client = get_alert_client()

    try:
        if client._client is None:
            await client.connect()

        # Reconstruct the full path
        full_path = request.url.path.replace("/api/v1/", "", 1)
        url = f"/api/v1/{full_path}"

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
        logger.error(f"Alert service error: {e}")
        return JSONResponse(
            status_code=503,
            content={"detail": f"Alert service unavailable: {str(e)}"},
        )

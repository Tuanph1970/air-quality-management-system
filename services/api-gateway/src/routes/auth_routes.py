"""Auth routes.

Proxies all /api/v1/auth/* requests to the user-service.
These endpoints are public (no authentication required).
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..config import settings
from ..utils.service_client import ServiceClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

_user_client: ServiceClient | None = None


def get_user_client() -> ServiceClient:
    """Get or create user service client."""
    global _user_client
    if _user_client is None:
        _user_client = ServiceClient(
            base_url=settings.USER_SERVICE_URL,
            service_name="user-service",
        )
    return _user_client


@router.api_route("", methods=["GET", "POST"])
@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_auth_request(request: Request, path: str = "") -> JSONResponse:
    """Proxy all auth requests to user-service."""
    client = get_user_client()

    try:
        if client._client is None:
            await client.connect()

        url = f"/api/v1/auth/{path}" if path else "/api/v1/auth"

        json_body = None
        if request.method in ("POST", "PUT", "PATCH"):
            raw_body = await request.body()
            if raw_body:
                import json
                try:
                    json_body = json.loads(raw_body)
                except Exception:
                    json_body = None

        response = await client.request(
            method=request.method,
            path=url,
            params=dict(request.query_params),
            json=json_body,
        )

        return JSONResponse(
            status_code=response.status_code,
            content=response.json() if response.content else {},
        )

    except Exception as e:
        logger.error(f"User service error: {e}")
        return JSONResponse(
            status_code=503,
            content={"detail": f"User service unavailable: {str(e)}"},
        )

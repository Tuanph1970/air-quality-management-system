"""Request logging middleware for API Gateway.

Logs all incoming requests with timing, status, and user information.
Useful for debugging, monitoring, and audit trails.

Features:
- Logs request method, path, and timing
- Includes user information if authenticated
- Optional request/response body logging
- Structured logging format
"""
from __future__ import annotations

import json
import logging
import time
from typing import Optional

from fastapi import Request

from ..config import settings

logger = logging.getLogger(__name__)


class RequestLoggerMiddleware:
    """Middleware for logging all requests.

    Logs request details including:
    - HTTP method and path
    - Response status code
    - Request duration
    - User information (if authenticated)
    - Client IP address
    """

    def __init__(self, app):
        """Initialize the middleware.

        Parameters
        ----------
        app:
            The FastAPI application
        """
        self.app = app
        self.log_body = settings.LOG_REQUEST_BODY
        self.log_response_body = settings.LOG_RESPONSE_BODY

    async def __call__(self, scope, receive, send):
        """Process the request through logging middleware.

        Parameters
        ----------
        scope:
            ASGI scope
        receive:
            ASGI receive callable
        send:
            ASGI send callable
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        start_time = time.time()

        # Log request
        self._log_request(request)

        # Capture response
        response_status = None
        response_body = b""

        async def send_wrapper(message):
            nonlocal response_status, response_body

            if message["type"] == "http.response.start":
                response_status = message["status"]
            elif message["type"] == "http.response.body":
                response_body += message.get("body", b"")

            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            # Log exception
            duration = time.time() - start_time
            self._log_exception(request, e, duration)
            raise

        # Log response
        duration = time.time() - start_time
        self._log_response(request, response_status, duration, response_body)

    def _log_request(self, request: Request):
        """Log incoming request.

        Parameters
        ----------
        request:
            FastAPI request
        """
        if not settings.LOG_REQUESTS:
            return

        # Get user info if available
        user_info = self._get_user_info(request)

        log_data = {
            "event": "request",
            "method": request.method,
            "path": str(request.url.path),
            "query": str(request.url.query) if request.url.query else None,
            "client_ip": request.client.host if request.client else "unknown",
            "user": user_info,
        }

        # Optionally log request body
        if self.log_body and request.method in ("POST", "PUT", "PATCH"):
            log_data["body"] = self._truncate_body(
                request.scope.get("_body", b"").decode("utf-8", errors="ignore")
            )

        logger.info(json.dumps(log_data))

    def _log_response(
        self,
        request: Request,
        status_code: Optional[int],
        duration: float,
        body: bytes,
    ):
        """Log response.

        Parameters
        ----------
        request:
            FastAPI request
        status_code:
            Response status code
        duration:
            Request duration in seconds
        body:
            Response body bytes
        """
        if not settings.LOG_REQUESTS:
            return

        log_data = {
            "event": "response",
            "method": request.method,
            "path": str(request.url.path),
            "status": status_code,
            "duration_ms": round(duration * 1000, 2),
        }

        # Add timing category
        if duration < 0.1:
            log_data["timing"] = "fast"
        elif duration < 0.5:
            log_data["timing"] = "normal"
        elif duration < 1.0:
            log_data["timing"] = "slow"
        else:
            log_data["timing"] = "very_slow"

        # Optionally log response body
        if self.log_response_body and body:
            log_data["body"] = self._truncate_body(
                body.decode("utf-8", errors="ignore")
            )

        logger.info(json.dumps(log_data))

    def _log_exception(self, request: Request, exception: Exception, duration: float):
        """Log exception.

        Parameters
        ----------
        request:
            FastAPI request
        exception:
            Exception that occurred
        duration:
            Request duration when exception occurred
        """
        user_info = self._get_user_info(request)

        log_data = {
            "event": "exception",
            "method": request.method,
            "path": str(request.url.path),
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "duration_ms": round(duration * 1000, 2),
            "user": user_info,
        }

        logger.error(json.dumps(log_data), exc_info=True)

    def _get_user_info(self, request: Request) -> Optional[dict]:
        """Get user info from request state.

        Parameters
        ----------
        request:
            FastAPI request

        Returns
        -------
        dict or None
            User info dict or None
        """
        if hasattr(request.state, "user") and request.state.user:
            return {
                "user_id": request.state.user.get("user_id"),
                "email": request.state.user.get("email"),
                "role": request.state.user.get("role"),
            }
        return None

    def _truncate_body(self, body: str, max_length: int = 1000) -> str:
        """Truncate body for logging.

        Parameters
        ----------
        body:
            Body string
        max_length:
            Maximum length

        Returns
        -------
        str
            Truncated body
        """
        if len(body) <= max_length:
            return body
        return body[:max_length] + f"... ({len(body)} bytes total)"


# =============================================================================
# Timing middleware for detailed performance tracking
# =============================================================================


class TimingMiddleware:
    """Middleware for tracking request timing.

    Adds timing information to request state for use in other middleware
    and route handlers.
    """

    def __init__(self, app):
        """Initialize the middleware.

        Parameters
        ----------
        app:
            The FastAPI application
        """
        self.app = app

    async def __call__(self, scope, receive, send):
        """Process the request through timing middleware.

        Parameters
        ----------
        scope:
            ASGI scope
        receive:
            ASGI receive callable
        send:
            ASGI send callable
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        from fastapi import Request

        request = Request(scope, receive)
        start_time = time.perf_counter()

        # Store start time in request state
        request.state.start_time = start_time

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                elapsed = time.perf_counter() - start_time
                request.state.elapsed_time = elapsed
            await send(message)

        await self.app(scope, receive, send_wrapper)

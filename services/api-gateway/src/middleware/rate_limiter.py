"""Rate limiting middleware for API Gateway.

Implements rate limiting to protect services from abuse.
Supports both in-memory and Redis-backed rate limiting.

Features:
- Rate limiting by IP address or user ID
- Configurable limits per endpoint type
- Redis for distributed rate limiting
- Sliding window algorithm
"""
from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Optional

import redis.asyncio as redis
from fastapi import Depends, Request

from ..config import settings

logger = logging.getLogger(__name__)


@dataclass
class RateLimitResult:
    """Result of rate limit check."""

    allowed: bool
    limit: int
    remaining: int
    reset_at: float
    retry_after: Optional[float] = None


class InMemoryRateLimiter:
    """In-memory rate limiter for single-instance deployments.

    Uses a sliding window algorithm to track request counts.
    """

    def __init__(self):
        """Initialize the rate limiter."""
        # Structure: {key: [(timestamp, count), ...]}
        self._requests: Dict[str, list] = defaultdict(list)
        self._window_size = 60  # 1 minute window

    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_size: int = 60,
    ) -> RateLimitResult:
        """Check if request is within rate limit.

        Parameters
        ----------
        key:
            Rate limit key (IP or user ID)
        limit:
            Maximum requests per window
        window_size:
            Window size in seconds

        Returns
        -------
        RateLimitResult
            Rate limit check result
        """
        now = time.time()
        window_start = now - window_size

        # Clean old entries
        self._requests[key] = [
            ts for ts in self._requests[key] if ts > window_start
        ]

        # Check limit
        current_count = len(self._requests[key])
        remaining = max(0, limit - current_count)

        if current_count >= limit:
            # Rate limited
            oldest = min(self._requests[key]) if self._requests[key] else now
            reset_at = oldest + window_size
            retry_after = reset_at - now

            return RateLimitResult(
                allowed=False,
                limit=limit,
                remaining=0,
                reset_at=reset_at,
                retry_after=max(0, retry_after),
            )

        # Record this request
        self._requests[key].append(now)

        return RateLimitResult(
            allowed=True,
            limit=limit,
            remaining=remaining - 1,
            reset_at=now + window_size,
        )

    async def cleanup(self):
        """Clean up old entries (periodic maintenance)."""
        now = time.time()
        window_start = now - self._window_size

        for key in list(self._requests.keys()):
            self._requests[key] = [
                ts for ts in self._requests[key] if ts > window_start
            ]
            if not self._requests[key]:
                del self._requests[key]


class RedisRateLimiter:
    """Redis-backed rate limiter for distributed deployments.

    Uses Redis INCR and EXPIRE for atomic rate limiting.
    """

    def __init__(self, redis_url: str = None):
        """Initialize the Redis rate limiter.

        Parameters
        ----------
        redis_url:
            Redis connection URL
        """
        self.redis_url = redis_url or settings.REDIS_URL
        self._client: Optional[redis.Redis] = None

    async def connect(self):
        """Connect to Redis."""
        try:
            self._client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            await self._client.ping()
            logger.info("Connected to Redis for rate limiting")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Falling back to memory.")
            self._client = None

    async def close(self):
        """Close Redis connection."""
        if self._client:
            await self._client.close()

    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_size: int = 60,
    ) -> RateLimitResult:
        """Check if request is within rate limit.

        Uses Redis atomic operations for distributed rate limiting.

        Parameters
        ----------
        key:
            Rate limit key (IP or user ID)
        limit:
            Maximum requests per window
        window_size:
            Window size in seconds

        Returns
        -------
        RateLimitResult
            Rate limit check result
        """
        if not self._client:
            # Fallback to in-memory
            fallback = InMemoryRateLimiter()
            return await fallback.check_rate_limit(key, limit, window_size)

        now = int(time.time())
        window_key = f"ratelimit:{key}:{now // window_size}"

        try:
            # Atomic increment
            current = await self._client.incr(window_key)
            
            # Set expiry on first request
            if current == 1:
                await self._client.expire(window_key, window_size * 2)

            remaining = max(0, limit - current)
            reset_at = ((now // window_size) + 1) * window_size

            if current > limit:
                return RateLimitResult(
                    allowed=False,
                    limit=limit,
                    remaining=0,
                    reset_at=reset_at,
                    retry_after=reset_at - now,
                )

            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=remaining,
                reset_at=reset_at,
            )
        except Exception as e:
            logger.error(f"Redis rate limit error: {e}")
            # Fail open - allow request
            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=limit,
                reset_at=time.time() + window_size,
            )


class RateLimitMiddleware:
    """Middleware for rate limiting requests.

    Applies rate limiting based on IP address or user ID.
    """

    def __init__(self, app):
        """Initialize the middleware.

        Parameters
        ----------
        app:
            The FastAPI application
        """
        self.app = app
        self._limiter: Optional[RedisRateLimiter | InMemoryRateLimiter] = None

        if settings.RATE_LIMIT_USE_REDIS:
            self._limiter = RedisRateLimiter()
        else:
            self._limiter = InMemoryRateLimiter()

    async def __call__(self, scope, receive, send):
        """Process the request through rate limiting middleware.

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
        from fastapi.responses import JSONResponse

        request = Request(scope, receive)

        # Skip rate limiting for health checks
        if request.url.path in ("/health", "/", "/docs", "/redoc", "/openapi.json"):
            await self.app(scope, receive, send)
            return

        # Get rate limit key (user ID if authenticated, else IP)
        key = self._get_rate_limit_key(request)

        # Get rate limit for this endpoint
        limit = self._get_rate_limit(request.url.path)

        # Check rate limit
        if isinstance(self._limiter, RedisRateLimiter) and not self._limiter._client:
            await self._limiter.connect()

        result = await self._limiter.check_rate_limit(key, limit)

        # Add rate limit headers
        headers = {
            "X-RateLimit-Limit": str(result.limit),
            "X-RateLimit-Remaining": str(result.remaining),
            "X-RateLimit-Reset": str(int(result.reset_at)),
        }

        if not result.allowed:
            headers["Retry-After"] = str(int(result.retry_after or 60))
            response = JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"},
                headers=headers,
            )
            await response(scope, receive, send)
            return

        # Store rate limit info in request state for response headers
        request.state.rate_limit = result

        # Wrap send to add headers to response
        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers_list = message.get("headers", [])
                for name, value in headers.items():
                    headers_list.append((name.lower().encode(), value.encode()))
                message["headers"] = headers_list
            await send(message)

        await self.app(scope, receive, send_with_headers)

    def _get_rate_limit_key(self, request) -> str:
        """Get rate limit key for request.

        Parameters
        ----------
        request:
            FastAPI request

        Returns
        -------
        str
            Rate limit key
        """
        # Try to get user ID from request state
        if hasattr(request.state, "user") and request.state.user:
            user_id = request.state.user.get("user_id")
            if user_id:
                return f"user:{user_id}"

        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"

    def _get_rate_limit(self, path: str) -> int:
        """Get rate limit for endpoint.

        Parameters
        ----------
        path:
            Request path

        Returns
        -------
        int
            Rate limit (requests per minute)
        """
        # Auth endpoints have stricter limits
        if path.startswith("/api/v1/auth"):
            return settings.RATE_LIMIT_AUTH

        # Admin endpoints have higher limits
        if "/admin/" in path:
            return settings.RATE_LIMIT_ADMIN

        return settings.RATE_LIMIT_DEFAULT


# =============================================================================
# Dependency for route handlers
# =============================================================================

async def check_rate_limit(
    request: Request,
    limiter: RedisRateLimiter = Depends(lambda: RedisRateLimiter()),
) -> RateLimitResult:
    """Check rate limit as a dependency.

    Can be used in route handlers for custom rate limiting logic.
    """
    key = f"endpoint:{request.url.path}"
    return await limiter.check_rate_limit(key, settings.RATE_LIMIT_DEFAULT)

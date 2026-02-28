"""Service client for calling microservices.

Provides a unified HTTP client for communicating with backend microservices.
Includes retry logic and circuit breaker pattern for resilience.

Features:
- HTTP client using httpx
- Automatic retry with exponential backoff
- Circuit breaker pattern
- Request/response logging
- Timeout configuration
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

import httpx

from ..config import settings

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreaker:
    """Circuit breaker for service calls.

    Prevents cascading failures by stopping requests to failing services.
    """

    failure_threshold: int = field(default=5)
    recovery_timeout: int = field(default=60)

    state: CircuitState = field(default=CircuitState.CLOSED)
    failure_count: int = field(default=0)
    last_failure_time: Optional[float] = field(default=None)
    success_count: int = field(default=0)

    def can_execute(self) -> bool:
        """Check if request can be executed.

        Returns
        -------
        bool
            True if circuit allows request
        """
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self.last_failure_time:
                elapsed = time.time() - self.last_failure_time
                if elapsed >= self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    return True
            return False

        # HALF_OPEN - allow one request to test
        return True

    def record_success(self):
        """Record successful request."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= 3:  # Require 3 successes to close
                self.state = CircuitState.CLOSED
                self.failure_count = 0
        else:
            self.failure_count = max(0, self.failure_count - 1)

    def record_failure(self):
        """Record failed request."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
        elif self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )


class ServiceClient:
    """HTTP client for calling microservices.

    Provides resilient communication with backend services including:
    - Automatic retries with exponential backoff
    - Circuit breaker pattern
    - Timeout configuration
    - Request/response logging
    """

    def __init__(
        self,
        base_url: str,
        service_name: str = "unknown",
        timeout: float = None,
        retry_count: int = None,
    ):
        """Initialize the service client.

        Parameters
        ----------
        base_url:
            Base URL of the service
        service_name:
            Name of the service for logging
        timeout:
            Request timeout in seconds
        retry_count:
            Number of retry attempts
        """
        self.base_url = base_url.rstrip("/")
        self.service_name = service_name
        self.timeout = timeout or settings.SERVICE_TIMEOUT
        self.retry_count = retry_count or settings.SERVICE_RETRY_COUNT
        self.retry_backoff = settings.SERVICE_RETRY_BACKOFF

        self._client: Optional[httpx.AsyncClient] = None
        self._circuit_breaker: Optional[CircuitBreaker] = None

        if settings.CIRCUIT_BREAKER_ENABLED:
            self._circuit_breaker = CircuitBreaker(
                failure_threshold=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
                recovery_timeout=settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
            )

    async def connect(self):
        """Initialize HTTP client."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout),
            headers={
                "Accept": "application/json",
            },
        )
        logger.info(f"ServiceClient initialized for {self.service_name} ({self.base_url})")

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()

    async def request(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> httpx.Response:
        """Make HTTP request to service.

        Parameters
        ----------
        method:
            HTTP method
        path:
            Request path
        headers:
            Optional headers
        params:
            Optional query parameters
        json:
            Optional JSON body
        **kwargs:
            Additional httpx arguments

        Returns
        -------
        httpx.Response
            HTTP response

        Raises
        ------
        httpx.HTTPError
            If request fails after retries
        """
        if not self._client:
            await self.connect()

        # Check circuit breaker
        if self._circuit_breaker and not self._circuit_breaker.can_execute():
            logger.warning(
                f"Circuit breaker open for {self.service_name}, rejecting request"
            )
            raise httpx.ConnectError(
                f"Service {self.service_name} is unavailable (circuit breaker open)"
            )

        last_exception = None

        for attempt in range(self.retry_count + 1):
            try:
                response = await self._client.request(
                    method=method,
                    url=path,
                    headers=headers,
                    params=params,
                    json=json,
                    **kwargs,
                )

                # Record success
                if self._circuit_breaker:
                    self._circuit_breaker.record_success()

                return response

            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
                last_exception = e
                logger.warning(
                    f"Request to {self.service_name} failed (attempt {attempt + 1}/{self.retry_count + 1}): {e}"
                )

                if self._circuit_breaker:
                    self._circuit_breaker.record_failure()

                if attempt < self.retry_count:
                    # Exponential backoff
                    wait_time = self.retry_backoff * (2 ** attempt)
                    await asyncio.sleep(wait_time)

        # All retries exhausted
        logger.error(
            f"All retries exhausted for {self.service_name} ({self.base_url}{path})"
        )
        raise last_exception or httpx.ConnectError("Request failed after all retries")

    async def get(self, path: str, **kwargs) -> httpx.Response:
        """Make GET request."""
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs) -> httpx.Response:
        """Make POST request."""
        return await self.request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs) -> httpx.Response:
        """Make PUT request."""
        return await self.request("PUT", path, **kwargs)

    async def patch(self, path: str, **kwargs) -> httpx.Response:
        """Make PATCH request."""
        return await self.request("PATCH", path, **kwargs)

    async def delete(self, path: str, **kwargs) -> httpx.Response:
        """Make DELETE request."""
        return await self.request("DELETE", path, **kwargs)

    async def post_file(
        self,
        path: str,
        file_content: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
        field_name: str = "file",
        **kwargs,
    ) -> httpx.Response:
        """Make POST request with multipart file upload.

        Parameters
        ----------
        path:
            Request path
        file_content:
            Raw file bytes
        filename:
            Original filename
        content_type:
            MIME type of the file
        field_name:
            Form field name for the file
        **kwargs:
            Additional httpx arguments

        Returns
        -------
        httpx.Response
            HTTP response
        """
        files = {field_name: (filename, file_content, content_type)}
        return await self.request("POST", path, files=files, **kwargs)

    def get_circuit_state(self) -> Optional[CircuitState]:
        """Get circuit breaker state.

        Returns
        -------
        CircuitState or None
            Current circuit state or None if disabled
        """
        if self._circuit_breaker:
            return self._circuit_breaker.state
        return None


# =============================================================================
# Service client registry
# =============================================================================


class ServiceClientRegistry:
    """Registry of service clients.

    Manages lifecycle of service clients for all microservices.
    """

    def __init__(self):
        """Initialize the registry."""
        self._clients: Dict[str, ServiceClient] = {}

    def register(
        self,
        name: str,
        base_url: str,
        timeout: float = None,
        retry_count: int = None,
    ) -> ServiceClient:
        """Register a service client.

        Parameters
        ----------
        name:
            Service name
        base_url:
            Service base URL
        timeout:
            Request timeout
        retry_count:
            Number of retries

        Returns
        -------
        ServiceClient
            Registered client
        """
        client = ServiceClient(
            base_url=base_url,
            service_name=name,
            timeout=timeout,
            retry_count=retry_count,
        )
        self._clients[name] = client
        return client

    def get(self, name: str) -> Optional[ServiceClient]:
        """Get service client by name.

        Parameters
        ----------
        name:
            Service name

        Returns
        -------
        ServiceClient or None
            Service client or None if not found
        """
        return self._clients.get(name)

    async def connect_all(self):
        """Connect all registered clients."""
        for name, client in self._clients.items():
            await client.connect()
            logger.info(f"Connected to service: {name}")

    async def close_all(self):
        """Close all registered clients."""
        for name, client in self._clients.items():
            await client.close()
            logger.info(f"Disconnected from service: {name}")


# Global registry instance
registry = ServiceClientRegistry()

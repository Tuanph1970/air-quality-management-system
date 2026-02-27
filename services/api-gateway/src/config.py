"""API Gateway configuration via Pydantic Settings.

Centralizes all configuration for the API Gateway including:
- Service URLs for all microservices
- JWT authentication settings
- Rate limiting configuration
- CORS settings
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings — populated from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # =========================================================================
    # Service Identity
    # =========================================================================
    SERVICE_NAME: str = "api-gateway"
    SERVICE_PORT: int = 8000
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # =========================================================================
    # Microservice URLs
    # =========================================================================
    FACTORY_SERVICE_URL: str = "http://factory-service:8001"
    SENSOR_SERVICE_URL: str = "http://sensor-service:8002"
    ALERT_SERVICE_URL: str = "http://alert-service:8003"
    AIR_QUALITY_SERVICE_URL: str = "http://air-quality-service:8004"
    USER_SERVICE_URL: str = "http://user-service:8005"

    # =========================================================================
    # JWT / Authentication
    # =========================================================================
    JWT_SECRET: str = "your-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_AUDIENCE: str = "aqms-api"

    # =========================================================================
    # Rate Limiting
    # =========================================================================
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: int = 60  # requests per minute
    RATE_LIMIT_AUTH: int = 10  # stricter limit for auth endpoints
    RATE_LIMIT_ADMIN: int = 120  # higher limit for admin endpoints

    # Rate limit storage (Redis for distributed, memory for single instance)
    REDIS_URL: str = "redis://redis:6379/0"
    RATE_LIMIT_USE_REDIS: bool = True

    # =========================================================================
    # CORS
    # =========================================================================
    CORS_ORIGINS: str = "*"  # Comma-separated list or "*"
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: str = "*"
    CORS_ALLOW_HEADERS: str = "*"

    # =========================================================================
    # Timeouts and Retries
    # =========================================================================
    SERVICE_TIMEOUT: float = 30.0  # seconds
    SERVICE_RETRY_COUNT: int = 3
    SERVICE_RETRY_BACKOFF: float = 0.1  # seconds

    # =========================================================================
    # Circuit Breaker
    # =========================================================================
    CIRCUIT_BREAKER_ENABLED: bool = True
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 60  # seconds

    # =========================================================================
    # Request Logging
    # =========================================================================
    LOG_REQUESTS: bool = True
    LOG_REQUEST_BODY: bool = False
    LOG_RESPONSE_BODY: bool = False


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


# Module-level convenience alias
settings = get_settings()

# =============================================================================
# Factory Service - Dockerfile
# =============================================================================
# Multi-stage build:
#   1. Install Python dependencies in a builder stage.
#   2. Copy only the installed packages + source into the final slim image.
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1 — dependency installer
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies for native extensions (asyncpg, cryptography).
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------------------------------------------------------------------------
# Stage 2 — runtime image
# ---------------------------------------------------------------------------
FROM python:3.11-slim

# Runtime dependency for asyncpg.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for security.
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

WORKDIR /app

# Copy installed Python packages from builder.
COPY --from=builder /install /usr/local

# Copy application source.
COPY . .

# Ensure the shared library is importable when volume-mounted at /app/shared.
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Switch to non-root user.
USER appuser

EXPOSE 8001

# Default command — production uses gunicorn/uvicorn workers via
# docker-compose override.  The CMD here is suitable for development.
CMD ["uvicorn", "src.interfaces.api.routes:app", \
     "--host", "0.0.0.0", \
     "--port", "8001"]

# =============================================================================
# Remote Sensing Service - Dockerfile
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

# Install build dependencies for native extensions (asyncpg, cryptography,
# netCDF4, rasterio/GDAL).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       gcc libpq-dev libgdal-dev libhdf5-dev libnetcdf-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------------------------------------------------------------------------
# Stage 2 — runtime image
# ---------------------------------------------------------------------------
FROM python:3.11-slim

# Install runtime dependencies using our helper script
# (Package names vary by Debian version)
COPY scripts/install-runtime-deps.sh /tmp/install-runtime-deps.sh
RUN chmod +x /tmp/install-runtime-deps.sh && /tmp/install-runtime-deps.sh

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

EXPOSE 8006

CMD ["uvicorn", "src.interfaces.api.routes:app", \
     "--host", "0.0.0.0", \
     "--port", "8006"]

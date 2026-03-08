# =============================================================================
# WRF Service - Dockerfile
# =============================================================================
# Multi-stage build:
#   1. Install Python dependencies in a builder stage.
#   2. Copy only the installed packages + source into the final slim image.
#
# Note: This Dockerfile sets up the Python environment for WRF service.
# The actual WRF model binaries should be installed separately or mounted
# as volumes from a WRF-enabled base image.
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1 — dependency installer
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies for native extensions
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       gcc gfortran libhdf5-dev libnetcdf-dev libopenmpi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------------------------------------------------------------------------
# Stage 2 — runtime image
# ---------------------------------------------------------------------------
FROM python:3.11-slim

# Install runtime dependencies using our helper script
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

# Create data directories
RUN mkdir -p /app/data/gfs /app/data/wrf_output /app/wrf \
    && chown -R appuser:appuser /app

# Ensure the shared library is importable when volume-mounted.
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# WRF-specific environment variables
ENV WRF_DATA_DIR=/app/data
ENV GFS_DATA_DIR=/app/data/gfs
ENV WRF_OUTPUT_DIR=/app/data/wrf_output
ENV WPS_DIR=/app/wrf/WPS
ENV WRF_MODEL_DIR=/app/wrf/WRFV4

# Switch to non-root user.
USER appuser

EXPOSE 8009

# Default command - can be overridden
CMD ["python", "main.py"]

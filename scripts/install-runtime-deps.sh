#!/usr/bin/env bash
# =============================================================================
# install-runtime-deps.sh - Install runtime dependencies for Python services
# =============================================================================
# This script installs runtime dependencies needed by various Python services.
# It handles differences between Debian versions and package availability.
# =============================================================================

set -e

echo "[INFO] Installing runtime dependencies..."

# Detect Debian version
if [ -f /etc/debian_version ]; then
    DEBIAN_VERSION=$(cat /etc/debian_version | cut -d. -f1)
else
    DEBIAN_VERSION="11"  # Default to bullseye
fi

echo "[INFO] Detected Debian version: $DEBIAN_VERSION"

# Base runtime dependencies
PACKAGES="curl ca-certificates"

# For services that need MySQL client libraries
PACKAGES="$PACKAGES default-libmysqlclient-dev"

# For services that need PostgreSQL client libraries  
PACKAGES="$PACKAGES libpq5"

# For services that need HDF5 and NetCDF runtime libraries
PACKAGES="$PACKAGES libhdf5-103-1 libnetcdf19"

# For services that need GDAL runtime libraries
if [ "$DEBIAN_VERSION" -ge "12" ]; then
    # Bookworm
    PACKAGES="$PACKAGES libgdal32"
elif [ "$DEBIAN_VERSION" -ge "11" ]; then
    # Bullseye
    PACKAGES="$PACKAGES libgdal28"
else
    # Buster and older
    PACKAGES="$PACKAGES libgdal20"
fi

# Install packages
apt-get update
apt-get install -y --no-install-recommends $PACKAGES

# Clean up
rm -rf /var/lib/apt/lists/*

echo "[INFO] Runtime dependencies installed successfully."

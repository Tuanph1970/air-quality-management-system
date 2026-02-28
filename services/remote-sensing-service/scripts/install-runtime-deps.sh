#!/bin/bash
# Install runtime dependencies for remote-sensing service
# Package names vary by Debian version

set -e

apt-get update

# Try to install the latest package versions first
if apt-get install -y --no-install-recommends libpq5 libgdal32 libhdf5-103-1 libnetcdf19 2>/dev/null; then
    echo "Installed GDAL 3.2+ packages"
elif apt-get install -y --no-install-recommends libpq5 libgdal30 libhdf5-103 libnetcdf18 2>/dev/null; then
    echo "Installed GDAL 3.0 packages"
else
    # Fallback: install whatever is available
    apt-get install -y --no-install-recommends \
        libpq5 \
        libgdal-dev \
        libhdf5-dev \
        libnetcdf-dev
    echo "Installed dev packages (fallback)"
fi

rm -rf /var/lib/apt/lists/*
echo "Dependencies installed successfully"

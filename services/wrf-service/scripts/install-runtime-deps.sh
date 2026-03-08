#!/bin/bash
# =============================================================================
# WRF Service - Runtime Dependencies Installation Script
# =============================================================================
# This script installs runtime dependencies for the WRF service Docker image.
# Package names may vary between Debian versions.
# =============================================================================

set -e

echo "Installing WRF Service runtime dependencies..."

# Update package lists
apt-get update

# Install HDF5 runtime library
# Try newer package names first (Debian 12+/trixie), then older ones
if apt-cache show libhdf5-310 &> /dev/null; then
    echo "Installing libhdf5-310..."
    apt-get install -y --no-install-recommends libhdf5-310
elif apt-cache show libhdf5-103-1 &> /dev/null; then
    echo "Installing libhdf5-103-1..."
    apt-get install -y --no-install-recommends libhdf5-103-1
elif apt-cache show libhdf5-103 &> /dev/null; then
    echo "Installing libhdf5-103..."
    apt-get install -y --no-install-recommends libhdf5-103
elif apt-cache show libhdf5-100 &> /dev/null; then
    echo "Installing libhdf5-100..."
    apt-get install -y --no-install-recommends libhdf5-100
else
    echo "Installing libhdf5-310 (fallback)..."
    apt-get install -y --no-install-recommends libhdf5-310 || \
    apt-get install -y --no-install-recommends libhdf5-dev
fi

# Install NetCDF runtime library
# Try newer package names first (Debian 12+/trixie), then older ones
if apt-cache show libnetcdf20 &> /dev/null; then
    echo "Installing libnetcdf20..."
    apt-get install -y --no-install-recommends libnetcdf20
elif apt-cache show libnetcdf19 &> /dev/null; then
    echo "Installing libnetcdf19..."
    apt-get install -y --no-install-recommends libnetcdf19
elif apt-cache show libnetcdf-20 &> /dev/null; then
    echo "Installing libnetcdf-20..."
    apt-get install -y --no-install-recommends libnetcdf-20
elif apt-cache show libnetcdf-19 &> /dev/null; then
    echo "Installing libnetcdf-19..."
    apt-get install -y --no-install-recommends libnetcdf-19
elif apt-cache show libnetcdf-18 &> /dev/null; then
    echo "Installing libnetcdf-18..."
    apt-get install -y --no-install-recommends libnetcdf-18
else
    echo "Installing libnetcdf20 (fallback)..."
    apt-get install -y --no-install-recommends libnetcdf20 || \
    apt-get install -y --no-install-recommends libnetcdf-dev
fi

# Clean up
rm -rf /var/lib/apt/lists/*

echo "Runtime dependencies installed successfully."

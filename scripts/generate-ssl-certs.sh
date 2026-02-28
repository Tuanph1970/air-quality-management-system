#!/bin/bash
# =============================================================================
# Generate self-signed SSL certificates for development/staging
# =============================================================================
# Usage:
#   ./scripts/generate-ssl-certs.sh
#
# Generates:
#   nginx/ssl/nginx.crt  — self-signed certificate
#   nginx/ssl/nginx.key  — private key
#
# For production, replace these with real certificates from a CA such as
# Let's Encrypt (certbot) or a commercial provider.
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SSL_DIR="$PROJECT_ROOT/nginx/ssl"

echo "Generating self-signed SSL certificates..."
echo "Output directory: $SSL_DIR"

mkdir -p "$SSL_DIR"

openssl req -x509 -nodes -days 365 \
    -newkey rsa:2048 \
    -keyout "$SSL_DIR/nginx.key" \
    -out    "$SSL_DIR/nginx.crt" \
    -subj "/C=VN/ST=Hanoi/L=Hanoi/O=AQMS/OU=Development/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

chmod 600 "$SSL_DIR/nginx.key"
chmod 644 "$SSL_DIR/nginx.crt"

echo ""
echo "SSL certificates generated successfully:"
echo "  Certificate : $SSL_DIR/nginx.crt"
echo "  Private Key : $SSL_DIR/nginx.key"
echo ""
echo "NOTE: These are self-signed certificates for development only."
echo "      Replace with real certificates before deploying to production."

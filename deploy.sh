#!/usr/bin/env bash
# =============================================================================
# deploy.sh — Build and start the entire AQMS stack
# =============================================================================
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
NO_CACHE="${NO_CACHE:-false}"

echo "========================================"
echo "  Air Quality Management System"
echo "  Deployment Script"
echo "========================================"
echo ""
echo "Compose file : $COMPOSE_FILE"
echo "Working dir  : $PROJECT_ROOT"
echo ""

# ── 1. Check prerequisites ────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
  echo "[ERROR] Docker is not installed or not in PATH." >&2
  exit 1
fi

if ! docker compose version &>/dev/null; then
  echo "[ERROR] Docker Compose (v2) is not available." >&2
  exit 1
fi

# ── 2. Create .env if it doesn't exist ────────────────────────────────────────
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  echo "[INFO]  .env not found — copying .env.example to .env"
  cp .env.example .env
fi

# ── 3. Build images ────────────────────────────────────────────────────────────
BUILD_FLAGS=""
if [ "$NO_CACHE" = "true" ]; then
  echo "[INFO]  Building with --no-cache"
  BUILD_FLAGS="--no-cache"
fi

echo "[INFO]  Building all Docker images..."
docker compose -f "$COMPOSE_FILE" build $BUILD_FLAGS

# ── 4. Start stack ─────────────────────────────────────────────────────────────
echo ""
echo "[INFO]  Starting all services..."
docker compose -f "$COMPOSE_FILE" up -d

# ── 5. Wait for health checks ─────────────────────────────────────────────────
echo ""
echo "[INFO]  Waiting for services to become healthy..."

wait_healthy() {
  local service="$1"
  local max_wait="${2:-60}"
  local elapsed=0
  local interval=3

  while [ $elapsed -lt $max_wait ]; do
    status=$(docker compose -f "$COMPOSE_FILE" ps "$service" --format json 2>/dev/null \
             | python3 -c "import sys,json; data=json.load(sys.stdin); print(data.get('Health','unknown'))" 2>/dev/null || echo "unknown")
    if [ "$status" = "healthy" ]; then
      echo "  ✓  $service is healthy"
      return 0
    fi
    sleep $interval
    elapsed=$((elapsed + interval))
  done

  echo "  ⚠  $service did not become healthy within ${max_wait}s (current: $status)"
  return 0  # non-fatal
}

wait_healthy mysql      90
wait_healthy rabbitmq   90
wait_healthy redis      30
wait_healthy user-service      60
wait_healthy factory-service   60
wait_healthy sensor-service    60
wait_healthy alert-service     60
wait_healthy air-quality-service 60
wait_healthy remote-sensing-service 60
wait_healthy api-gateway       60

# ── 6. Summary ────────────────────────────────────────────────────────────────
echo ""
echo "========================================"
echo "  Services"
echo "========================================"
docker compose -f "$COMPOSE_FILE" ps

echo ""
echo "========================================"
echo "  Endpoints"
echo "========================================"
echo "  Frontend        : http://localhost:3000"
echo "  API Gateway     : http://localhost:8000"
echo "  API Docs        : http://localhost:8000/docs"
echo "  RabbitMQ Mgmt   : http://localhost:15672  (guest/guest)"
echo "========================================"
echo ""
echo "[INFO]  Deployment complete."

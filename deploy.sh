#!/usr/bin/env bash
# =============================================================================
# deploy.sh — Build and start the entire AQMS stack
# =============================================================================
set -uo pipefail

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

# ── 3. Build frontend locally (avoids npm registry network issues inside Docker) ──
echo "[INFO]  Building frontend (npm install + vite build)..."
(
  cd "$PROJECT_ROOT/frontend"
  if [ ! -d node_modules ]; then
    echo "[INFO]  Installing frontend dependencies..."
    npm install --no-audit --no-fund
  fi
  npm run build
)
echo "[INFO]  Frontend built successfully."
echo ""

# ── 4. Build Docker images ────────────────────────────────────────────────────
BUILD_FLAGS=""
if [ "$NO_CACHE" = "true" ]; then
  echo "[INFO]  Building with --no-cache"
  BUILD_FLAGS="--no-cache"
fi

echo "[INFO]  Building all Docker images..."
docker compose -f "$COMPOSE_FILE" build $BUILD_FLAGS

# ── 5. Start stack ─────────────────────────────────────────────────────────────
echo ""
echo "[INFO]  Starting all services..."
# Allow partial failures — individual health is checked below
docker compose -f "$COMPOSE_FILE" up -d || true

# ── 6. Wait for health checks ─────────────────────────────────────────────────
echo ""
echo "[INFO]  Waiting for services to become healthy..."

FAILED_SERVICES=()

# Uses `docker inspect` to avoid NDJSON parsing issues with `docker compose ps --format json`
wait_healthy() {
  local service="$1"
  local max_wait="${2:-120}"
  local elapsed=0
  local interval=5
  local container="aqms-${service}"

  while [ $elapsed -lt $max_wait ]; do
    local inspect_out
    inspect_out=$(docker inspect "$container" \
      --format='{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' \
      2>/dev/null || echo "notfound no-healthcheck")

    local cstate chealth
    cstate=$(echo "$inspect_out" | awk '{print $1}')
    chealth=$(echo "$inspect_out" | awk '{print $2}')

    if [ "$chealth" = "healthy" ]; then
      echo "  ✓  $service is healthy (${elapsed}s)"
      return 0
    fi

    # Container exited / crashed — no point waiting further
    if [ "$cstate" = "exited" ] || [ "$cstate" = "dead" ]; then
      echo "  ✗  $service stopped unexpectedly (state=$cstate). Last 40 log lines:"
      docker logs --tail=40 "$container" 2>&1 | sed 's/^/        /'
      return 1
    fi

    sleep $interval
    elapsed=$((elapsed + interval))
  done

  echo "  ⚠  $service not healthy after ${max_wait}s (state=$cstate, health=$chealth)"
  return 1
}

check() {
  local svc="$1"; shift
  if ! wait_healthy "$svc" "$@"; then
    FAILED_SERVICES+=("$svc")
  fi
}

check mysql      120
check rabbitmq   120
check redis       60
check user-service      120
check factory-service   120
check sensor-service    120
check alert-service     150
check air-quality-service 120
check remote-sensing-service 120
check wrf-service       120
check station-service   120
check purpleair-ingestion-service 120
check station-ingestion-service 120
check station-excel-fetcher 120
check frontend            60
check api-gateway       120

# ── 7. Summary ────────────────────────────────────────────────────────────────
echo ""
echo "========================================"
echo "  Services"
echo "========================================"
docker compose -f "$COMPOSE_FILE" ps

echo ""
echo "========================================"
echo "  Endpoints"
echo "========================================"
echo "  Frontend        : http://localhost:3002"
echo "  API Gateway     : http://localhost:8000"
echo "  API Docs        : http://localhost:8000/docs"
echo "  RabbitMQ Mgmt   : http://localhost:15672  (guest/guest)"
echo "========================================"
echo ""

if [ ${#FAILED_SERVICES[@]} -gt 0 ]; then
  echo "[WARN]  The following services did not reach healthy state:"
  for svc in "${FAILED_SERVICES[@]}"; do
    echo "          • $svc  (run: docker logs aqms-${svc})"
  done
  echo ""
  echo "[INFO]  Deployment finished with warnings."
  exit 1
else
  echo "[INFO]  Deployment complete — all services healthy."
fi

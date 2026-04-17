#!/usr/bin/env bash
# =============================================================================
# deploy.sh — Build and start the AQMS stack (dev or production)
#
# Usage:
#   ./deploy.sh              Dev stack  (docker-compose.yml, .env)
#   ./deploy.sh --prod       Prod stack (docker-compose.prod.yml, .env.prod)
#   ./deploy.sh --prod -e DB_PASSWORD=xxx ...   Override specific vars
#
# For remote server: clone repo, then run:
#   ./deploy.sh --prod \
#     -e DB_PASSWORD="$(openssl rand -hex 24)" \
#     -e JWT_SECRET="$(openssl rand -hex 32)" \
#     -e RABBITMQ_PASS="$(openssl rand -hex 24)" \
#     -e REDIS_PASSWORD="$(openssl rand -hex 24)" \
#     -e ENVISOFT_BASIC_PASS=... \
#     -e ENVISOFT_FORM_PASS=...
# =============================================================================
set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# ── Parse flags ──────────────────────────────────────────────────────────────
PROD_MODE=false
NO_CACHE=false
ENV_FILE=".env"
COMPOSE_FILE="docker-compose.yml"
EXTRA_ENV_VARS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prod)
      PROD_MODE=true
      ENV_FILE=".env.prod"
      COMPOSE_FILE="docker-compose.prod.yml"
      shift
      ;;
    --no-cache)
      NO_CACHE=true
      shift
      ;;
    -e)
      EXTRA_ENV_VARS+=("$2")
      shift 2
      ;;
    *)
      echo "[ERROR] Unknown argument: $1" >&2
      echo "Usage: $0 [--prod] [--no-cache] [-e KEY=VALUE]..." >&2
      exit 1
      ;;
  esac
done

# ── 1. Prerequisites ─────────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
  echo "[ERROR] Docker is not installed or not in PATH." >&2
  exit 1
fi

if ! docker compose version &>/dev/null; then
  echo "[ERROR] Docker Compose (v2) is not available." >&2
  exit 1
fi

# ── 2. Validate env file ─────────────────────────────────────────────────────
if [ ! -f "$ENV_FILE" ]; then
  echo "[ERROR] $ENV_FILE not found." >&2
  echo "        For production: cp .env.prod.example .env.prod and fill in secrets." >&2
  exit 1
fi

echo "========================================"
echo "  Air Quality Management System"
echo "  Deploy Script"
echo "========================================"
echo ""
echo "Mode           : $([ "$PROD_MODE" = true ] && echo "PRODUCTION" || echo "DEVELOPMENT")"
echo "Compose file   : $COMPOSE_FILE"
echo "Env file       : $ENV_FILE"
echo "Extra env vars : ${EXTRA_ENV_VARS[*]:-none}"
echo "Working dir    : $PROJECT_ROOT"
echo ""

# ── 3. Warn about unset secrets in prod ─────────────────────────────────────
if [ "$PROD_MODE" = true ]; then
  # Source env file to check for empty secrets
  set -a
  # shellcheck source=/dev/null
  source "$ENV_FILE"
  set +a

  MISSING=()
  for var in DB_PASSWORD RABBITMQ_PASS REDIS_PASSWORD JWT_SECRET; do
    val="$(eval echo "\$$var")"
    if [ -z "$val" ]; then
      MISSING+=("$var")
    fi
  done

  if [ ${#MISSING[@]} -gt 0 ]; then
    echo "[WARN] The following secrets are EMPTY in $ENV_FILE:"
    for v in "${MISSING[@]}"; do echo "         • $v"; done
    echo ""
    echo "[WARN] Set them via:  ./deploy.sh --prod -e ${MISSING[0]}=value ..."
    echo ""
    read -r -p "Continue anyway? [y/N] " answer
    if [ "${answer,,}" != "y" ]; then
      echo "[ABORTED] Deploy cancelled."
      exit 1
    fi
  fi
fi

# ── 4. Frontend build ─────────────────────────────────────────────────────────
echo "[INFO]  Building frontend..."
(
  cd "$PROJECT_ROOT/frontend"

  if [ ! -d node_modules ]; then
    echo "[INFO]  Installing frontend dependencies..."
    npm install --no-audit --no-fund
  fi

  if [ "$PROD_MODE" = true ]; then
    # Production: relative API URL (nginx handles routing inside Docker)
    VITE_API_URL="/api/v1" \
    npm run build
  else
    # Development: proxy through vite dev server
    VITE_API_URL="http://localhost:8000/api/v1" \
    npm run build
  fi
)
echo "[INFO]  Frontend built."
echo ""

# ── 5. Build Docker images ────────────────────────────────────────────────────
BUILD_FLAGS=""
if [ "$NO_CACHE" = true ]; then
  echo "[INFO]  Building with --no-cache"
  BUILD_FLAGS="--no-cache"
fi

echo "[INFO]  Building Docker images..."
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build $BUILD_FLAGS

# ── 6. Start stack ─────────────────────────────────────────────────────────────
echo ""
echo "[INFO]  Starting all services..."
# Allow partial failures — individual health is checked below
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d "${EXTRA_ENV_VARS[@]}" || true

# ── 7. Wait for health checks ─────────────────────────────────────────────────
echo ""
echo "[INFO]  Waiting for services to become healthy..."

FAILED_SERVICES=()

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

check rabbitmq     120
check redis         60
check user-db      120
check factory-db   120
check sensor-db    120
check alert-db     120
check remote-sensing-db  120
check station-db   120
check wrf-db       120
check station-excel-fetcher-db 120
check user-service      120
check factory-service   120
check sensor-service    120
check alert-service     150
check air-quality-service 120
check remote-sensing-service 120
check station-service   120
check wrf-service       120
check station-excel-fetcher 120
check frontend            60
check api-gateway       120

# ── 8. Summary ────────────────────────────────────────────────────────────────
echo ""
echo "========================================"
echo "  Services"
echo "========================================"
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps

echo ""
echo "========================================"
echo "  Endpoints"
echo "========================================"
if [ "$PROD_MODE" = true ]; then
  echo "  Frontend        : http://<your-server-ip>"
  echo "  API Gateway     : http://<your-server-ip>/api/v1"
  echo "  API Docs        : http://<your-server-ip>/api/v1/docs"
  echo "  RabbitMQ Mgmt   : http://<your-server-ip>:15672"
else
  echo "  Frontend        : http://localhost:3002"
  echo "  API Gateway     : http://localhost:8000"
  echo "  API Docs        : http://localhost:8000/docs"
  echo "  RabbitMQ Mgmt   : http://localhost:15672  (guest/guest)"
fi
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

#!/usr/bin/env bash
# =============================================================================
# undeploy.sh — Stop and completely remove the AQMS stack
#               Removes containers, images, volumes, and networks.
# =============================================================================
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"

echo "========================================"
echo "  Air Quality Management System"
echo "  Undeploy Script"
echo "========================================"
echo ""
echo "Compose file : $COMPOSE_FILE"
echo "Working dir  : $PROJECT_ROOT"
echo ""

# ── Confirmation prompt ───────────────────────────────────────────────────────
echo "WARNING: This will remove all containers, images, volumes, and networks"
echo "         associated with this project. All stored data will be DELETED."
echo ""
read -r -p "Are you sure you want to continue? [y/N] " confirm
case "$confirm" in
  [yY][eE][sS]|[yY])
    ;;
  *)
    echo "Aborted."
    exit 0
    ;;
esac
echo ""

# ── 1. Stop and remove containers + networks ──────────────────────────────────
echo "[INFO]  Stopping and removing containers and networks..."
docker compose -f "$COMPOSE_FILE" down --remove-orphans

# ── 2. Remove named volumes (database data, etc.) ─────────────────────────────
echo "[INFO]  Removing volumes..."
docker compose -f "$COMPOSE_FILE" down --volumes 2>/dev/null || true

# ── 3. Remove project images ──────────────────────────────────────────────────
echo "[INFO]  Removing project Docker images..."
PROJECT_NAME=$(basename "$PROJECT_ROOT" | tr '[:upper:]' '[:lower:]' | tr -cd '[:alnum:]-_')

# Collect image IDs for images built by this compose project
IMAGE_IDS=$(docker compose -f "$COMPOSE_FILE" images -q 2>/dev/null || true)
if [ -n "$IMAGE_IDS" ]; then
  echo "  Removing images: $(echo "$IMAGE_IDS" | tr '\n' ' ')"
  echo "$IMAGE_IDS" | xargs docker rmi -f 2>/dev/null || true
else
  # Fallback: remove by name pattern (project prefix)
  docker images --format "{{.Repository}}:{{.Tag}}" \
    | grep -E "^(${PROJECT_NAME}|air-quality)" \
    | xargs docker rmi -f 2>/dev/null || true
fi

# ── 4. Remove dangling build cache ───────────────────────────────────────────
echo "[INFO]  Pruning dangling build cache..."
docker builder prune -f --filter "until=24h" 2>/dev/null || true

# ── 5. Final status ───────────────────────────────────────────────────────────
echo ""
echo "[INFO]  Verifying removal — remaining containers:"
REMAINING=$(docker compose -f "$COMPOSE_FILE" ps -q 2>/dev/null || true)
if [ -z "$REMAINING" ]; then
  echo "  (none)"
else
  docker compose -f "$COMPOSE_FILE" ps
fi

echo ""
echo "[INFO]  Undeploy complete. All project resources have been removed."

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

# ── 1. Stop containers, remove networks, volumes, and all project images ───────
echo "[INFO]  Stopping containers and removing networks, volumes, and images..."
# --rmi all  : removes every image referenced by the compose file (built + pulled)
# --volumes  : removes named and anonymous volumes
docker compose -f "$COMPOSE_FILE" down --remove-orphans --volumes --rmi all 2>/dev/null || true

# ── 2. Remove ALL build cache (no time filter) ────────────────────────────────
echo "[INFO]  Pruning all build cache..."
docker builder prune -f 2>/dev/null || true

# ── 3. Remove remaining dangling images ───────────────────────────────────────
echo "[INFO]  Removing dangling images..."
docker image prune -f 2>/dev/null || true

# ── 4. Final status ───────────────────────────────────────────────────────────
echo ""
echo "[INFO]  Verifying removal — remaining containers:"
REMAINING=$(docker compose -f "$COMPOSE_FILE" ps -q 2>/dev/null || true)
if [ -z "$REMAINING" ]; then
  echo "  (none)"
else
  docker compose -f "$COMPOSE_FILE" ps
fi

echo ""
echo "[INFO]  Disk usage after cleanup:"
docker system df

echo ""
echo "[INFO]  Undeploy complete. All project resources have been removed."

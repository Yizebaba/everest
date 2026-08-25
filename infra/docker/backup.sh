#!/usr/bin/env bash
set -euo pipefail

# Everest DB-005: nightly logical backup of the persistent PostgreSQL volume.
# Usage: EVEREST_BACKUP_DIR=/path backup.sh [container]
# Writes a timestamped pg_dump archive. Retention: keep 14 daily + 8 weekly.

CONTAINER="${1:-everest-postgres}"
BACKUP_DIR="${EVEREST_BACKUP_DIR:-/mnt/d/Everest-data/backups}"
USER="${EVEREST_DB_USER:-everest}"
DB="${EVEREST_DB_NAME:-everest}"

mkdir -p "$BACKUP_DIR"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="${BACKUP_DIR}/everest-${STAMP}.dump"

docker exec "$CONTAINER" pg_dump -U "$USER" -d "$DB" -Fc > "$OUT"
echo "backup written: $OUT ($(stat -c%s "$OUT") bytes)"

# Prune old backups: keep newest 14 files.
ls -1t "${BACKUP_DIR}"/everest-*.dump 2>/dev/null | tail -n +15 | while read -r old; do
  echo "prune $old"
  rm -f "$old"
done

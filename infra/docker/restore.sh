#!/usr/bin/env bash
set -euo pipefail

# Everest DB-005: restore a pg_dump archive into the persistent PostgreSQL.
# Usage: restore.sh <backup-file>
# Stop condition: refuse to restore over a non-empty database without FORCE=1.

BACKUP="${1:?usage: restore.sh <backup-file>}"
CONTAINER="${2:-everest-postgres}"
USER="${EVEREST_DB_USER:-everest}"
DB="${EVEREST_DB_NAME:-everest}"

[ -f "$BACKUP" ] || { echo "backup file not found: $BACKUP" >&2; exit 1; }

EXISTING="$(docker exec "$CONTAINER" psql -U "$USER" -d "$DB" -Atc \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")"
if [ "${EXISTING:-0}" != "0" ] && [ "${FORCE:-}" != "1" ]; then
  echo "database has $EXISTING tables; set FORCE=1 to overwrite (destructive)" >&2
  exit 1
fi

docker exec -i "$CONTAINER" pg_restore -U "$USER" -d "$DB" --clean --if-exists < "$BACKUP"
echo "restore complete from $BACKUP"

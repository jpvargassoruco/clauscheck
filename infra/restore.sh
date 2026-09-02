#!/usr/bin/env bash
# Restore a backup produced by infra/backup.sh.
# Usage: infra/restore.sh <timestamp>   (matches a backups/<timestamp>/ dir)
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

TS="${1:-}"
if [ -z "$TS" ]; then
  echo "usage: infra/restore.sh <timestamp>" >&2
  echo "available backups:" >&2
  ls -1 backups/ 2>/dev/null >&2 || true
  exit 1
fi

SRC="backups/${TS}"
if [ ! -d "$SRC" ]; then
  echo "no such backup: ${SRC}" >&2
  exit 1
fi

DC="docker compose -f infra/docker-compose.yml --env-file .env"

echo "==> This will DROP and recreate clauscheck/paperless DBs and overwrite"
echo "    infra/data/paperless/{data,media}. Ctrl-C now to abort."
read -r -p "Type 'yes' to continue: " CONFIRM
[ "$CONFIRM" = "yes" ] || { echo "aborted"; exit 1; }

echo "==> Stopping api/worker/paperless (keep postgres/redis up)"
$DC --profile app stop api worker paperless 2>/dev/null || true

echo "==> Restoring clauscheck DB"
$DC exec -T postgres psql -U postgres -d postgres -c "DROP DATABASE IF EXISTS clauscheck;"
$DC exec -T postgres psql -U postgres -d postgres -c "CREATE DATABASE clauscheck;"
$DC exec -T postgres psql -U postgres -d clauscheck -c "CREATE EXTENSION IF NOT EXISTS vector;"
gunzip -c "${SRC}/clauscheck.sql.gz" | $DC exec -T postgres psql -U postgres -d clauscheck

echo "==> Restoring paperless DB"
$DC exec -T postgres psql -U postgres -d postgres -c "DROP DATABASE IF EXISTS paperless;"
$DC exec -T postgres psql -U postgres -d postgres -c "CREATE DATABASE paperless;"
gunzip -c "${SRC}/paperless.sql.gz" | $DC exec -T postgres psql -U postgres -d paperless

echo "==> Restoring paperless media/data"
rm -rf infra/data/paperless/data infra/data/paperless/media
tar -xzf "${SRC}/paperless-media.tar.gz" -C infra/data/paperless

echo "==> Restarting stack"
$DC up -d

echo "==> Restore from ${SRC} complete"

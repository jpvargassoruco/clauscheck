#!/usr/bin/env bash
# Dump both Postgres DBs + tar the paperless media/data dirs into
# backups/<timestamp>/. Run from repo root (or anywhere, paths are
# resolved relative to this script).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DC="docker compose -f infra/docker-compose.yml --env-file .env"
TS="$(date +%Y%m%d-%H%M%S)"
OUT="backups/${TS}"
mkdir -p "$OUT"

echo "==> Dumping clauscheck DB"
$DC exec -T postgres pg_dump -U postgres -d clauscheck | gzip > "${OUT}/clauscheck.sql.gz"

echo "==> Dumping paperless DB"
$DC exec -T postgres pg_dump -U postgres -d paperless | gzip > "${OUT}/paperless.sql.gz"

echo "==> Archiving paperless media/data"
tar -czf "${OUT}/paperless-media.tar.gz" -C infra/data/paperless data media

echo "==> Backup written to ${OUT}"

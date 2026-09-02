#!/usr/bin/env bash
# Phase B: deploy the latest main to the COTAS VM over SSH. Run from a
# workstation with SSH access to the VM. NOT executed automatically.
#
# Usage: DEPLOY_HOST=user@vm.example DEPLOY_PATH=/opt/clauscheck ./deploy.sh
set -euo pipefail

: "${DEPLOY_HOST:?set DEPLOY_HOST, e.g. deploy@10.8.0.5}"
DEPLOY_PATH="${DEPLOY_PATH:-/opt/clauscheck}"

echo "==> Deploying to ${DEPLOY_HOST}:${DEPLOY_PATH}"
ssh "${DEPLOY_HOST}" bash -s <<REMOTE
set -euo pipefail
cd "${DEPLOY_PATH}"

echo "==> git pull"
git pull --ff-only

echo "==> docker compose up -d --build (profiles: app, edge)"
docker compose -f infra/docker-compose.yml --env-file .env --profile app --profile edge up -d --build

echo "==> alembic upgrade head"
docker compose -f infra/docker-compose.yml --env-file .env exec -T api alembic upgrade head

echo "==> deploy done"
REMOTE

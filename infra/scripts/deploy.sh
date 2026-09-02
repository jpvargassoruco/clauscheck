#!/usr/bin/env bash
# Phase B: deploy the latest main to the COTAS VM over SSH. Run from a
# workstation with SSH access to the VM. NOT executed automatically.
#
# Brings up the `app` profile only (no `edge`/cloudflared - that profile is
# enabled separately once CF_TUNNEL_TOKEN is provided).
#
# Usage: VPS_HOST=10.40.2.235 VPS_USER=ubuntu VPS_KEY=~/.ssh/id_ed25519 ./deploy.sh
set -euo pipefail

: "${VPS_HOST:?set VPS_HOST, e.g. 10.40.2.235}"
VPS_USER="${VPS_USER:-ubuntu}"
: "${VPS_KEY:?set VPS_KEY, path to the ssh private key for ${VPS_USER}@${VPS_HOST}}"
DEPLOY_PATH="${DEPLOY_PATH:-/opt/clauscheck}"

SSH_CMD=(ssh -i "${VPS_KEY}" "${VPS_USER}@${VPS_HOST}")

echo "==> Deploying to ${VPS_USER}@${VPS_HOST}:${DEPLOY_PATH}"
"${SSH_CMD[@]}" DEPLOY_PATH="${DEPLOY_PATH}" bash -s <<'REMOTE'
set -euo pipefail
cd "${DEPLOY_PATH}"

echo "==> git pull"
git pull --ff-only

echo "==> building web (node:22 one-off container -> web/dist)"
docker run --rm -v "${DEPLOY_PATH}/web:/w" -w /w node:22 sh -c "npm ci && npm run build" < /dev/null

echo "==> docker compose up -d --build (profile: app)"
docker compose -f infra/docker-compose.yml --env-file .env --profile app up -d --build < /dev/null

echo "==> alembic upgrade head"
docker compose -f infra/docker-compose.yml --env-file .env exec -T api alembic upgrade head < /dev/null

echo "==> health check"
sleep 5
curl -fs localhost:8080/api/v1/health && echo
REMOTE

echo "==> deploy done"

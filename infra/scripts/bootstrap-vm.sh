#!/usr/bin/env bash
# Phase B: one-time bootstrap of a fresh Ubuntu 24.04 VM (COTAS cloud) to
# host ClausCheck behind a Cloudflare Tunnel. Run as root (or via sudo) on
# the target VM itself. NOT executed automatically — review before running.
#
# Usage: VPN_SUBNET=10.8.0.0/24 REPO_URL=git@github.com:jpvargassoruco/clauscheck.git \
#          ./bootstrap-vm.sh
set -euo pipefail

: "${VPN_SUBNET:?set VPN_SUBNET, e.g. 10.8.0.0/24 (only SSH from here is allowed)}"
REPO_URL="${REPO_URL:-git@github.com:jpvargassoruco/clauscheck.git}"
REPO_PATH="${REPO_PATH:-/opt/clauscheck}"
DEPLOY_USER="${DEPLOY_USER:-$(logname 2>/dev/null || echo "$SUDO_USER")}"

echo "==> Updating base system"
apt-get update -y
apt-get upgrade -y

echo "==> Installing prerequisites"
apt-get install -y ca-certificates curl gnupg ufw unattended-upgrades git

echo "==> Installing Docker CE + compose plugin (official repo)"
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
ARCH="$(dpkg --print-architecture)"
CODENAME="$(. /etc/os-release && echo "$VERSION_CODENAME")"
echo "deb [arch=${ARCH} signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${CODENAME} stable" \
  > /etc/apt/sources.list.d/docker.list
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

if [ -n "${DEPLOY_USER:-}" ] && [ "${DEPLOY_USER}" != "root" ]; then
  usermod -aG docker "${DEPLOY_USER}"
  echo "==> Added ${DEPLOY_USER} to the docker group (re-login required)"
fi

echo "==> Configuring ufw (deny incoming by default; SSH only from ${VPN_SUBNET})"
ufw default deny incoming
ufw default allow outgoing
ufw allow from "${VPN_SUBNET}" to any port 22 proto tcp
# HTTP/HTTPS/edge traffic reaches the box via the Cloudflare Tunnel
# (outbound-only), so no inbound 80/443 rule is opened here.
ufw --force enable

echo "==> Enabling unattended-upgrades"
dpkg-reconfigure -f noninteractive unattended-upgrades
systemctl enable --now unattended-upgrades

echo "==> Cloning repo to ${REPO_PATH}"
if [ -d "${REPO_PATH}/.git" ]; then
  echo "    already present, skipping clone"
else
  git clone "${REPO_URL}" "${REPO_PATH}"
fi
if [ -n "${DEPLOY_USER:-}" ] && [ "${DEPLOY_USER}" != "root" ]; then
  chown -R "${DEPLOY_USER}:${DEPLOY_USER}" "${REPO_PATH}"
fi

cat <<EOF

==> Bootstrap done.
Next steps (manual):
  1. Copy infra/.env.example to ${REPO_PATH}/.env and fill in secrets
     (POSTGRES_PASSWORD, PAPERLESS_*, JWT_SECRET, FERNET_KEY, DEEPSEEK_*,
     CF_TUNNEL_TOKEN, ...).
  2. Log out/in (or newgrp docker) for the docker group membership to apply.
  3. Run infra/scripts/deploy.sh from your workstation to bring the stack up.
EOF

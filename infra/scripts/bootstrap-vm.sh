#!/usr/bin/env bash
# Phase B: one-time bootstrap of a fresh Ubuntu 24.04 VM (COTAS cloud) to
# host ClausCheck behind a Cloudflare Tunnel. Run as root (or via sudo) on
# the target VM itself. NOT executed automatically - review before running.
#
# The VM has only a private IP inside the COTAS tenant network (no public
# IP), so SSH (22/tcp) is allowed from anywhere; every other inbound port
# stays denied. HTTP/HTTPS/edge traffic reaches the box via the outbound-only
# Cloudflare Tunnel once that profile is enabled (Phase B, later).
#
# Usage: ./bootstrap-vm.sh
set -euo pipefail

DEPLOY_USER="${DEPLOY_USER:-$(logname 2>/dev/null || echo "${SUDO_USER:-}")}"

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

echo "==> Configuring ufw (deny incoming by default; allow SSH from anywhere; allow outgoing)"
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw --force enable

echo "==> Setting timezone to America/La_Paz"
timedatectl set-timezone America/La_Paz

echo "==> Enabling unattended-upgrades"
dpkg-reconfigure -f noninteractive unattended-upgrades
systemctl enable --now unattended-upgrades

cat <<EOF

==> Bootstrap done.
Next steps (manual):
  1. Generate a deploy key on this VM, register it as a read-only GitHub
     deploy key, and clone the repo into /opt/clauscheck.
  2. Copy infra/.env.example to /opt/clauscheck/.env and fill in secrets
     (POSTGRES_PASSWORD, PAPERLESS_*, JWT_SECRET, FERNET_KEY, DEEPSEEK_*,
     CF_TUNNEL_TOKEN once Phase B edge is enabled, ...).
  3. Log out/in (or newgrp docker) for the docker group membership to apply.
  4. Run infra/scripts/deploy.sh from your workstation to bring the stack up.
EOF

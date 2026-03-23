#!/bin/bash
# ── EnderPanel VPS Setup ──────────────────────────────────────────────────────
# Run this ONCE on your Contabo VPS to set up Nginx and the folder structure.
# Usage: bash setup_vps.sh

set -e

GREEN='\033[0;32m'; CYAN='\033[0;36m'; NC='\033[0m'; BOLD='\033[1m'
ok()   { echo -e "  ${GREEN}✓${NC}  $1"; }
info() { echo -e "  ${CYAN}→${NC}  $1"; }

echo ""
echo -e "  ${BOLD}Setting up EnderPanel VPS...${NC}"
echo ""

# Install nginx
info "Installing Nginx..."
apt-get update -qq
apt-get install -y -qq nginx
ok "Nginx installed"

# Create folder structure
info "Creating folder structure..."
mkdir -p /var/www/enderpanel/{website,releases}
ok "Folders created at /var/www/enderpanel/"

# Copy nginx config
info "Installing Nginx config..."
cp /tmp/nginx.conf /etc/nginx/sites-available/enderpanel
ln -sf /etc/nginx/sites-available/enderpanel /etc/nginx/sites-enabled/enderpanel
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
ok "Nginx configured"

echo ""
echo -e "  ${GREEN}${BOLD}VPS setup complete!${NC}"
echo ""
echo -e "  Your VPS is now serving from: ${CYAN}http://144.91.87.66/${NC}"
echo ""
echo -e "  Next step: run ${BOLD}./Scripts/package_release.sh 1.0.0${NC} on your Mac"
echo ""

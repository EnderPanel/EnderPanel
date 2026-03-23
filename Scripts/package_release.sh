 #!/bin/bash
# ── EnderPanel Release Packager ───────────────────────────────────────────────
# Run this on your Mac to build a release and upload it to your VPS.
# Usage: ./Scripts/package_release.sh 1.0.0

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; NC='\033[0m'; BOLD='\033[1m'
ok()   { echo -e "  ${GREEN}✓${NC}  $1"; }
err()  { echo -e "  ${RED}✗${NC}  $1"; exit 1; }
info() { echo -e "  ${CYAN}→${NC}  $1"; }

VERSION=${1:-"1.0.0"}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
DIST_DIR="$ROOT_DIR/dist"
RELEASE_NAME="enderpanel-${VERSION}"

# ── Config ────────────────────────────────────────────────────────────────────
VPS_USER="root"
VPS_HOST="144.91.87.66"          # Contabo VPS
VPS_WEB_DIR="/var/www/enderpanel"
# ──────────────────────────────────────────────────────────────────────────────

echo ""
echo -e "  ${BOLD}Packaging EnderPanel v${VERSION}${NC}"
echo ""

# Build frontend first
info "Building frontend..."
cd "$ROOT_DIR/frontend"
npm run build --silent
ok "Frontend built"

# Create dist folder
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR/$RELEASE_NAME"

# Copy backend
info "Copying backend..."
rsync -a --exclude='__pycache__' \
         --exclude='*.pyc' \
         --exclude='mcpanel.db' \
         --exclude='servers/' \
         --exclude='avatars/' \
         "$ROOT_DIR/backend/" "$DIST_DIR/$RELEASE_NAME/backend/"
ok "Backend copied"

# Copy built frontend
info "Copying frontend..."
mkdir -p "$DIST_DIR/$RELEASE_NAME/frontend"
cp -r "$ROOT_DIR/frontend/dist" "$DIST_DIR/$RELEASE_NAME/frontend/dist"
cp "$ROOT_DIR/frontend/package.json" "$DIST_DIR/$RELEASE_NAME/frontend/"
cp "$ROOT_DIR/frontend/package-lock.json" "$DIST_DIR/$RELEASE_NAME/frontend/" 2>/dev/null || true
ok "Frontend copied"

# Copy install scripts
cp "$ROOT_DIR/install.sh" "$DIST_DIR/$RELEASE_NAME/"
cp "$ROOT_DIR/install.ps1" "$DIST_DIR/$RELEASE_NAME/" 2>/dev/null || true

# Write version file
echo "$VERSION" > "$DIST_DIR/$RELEASE_NAME/VERSION"

# Create tarball
info "Creating tarball..."
cd "$DIST_DIR"
tar -czf "${RELEASE_NAME}.tar.gz" "$RELEASE_NAME"
rm -rf "$DIST_DIR/$RELEASE_NAME"
ok "Created dist/${RELEASE_NAME}.tar.gz ($(du -sh "${RELEASE_NAME}.tar.gz" | cut -f1))"

# Update latest txt
echo "$VERSION" > "$DIST_DIR/latest.txt"

# Upload to VPS
echo ""
info "Uploading to VPS (${VPS_HOST})..."
ssh "$VPS_USER@$VPS_HOST" "mkdir -p $VPS_WEB_DIR/releases"
scp "$DIST_DIR/${RELEASE_NAME}.tar.gz" "$VPS_USER@$VPS_HOST:$VPS_WEB_DIR/releases/"
scp "$ROOT_DIR/install.sh"             "$VPS_USER@$VPS_HOST:$VPS_WEB_DIR/"
scp "$DIST_DIR/latest.txt"             "$VPS_USER@$VPS_HOST:$VPS_WEB_DIR/"

# Create latest symlink on VPS
ssh "$VPS_USER@$VPS_HOST" \
  "ln -sf $VPS_WEB_DIR/releases/${RELEASE_NAME}.tar.gz $VPS_WEB_DIR/releases/latest.tar.gz"

ok "Uploaded to VPS"

echo ""
echo -e "  ${GREEN}${BOLD}Release v${VERSION} published!${NC}"
echo ""
echo -e "  Install URL:  ${CYAN}curl -sSL http://144.91.87.66/install.sh | bash${NC}"
echo -e "  Download URL: ${CYAN}http://144.91.87.66/releases/${RELEASE_NAME}.tar.gz${NC}"
echo ""

#!/bin/bash
# ── EnderPanel Release Packager ───────────────────────────────────────────────

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; NC='\033[0m'; BOLD='\033[1m'
ok()   { echo -e "  ${GREEN}✓${NC}  $1"; }
err()  { echo -e "  ${RED}✗${NC}  $1"; exit 1; }
info() { echo -e "  ${CYAN}→${NC}  $1"; }

VERSION=${1:-"1.0.0"}
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="$ROOT_DIR/dist"
RELEASE_NAME="enderpanel-${VERSION}"
RELEASE_DIR="$DIST_DIR/$RELEASE_NAME"

VPS_USER="root"
VPS_HOST="144.91.87.66"
VPS_WEB_DIR="/var/www/enderpanel"

echo ""
echo -e "  ${BOLD}Packaging EnderPanel v${VERSION}${NC}"
echo -e "  Root: $ROOT_DIR"
echo ""

# Build frontend
info "Building frontend..."
cd "$ROOT_DIR/frontend"
npm run build
cd "$ROOT_DIR"
ok "Frontend built"

# Create release folder
rm -rf "$DIST_DIR"
mkdir -p "$RELEASE_DIR"

# Copy backend
info "Copying backend..."
rsync -a --exclude='__pycache__' --exclude='*.pyc' --exclude='mcpanel.db' --exclude='servers/' --exclude='avatars/' "$ROOT_DIR/backend/" "$RELEASE_DIR/backend/"
cp "$ROOT_DIR/backend/Dockerfile" "$RELEASE_DIR/backend/"
ok "Backend copied"

# Copy frontend - explicitly copy each item
info "Copying frontend..."
mkdir -p "$RELEASE_DIR/frontend"
cp "$ROOT_DIR/frontend/index.html" "$RELEASE_DIR/frontend/"
cp "$ROOT_DIR/frontend/package.json" "$RELEASE_DIR/frontend/"
cp "$ROOT_DIR/frontend/package-lock.json" "$RELEASE_DIR/frontend/" 2>/dev/null || true
cp "$ROOT_DIR/frontend/vite.config.js" "$RELEASE_DIR/frontend/"
cp "$ROOT_DIR/frontend/tailwind.config.js" "$RELEASE_DIR/frontend/"
cp "$ROOT_DIR/frontend/postcss.config.js" "$RELEASE_DIR/frontend/"
cp -r "$ROOT_DIR/frontend/src" "$RELEASE_DIR/frontend/"
cp -r "$ROOT_DIR/frontend/dist" "$RELEASE_DIR/frontend/"
ok "Frontend copied"

# Copy install scripts
cp "$ROOT_DIR/install.sh" "$RELEASE_DIR/"
cp "$ROOT_DIR/install.ps1" "$RELEASE_DIR/" 2>/dev/null || true
cp "$ROOT_DIR/package.json" "$RELEASE_DIR/"

# Create .env template
cat > "$RELEASE_DIR/.env.example" << 'EOF'
DATABASE_URL=sqlite:///./mcpanel.db
SECRET_KEY=change-me-to-a-random-string
SERVERS_DIR=./servers
EOF

# Write version
echo "$VERSION" > "$RELEASE_DIR/VERSION"

# Create tarball
info "Creating tarball..."
cd "$DIST_DIR"
tar -czf "${RELEASE_NAME}.tar.gz" "$RELEASE_NAME"
rm -rf "$RELEASE_DIR"
ok "Created ${RELEASE_NAME}.tar.gz"

# Upload
echo ""
info "Uploading to VPS..."
ssh "$VPS_USER@$VPS_HOST" "mkdir -p $VPS_WEB_DIR/releases"
scp "$DIST_DIR/${RELEASE_NAME}.tar.gz" "$VPS_USER@$VPS_HOST:$VPS_WEB_DIR/releases/"
scp "$ROOT_DIR/install.sh" "$VPS_USER@$VPS_HOST:$VPS_WEB_DIR/"
echo "$VERSION" > "$DIST_DIR/latest.txt"
scp "$DIST_DIR/latest.txt" "$VPS_USER@$VPS_HOST:$VPS_WEB_DIR/"

# Fix symlink (relative path) and delete old releases
ssh "$VPS_USER@$VPS_HOST" "
  cd $VPS_WEB_DIR/releases
  rm -f latest.tar.gz
  ln -sf ${RELEASE_NAME}.tar.gz latest.tar.gz
  ls -t enderpanel-*.tar.gz | tail -n +4 | xargs -r rm -f
  echo 'Cleaned old releases'
"
ok "Uploaded"

echo ""
echo -e "  ${GREEN}${BOLD}Release v${VERSION} published!${NC}"
echo ""
echo -e "  curl -sSL https://enderpanel.space/install.sh | bash"
echo ""

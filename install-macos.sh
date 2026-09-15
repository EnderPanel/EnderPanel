#!/bin/bash
set -euo pipefail

BLUE='\033[1;34m'; GREEN='\033[1;32m'; YELLOW='\033[1;33m'; RED='\033[1;31m'; RESET='\033[0m'
step() { printf "\n${BLUE}==>${RESET} %s\n" "$1"; }
ok() { printf "${GREEN}[OK]${RESET} %s\n" "$1"; }
fail() { printf "${RED}[ERROR]${RESET} %s\n" "$1" >&2; exit 1; }

printf "${BLUE}=====================================${RESET}\n"
printf "${BLUE}       EnderPanel Installer          ${RESET}\n"
printf "${BLUE}              macOS                  ${RESET}\n"
printf "${BLUE}=====================================${RESET}\n"

# Check Homebrew
if ! command -v brew &> /dev/null; then
    echo "Homebrew not found. Installing via official script..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    if [ $? -ne 0 ]; then
        echo "Homebrew installation failed. Please install it manually:"
        echo '  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        exit 1
    fi
    eval "$(/opt/homebrew/bin/brew shellenv)" 2>/dev/null || true
    export PATH
fi

# Install Python
echo "Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "Installing Python via Homebrew..."
    brew install python@3.12
else
    echo "Python found: $(python3 --version)"
fi

# Install Node.js
echo "Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo "Installing Node.js via Homebrew..."
    brew install node@20
else
    echo "Node.js found: $(node --version)"
fi

# Java is supplied by the version-specific Docker images built below.

# Install Docker
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Installing via Homebrew..."
    brew install --cask docker
    echo "Docker Desktop installed. Please open Docker Desktop app and start it."
    open -a Docker
    echo "Waiting for Docker to start..."
    for i in $(seq 1 30); do
        if docker info &> /dev/null; then break; fi
        sleep 2
    done
else
    echo "Docker found."
fi

# Check Docker is running
if ! docker info &> /dev/null; then
    echo "Docker is not running. Please start Docker Desktop and try again."
    echo "Open Docker Desktop from Applications."
    exit 1
fi

# Configure Docker RAM allocation
echo ""
echo "Configuring Docker RAM allocation..."
DOCKER_SETTINGS="$HOME/Library/Application Support/Docker Desktop/settings.json"
if [ ! -f "$DOCKER_SETTINGS" ]; then
    DOCKER_SETTINGS="$HOME/Library/Group Containers/group.com.docker/settings.json"
fi

TOTAL_MEM_MB=$(( $(sysctl -n hw.memsize) / 1024 / 1024 ))
DEFAULT_ALLOC=$(( TOTAL_MEM_MB / 2 ))
DEFAULT_SWAP=$(( DEFAULT_ALLOC / 2 ))
echo "Your Mac has ${TOTAL_MEM_MB}MB of RAM."
read -p "How much RAM (MB) should Docker use? [default: ${DEFAULT_ALLOC}]: " DOCKER_RAM
DOCKER_RAM=${DOCKER_RAM:-$DEFAULT_ALLOC}
read -p "How much swap (MB) for containers? [default: ${DEFAULT_SWAP}]: " DOCKER_SWAP
DOCKER_SWAP=${DOCKER_SWAP:-$DEFAULT_SWAP}

if [ -f "$DOCKER_SETTINGS" ]; then
    python3 - <<PYEOF
import json
path = "$DOCKER_SETTINGS"
with open(path, 'r') as f:
    cfg = json.load(f)
cfg['memoryMiB'] = $DOCKER_RAM
cfg['swapMiB'] = $DOCKER_SWAP
with open(path, 'w') as f:
    json.dump(cfg, f, indent=2)
print(f"Docker RAM set to $DOCKER_RAM MB, swap to $DOCKER_SWAP MB in {path}")
PYEOF
    echo "Restart Docker Desktop for changes to take effect."
else
    echo "Docker Desktop settings file not found — open Docker Desktop > Settings > Resources and set RAM to ${DOCKER_RAM}MB and swap to ${DOCKER_SWAP}MB manually."
fi

# Check if running from local source (installer is in same dir as backend/)
LOCAL_SOURCE=""
if [ -d "./backend" ] && [ -f "./backend/requirements.txt" ]; then
    LOCAL_SOURCE="."
fi

INSTALL_DIR="$HOME/EnderPanel"
if [ -n "$LOCAL_SOURCE" ]; then
    echo ""
    echo "Local EnderPanel source detected. Installing from $LOCAL_SOURCE..."
    SOURCE_DIR="$(cd "$LOCAL_SOURCE" && pwd -P)"
    # Preserve existing data on upgrade
    if [ "$SOURCE_DIR" = "$INSTALL_DIR" ]; then
        ok "Already running from the installation directory; updating in place."
    elif [ -d "$INSTALL_DIR" ]; then
        echo "Existing installation found. Upgrading..."
        cp -r "$SOURCE_DIR/." "$INSTALL_DIR/"
        mkdir -p "$INSTALL_DIR/backend/servers" "$INSTALL_DIR/backend/avatars" 2>/dev/null || true
    else
        mkdir -p "$INSTALL_DIR"
        cp -a "$SOURCE_DIR/." "$INSTALL_DIR/"
    fi
else
    echo ""
    echo "No local source found. Please run this installer from the EnderPanel source directory."
    echo "Expected: A 'backend' folder with requirements.txt in the same directory as this script."
    exit 1
fi

cd "$INSTALL_DIR"

# Install dependencies
echo ""
echo "Installing backend dependencies..."
cd backend
python3 -m pip install --break-system-packages -r requirements.txt 2>/dev/null || \
sudo python3 -m pip install --break-system-packages -r requirements.txt

echo ""
echo "Installing frontend dependencies..."
cd "$INSTALL_DIR/frontend"
npm ci

echo ""
echo "Building frontend..."
npm run build

echo ""
echo "Building Docker images..."
cd "$INSTALL_DIR/backend"
docker build -t mc-panel-server:latest .
docker build -t mc-panel-server:java11 -f Dockerfile.java11 .
docker build -t mc-panel-server:java17 -f Dockerfile.java17 .
docker build -t mc-panel-server:java25 -f Dockerfile.java25 .
ok "Java 11, 17, 21, and 25 runtime images are ready."

echo ""
echo "=== Installation Complete ==="
echo ""
echo "To start EnderPanel:"
echo ""
echo "  cd $INSTALL_DIR/backend"
echo "  python3 main.py"
echo ""
echo "Then open http://localhost:8000"
RELEASE_VERSION="__RELEASE_VERSION__"

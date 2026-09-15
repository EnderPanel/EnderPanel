#!/bin/bash
set -euo pipefail

BLUE='\033[1;34m'; GREEN='\033[1;32m'; YELLOW='\033[1;33m'; RED='\033[1;31m'; RESET='\033[0m'
step() { printf "\n${BLUE}==>${RESET} %s\n" "$1"; }
ok() { printf "${GREEN}[OK]${RESET} %s\n" "$1"; }
warn() { printf "${YELLOW}[!]${RESET} %s\n" "$1"; }
fail() { printf "${RED}[ERROR]${RESET} %s\n" "$1" >&2; exit 1; }

printf "${BLUE}=====================================${RESET}\n"
printf "${BLUE}       EnderPanel Installer          ${RESET}\n"
printf "${BLUE}              Linux                  ${RESET}\n"
printf "${BLUE}=====================================${RESET}\n"

# Detect package manager
if command -v apt &> /dev/null; then
    PKG="apt"
elif command -v dnf &> /dev/null; then
    PKG="dnf"
elif command -v yum &> /dev/null; then
    PKG="yum"
elif command -v pacman &> /dev/null; then
    PKG="pacman"
else
    fail "Unsupported package manager. Install Python 3, Node.js 20, and Docker manually."
fi

echo "Detected package manager: $PKG"

# Install Python
echo ""
echo "Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "Installing Python 3..."
    if [ "$PKG" = "apt" ]; then
        sudo apt update
        sudo apt install -y python3 python3-venv
    elif [ "$PKG" = "dnf" ]; then
        sudo dnf install -y python3
    elif [ "$PKG" = "yum" ]; then
        sudo yum install -y python3
    elif [ "$PKG" = "pacman" ]; then
        sudo pacman -S --noconfirm python
    fi
else
    echo "Python 3 found: $(python3 --version)"
fi

# Ensure pip is available
if ! python3 -m pip --version &> /dev/null 2>&1; then
    echo "Installing pip..."
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3 - --break-system-packages 2>/dev/null || \
    curl -sS https://bootstrap.pypa.io/get-pip.py | sudo python3 2>/dev/null || true
fi
echo "Pip ready."

# Install Node.js
echo ""
echo "Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo "Installing Node.js..."
    if [ "$PKG" = "apt" ]; then
        curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
        sudo apt install -y nodejs
    elif [ "$PKG" = "dnf" ]; then
        curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
        sudo dnf install -y nodejs
    elif [ "$PKG" = "yum" ]; then
        curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
        sudo yum install -y nodejs
    elif [ "$PKG" = "pacman" ]; then
        sudo pacman -S --noconfirm nodejs npm
    fi
else
    echo "Node.js found: $(node --version)"
fi

# Java is supplied by the version-specific Docker images built below.

# Install Docker
echo ""
echo "Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    if [ "$PKG" = "apt" ]; then
        sudo apt install -y ca-certificates curl gnupg
        sudo install -m 0755 -d /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        sudo chmod a+r /etc/apt/keyrings/docker.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        sudo apt update
        sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    elif [ "$PKG" = "dnf" ]; then
        sudo dnf -y install dnf-plugins-core
        sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
        sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    elif [ "$PKG" = "yum" ]; then
        sudo yum install -y yum-utils
        sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
        sudo yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    elif [ "$PKG" = "pacman" ]; then
        sudo pacman -S --noconfirm docker docker-compose
    fi
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
    echo "Docker installed. You may need to log out and back in for group changes to take effect."
else
    echo "Docker found: $(docker --version)"
fi

# Check Docker is running
docker_working=false
if docker info &> /dev/null; then
    docker_working=true
elif sg docker -c "docker info" &> /dev/null; then
    docker_working=true
elif sudo docker info &> /dev/null; then
    docker_working=true
    echo "Docker works with sudo."
fi

if [ "$docker_working" != "true" ]; then
    echo "Starting Docker..."
    sudo systemctl start docker
    sleep 2
    if ! docker info &> /dev/null && ! sudo docker info &> /dev/null; then
        echo "Docker failed to start. Try: sudo systemctl start docker"
        exit 1
    fi
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
    if [ "$SOURCE_DIR" = "$INSTALL_DIR" ]; then
        ok "Already running from the installation directory; updating in place."
    elif [ -d "$INSTALL_DIR" ]; then
        echo "Existing installation found. Upgrading..."
        sudo cp -r "$SOURCE_DIR/." "$INSTALL_DIR/" 2>/dev/null || cp -r "$SOURCE_DIR/." "$INSTALL_DIR/"
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

echo "EnderPanel ready at $INSTALL_DIR"
cd "$INSTALL_DIR"

# Install Python dependencies
echo ""
echo "Installing backend dependencies..."
cd backend
python3 -m pip install --break-system-packages -r requirements.txt 2>/dev/null || \
sudo python3 -m pip install --break-system-packages -r requirements.txt

# Install frontend dependencies
echo ""
echo "Installing frontend dependencies..."
cd "$INSTALL_DIR/frontend"
npm ci

# Build frontend
echo ""
echo "Building frontend..."
npm run build

# Build Docker images
step "Building Java runtime images in Docker"
cd "$INSTALL_DIR/backend"

# Try to build as user first
if docker info &> /dev/null; then
    DOCKER_RUN=(docker)
else
    warn "Docker needs elevated access; using sudo."
    DOCKER_RUN=(sudo docker)
fi

"${DOCKER_RUN[@]}" build -t mc-panel-server:latest .
"${DOCKER_RUN[@]}" build -t mc-panel-server:java11 -f Dockerfile.java11 .
"${DOCKER_RUN[@]}" build -t mc-panel-server:java17 -f Dockerfile.java17 .
"${DOCKER_RUN[@]}" build -t mc-panel-server:java25 -f Dockerfile.java25 .
ok "Java 11, 17, 21, and 25 runtime images are ready."

echo ""
echo "=== Installation Complete ==="
echo ""
echo "To start EnderPanel:"
echo "  cd $INSTALL_DIR/backend"
echo "  python3 main.py"
echo ""
echo "Open http://localhost:8000 in your browser"
RELEASE_VERSION="__RELEASE_VERSION__"

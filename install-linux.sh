#!/bin/bash

echo "=== EnderPanel Installer (Linux) ==="
echo ""

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
    echo "Unsupported package manager. Install Python 3, Node.js, Java 8/17/21/25, and Docker manually."
    exit 1
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

# Install Java
echo ""
echo "Checking Java..."
if [ "$PKG" = "apt" ]; then
    # Fix broken Adoptium/Temurin repo if present (uses distro codename, not 'stable')
    if [ -f /etc/apt/sources.list.d/adoptium.list ] || grep -r "adoptium" /etc/apt/sources.list.d/ &>/dev/null; then
        CODENAME=$(. /etc/os-release && echo "$VERSION_CODENAME")
        if [ -n "$CODENAME" ]; then
            sudo find /etc/apt/sources.list.d/ -name "*.list" -exec sudo sed -i "s|adoptium.net.*stable|adoptium.net/artifactory/deb ${CODENAME} main|g" {} \; 2>/dev/null || true
        fi
    fi
    sudo apt-get update -o APT::Update::Error-Mode=ignore 2>/dev/null || sudo apt update || true
    for ver in 8 17 21 25; do
        if ! update-alternatives --list java 2>/dev/null | grep -q "java-${ver}"; then
            echo "Installing Java ${ver}..."
            sudo apt install -y openjdk-${ver}-jdk
        else
            echo "Java ${ver} found."
        fi
    done
elif [ "$PKG" = "dnf" ]; then
    for pair in "1.8:java-1.8.0-openjdk-devel" "17:java-17-openjdk-devel" "21:java-21-openjdk-devel" "25:java-latest-openjdk-devel"; do
        ver="${pair%%:*}"; pkg="${pair##*:}"
        key="jre_${ver/./_}"
        if ! alternatives --list 2>/dev/null | grep -q "$key"; then
            echo "Installing Java ${ver}..."
            sudo dnf install -y $pkg
        else
            echo "Java ${ver} found."
        fi
    done
elif [ "$PKG" = "yum" ]; then
    for pair in "1.8:java-1.8.0-openjdk-devel" "17:java-17-openjdk-devel" "21:java-21-openjdk-devel" "25:java-latest-openjdk-devel"; do
        ver="${pair%%:*}"; pkg="${pair##*:}"
        if ! alternatives --list 2>/dev/null | grep -q "jre_${ver/./_}"; then
            echo "Installing Java ${ver}..."
            sudo yum install -y $pkg
        else
            echo "Java ${ver} found."
        fi
    done
elif [ "$PKG" = "pacman" ]; then
    for ver in 8 17 21; do
        if ! pacman -Qs "jdk${ver}-openjdk" &> /dev/null; then
            echo "Installing Java ${ver}..."
            sudo pacman -S --noconfirm "jdk${ver}-openjdk"
        else
            echo "Java ${ver} found."
        fi
    done
    if ! pacman -Qs "jre-openjdk" &> /dev/null; then
        echo "Installing Java 25..."
        sudo pacman -S --noconfirm jre-openjdk jdk-openjdk
    else
        echo "Latest OpenJDK found."
    fi
fi

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
    if [ -d "$INSTALL_DIR" ]; then
        echo "Existing installation found. Upgrading..."
        sudo cp -r "$LOCAL_SOURCE/." "$INSTALL_DIR/" 2>/dev/null || cp -r "$LOCAL_SOURCE/." "$INSTALL_DIR/" 2>/dev/null || true
        mkdir -p "$INSTALL_DIR/backend/servers" "$INSTALL_DIR/backend/avatars" 2>/dev/null || true
    else
        mkdir -p "$INSTALL_DIR"
        cp -a "$LOCAL_SOURCE/." "$INSTALL_DIR/"
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
npm install --include=dev

# Build frontend
echo ""
echo "Building frontend..."
npm run build

# Build Docker image
echo ""
echo "Building Docker image..."

# Try to build as user first
if docker info &> /dev/null; then
    echo "Docker accessible as user, building..."
    docker build -t mc-panel-server:latest .
else
    echo "Docker not accessible as user. Attempting to activate docker group..."
    sg docker -c "docker build -t mc-panel-server:latest ."
fi

echo ""
echo "=== Installation Complete ==="
echo ""
echo "To start EnderPanel:"
echo "  cd $INSTALL_DIR/backend"
echo "  python3 main.py"
echo ""
echo "Open http://localhost:8000 in your browser"
RELEASE_VERSION="__RELEASE_VERSION__"
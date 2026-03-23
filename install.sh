#!/bin/bash

echo "=== MC Panel Installer ==="
echo ""


if ! command -v python3 &> /dev/null; then
    echo "Python 3 not found. Please install it first."
    exit 1
fi


if ! command -v node &> /dev/null; then
    echo "Node.js not found. Please install it first."
    echo "Visit: https://nodejs.org"
    exit 1
fi


echo "Checking Java installations..."

install_java_mac() {
    if ! /usr/libexec/java_home -v 1.8 &> /dev/null; then
        echo "Installing Java 8..."
        brew install --cask temurin@8
    else
        echo "Java 8 found."
    fi

    if ! /usr/libexec/java_home -v 17 &> /dev/null; then
        echo "Installing Java 17..."
        brew install --cask temurin@17
    else
        echo "Java 17 found."
    fi

    if ! /usr/libexec/java_home -v 21 &> /dev/null; then
        echo "Installing Java 21..."
        brew install --cask temurin@21
    else
        echo "Java 21 found."
    fi
}

install_java_apt() {
    sudo apt update

    if ! update-alternatives --list java 2>/dev/null | grep -q "java-8"; then
        echo "Installing Java 8..."
        sudo apt install -y openjdk-8-jdk
    else
        echo "Java 8 found."
    fi

    if ! update-alternatives --list java 2>/dev/null | grep -q "java-17"; then
        echo "Installing Java 17..."
        sudo apt install -y openjdk-17-jdk
    else
        echo "Java 17 found."
    fi

    if ! update-alternatives --list java 2>/dev/null | grep -q "java-21"; then
        echo "Installing Java 21..."
        sudo apt install -y openjdk-21-jdk
    else
        echo "Java 21 found."
    fi
}

install_java_dnf() {
    if ! alternatives --list 2>/dev/null | grep -q "jre_1.8"; then
        echo "Installing Java 8..."
        sudo dnf install -y java-1.8.0-openjdk-devel
    else
        echo "Java 8 found."
    fi

    if ! alternatives --list 2>/dev/null | grep -q "jre_17"; then
        echo "Installing Java 17..."
        sudo dnf install -y java-17-openjdk-devel
    else
        echo "Java 17 found."
    fi

    if ! alternatives --list 2>/dev/null | grep -q "jre_21"; then
        echo "Installing Java 21..."
        sudo dnf install -y java-21-openjdk-devel
    else
        echo "Java 21 found."
    fi
}

if [[ "$OSTYPE" == "darwin"* ]]; then
    if command -v brew &> /dev/null; then
        install_java_mac
    else
        echo "Homebrew not found. Install Java manually from: https://adoptium.net"
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if command -v apt &> /dev/null; then
        install_java_apt
    elif command -v dnf &> /dev/null; then
        install_java_dnf
    else
        echo "Install Java manually from: https://adoptium.net"
    fi
fi

if ! command -v docker &> /dev/null; then
    echo "Docker not found. Installing..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            echo "Installing Docker via Homebrew..."
            brew install --cask docker
            echo "Docker Desktop installed. Please open Docker Desktop app and start it."
        else
            echo "Homebrew not found."
            echo "Install Docker manually from: https://www.docker.com/products/docker-desktop/"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt &> /dev/null; then
            echo "Installing Docker via apt..."
            sudo apt update
            sudo apt install -y ca-certificates curl gnupg
            sudo install -m 0755 -d /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
            sudo chmod a+r /etc/apt/keyrings/docker.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            sudo apt update
            sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            sudo usermod -aG docker $USER
            echo "Docker installed. You may need to log out and back in for group changes to take effect."
        elif command -v dnf &> /dev/null; then
            echo "Installing Docker via dnf..."
            sudo dnf -y install dnf-plugins-core
            sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
            sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            sudo systemctl start docker
            sudo systemctl enable docker
            sudo usermod -aG docker $USER
            echo "Docker installed and started."
        else
            echo "Install Docker manually from: https://docs.docker.com/engine/install/"
            exit 1
        fi
    fi
else
    echo "Docker found."
fi

if ! docker info &> /dev/null; then
    echo "Docker daemon is not running. Please start Docker and try again."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Open Docker Desktop from Applications."
    else
        echo "Run: sudo systemctl start docker"
    fi
    exit 1
fi

echo ""
echo "Installing backend dependencies..."
cd backend
python3 -m pip install -r requirements.txt

echo ""
echo "Installing frontend dependencies..."
cd ../frontend
npm install

echo ""
echo "=== Installation Complete ==="
echo ""
echo "To start the panel:"
echo ""
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "Then open http://localhost:3000"

# EnderPanel Windows Installer
# Run with: irm https://enderpanel.space/install.ps1 | iex

Write-Host "=== EnderPanel Installer ===" -ForegroundColor Magenta
Write-Host ""

# Enable scripting if needed
try { Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force } catch {}

# Check admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Please run PowerShell as Administrator and try again." -ForegroundColor Red
    Write-Host "Right-click PowerShell -> Run as Administrator" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

$ErrorActionPreference = "Stop"
$InstallDir = "$env:LOCALAPPDATA\EnderPanel"

# Install Python
Write-Host "Checking Python..." -ForegroundColor Cyan
try { python --version *>$null } catch {
    Write-Host "Installing Python 3.12.9..." -ForegroundColor Yellow
    winget install Python.Python.3.12 --version 3.12.9 --accept-package-agreements --accept-source-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}

# Install Node.js
Write-Host "Checking Node.js..." -ForegroundColor Cyan
try { node --version *>$null } catch {
    Write-Host "Installing Node.js 20 LTS..." -ForegroundColor Yellow
    winget install OpenJS.NodeJS.LTS --version 20.19.0 --accept-package-agreements --accept-source-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}

# Install Java
Write-Host "Checking Java..." -ForegroundColor Cyan
try { java -version *>$null } catch {
    Write-Host "Installing Java 21 LTS..." -ForegroundColor Yellow
    winget install EclipseAdoptium.Temurin.21.JDK --version 21.0.6.7 --accept-package-agreements --accept-source-agreements
}

# Install Docker
Write-Host "Checking Docker..." -ForegroundColor Cyan
try { docker --version *>$null } catch {
    Write-Host "Please install Docker Desktop from https://docker.com" -ForegroundColor Red
    Start-Process "https://www.docker.com/products/docker-desktop/"
    Read-Host "Press Enter after installing Docker Desktop"
}
# Configure Docker RAM allocation (Windows via WSL2)
Write-Host ""
Write-Host "Configuring Docker RAM allocation..." -ForegroundColor Cyan

$TotalRAM = (Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum).Sum
$TotalRAM_GB = [math]::Round($TotalRAM / 1GB, 1)
$DefaultAlloc_GB = [math]::Max(2, [math]::Floor($TotalRAM_GB / 2))

Write-Host "Your system has ${TotalRAM_GB}GB of RAM." -ForegroundColor White
$InputRam = Read-Host "How much RAM (GB) should Docker/WSL2 use? [default: ${DefaultAlloc_GB}GB]"
if (-not $InputRam) { $InputRam = $DefaultAlloc_GB }

$DefaultSwap_GB = [math]::Max(2, [math]::Floor([int]$InputRam / 2))
$InputSwap = Read-Host "How much swap (GB) for containers? [default: ${DefaultSwap_GB}GB]"
if (-not $InputSwap) { $InputSwap = $DefaultSwap_GB }

$WslConfig = "$env:USERPROFILE\.wslconfig"
$WslContent = "[wsl2]`nmemory=${InputRam}GB`nswap=${InputSwap}GB`nlocalhostForwarding=true`n"
Set-Content -Path $WslConfig -Value $WslContent -Encoding UTF8

Write-Host "Docker WSL2 RAM: ${InputRam}GB, Swap: ${InputSwap}GB (saved to $WslConfig)." -ForegroundColor Green
Write-Host "Restart WSL2 and Docker Desktop for changes to take effect." -ForegroundColor Yellow
Write-Host "  Run: wsl --shutdown" -ForegroundColor Gray
Write-Host ""


Write-Host ""
Write-Host "Downloading EnderPanel..." -ForegroundColor Cyan

# Download and extract tarball
$TarPath = "$env:TEMP\enderpanel-latest.tar.gz"
$TmpDir = "$env:TEMP\EnderPanel-upgrade"
try {
    Invoke-WebRequest -Uri "https://enderpanel.space/releases/latest.tar.gz" -OutFile $TarPath
    if (Test-Path $TmpDir) { Remove-Item -Recurse -Force $TmpDir }
    New-Item -ItemType Directory -Force -Path $TmpDir | Out-Null
    tar -xzf $TarPath -C $TmpDir
    Remove-Item $TarPath -Force -ErrorAction SilentlyContinue
    # Flatten single subdirectory wrapper if present (e.g. enderpanel-2.0.0-r2/)
    if (-not (Test-Path "$TmpDir\backend")) {
        $SubDir = Get-ChildItem -Path $TmpDir -Directory | Select-Object -First 1
        if ($SubDir) { Get-ChildItem -Path $SubDir.FullName | Move-Item -Destination $TmpDir -Force; Remove-Item $SubDir.FullName -Force }
    }

    # Preserve existing data on upgrade
    if (Test-Path $InstallDir) {
        Write-Host "Existing installation found. Upgrading..." -ForegroundColor Yellow
        if (Test-Path "$InstallDir\backend\mcpanel.db") { Copy-Item "$InstallDir\backend\mcpanel.db" "$TmpDir\backend\" -Force }
        if (Test-Path "$InstallDir\backend\servers") { Copy-Item "$InstallDir\backend\servers" "$TmpDir\backend\" -Recurse -Force }
        if (Test-Path "$InstallDir\backend\avatars") { Copy-Item "$InstallDir\backend\avatars" "$TmpDir\backend\" -Recurse -Force }
        if (Test-Path "$InstallDir\backend\data") { Copy-Item "$InstallDir\backend\data" "$TmpDir\backend\" -Recurse -Force }
        Remove-Item -Recurse -Force $InstallDir
    }

    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
    Copy-Item "$TmpDir\*" $InstallDir -Recurse -Force
    Remove-Item -Recurse -Force $TmpDir -ErrorAction SilentlyContinue
} catch {
    Write-Host "Download failed: $_" -ForegroundColor Red
    Remove-Item $TarPath -Force -ErrorAction SilentlyContinue
    exit 1
}

if (-not (Test-Path "$InstallDir\backend")) {
    Write-Host "Backend folder not found. Download may have failed. Please try again." -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Cyan
Set-Location "$InstallDir\backend"
pip install -r requirements.txt

Write-Host "Installing Node dependencies..." -ForegroundColor Cyan
Set-Location "$InstallDir\frontend"
npm install

# Build frontend
Write-Host "Building frontend..." -ForegroundColor Cyan
npx vite build

# Build Docker image
Write-Host "Building Docker image..." -ForegroundColor Cyan
Set-Location "$InstallDir\backend"
docker build -t mc-panel-server:latest .

# Create desktop shortcut
Write-Host "Creating shortcuts..." -ForegroundColor Cyan
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\EnderPanel.lnk")
$Shortcut.TargetPath = "powershell.exe"
$StartCmd = "Set-Location '$InstallDir\backend'; python main.py 2>&1 | Tee-Object -FilePath '$InstallDir\enderpanel.log' -Append"
$Shortcut.Arguments = "-NoExit -Command `"$StartCmd`""
$Shortcut.IconLocation = "$InstallDir\electron\icon.png"
$Shortcut.Save()

Write-Host ""
Write-Host "=== Installation Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "To start EnderPanel:" -ForegroundColor White
Write-Host "  cd '$InstallDir\backend'" -ForegroundColor Gray
Write-Host "  python main.py" -ForegroundColor Gray
Write-Host ""
Write-Host "Then open http://localhost:3000" -ForegroundColor White
Write-Host ""

$start = Read-Host "Start EnderPanel now? (y/n)"
if ($start -eq "y") {
    Set-Location "$InstallDir\backend"
    python main.py
}

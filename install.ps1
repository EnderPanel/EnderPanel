# EnderPanel Windows Installer
# Run with: irm https://enderpanel.space/install.ps1 | iex

Write-Host "=== EnderPanel Installer ===" -ForegroundColor Magenta
Write-Host ""

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
    Write-Host "Installing Python..." -ForegroundColor Yellow
    winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}

# Install Node.js
Write-Host "Checking Node.js..." -ForegroundColor Cyan
try { node --version *>$null } catch {
    Write-Host "Installing Node.js..." -ForegroundColor Yellow
    winget install OpenJS.NodeJS.LTS --accept-package-agreements --accept-source-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}

# Install Java
Write-Host "Checking Java..." -ForegroundColor Cyan
try { java -version *>$null } catch {
    Write-Host "Installing Java 21..." -ForegroundColor Yellow
    winget install EclipseAdoptium.Temurin.21.JDK --accept-package-agreements --accept-source-agreements
}

# Install Docker
Write-Host "Checking Docker..." -ForegroundColor Cyan
try { docker --version *>$null } catch {
    Write-Host "Please install Docker Desktop from https://docker.com" -ForegroundColor Red
    Start-Process "https://www.docker.com/products/docker-desktop/"
    Read-Host "Press Enter after installing Docker Desktop"
}

# Download EnderPanel
Write-Host ""
Write-Host "Downloading EnderPanel..." -ForegroundColor Cyan
if (Test-Path $InstallDir) { Remove-Item -Recurse -Force $InstallDir }

$Release = Invoke-RestMethod "https://api.github.com/repos/EnderPanel/EnderPanel/releases/latest"
$ZipUrl = ($Release.assets | Where-Object { $_.name -like "*.zip" }).browser_download_url

if (-not $ZipUrl) {
    Write-Host "Downloading from GitHub..." -ForegroundColor Yellow
    git clone https://github.com/EnderPanel/EnderPanel.git $InstallDir
} else {
    $ZipPath = "$env:TEMP\enderpanel.zip"
    Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipPath
    Expand-Archive -Path $ZipPath -DestinationPath $InstallDir -Force
    Remove-Item $ZipPath
}

# Install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Cyan
Set-Location "$InstallDir\backend"
pip install -r requirements.txt

Write-Host "Installing Node dependencies..." -ForegroundColor Cyan
Set-Location "$InstallDir\frontend"
npm install
npm run build

# Build Docker image
Write-Host "Building Docker image..." -ForegroundColor Cyan
Set-Location "$InstallDir\backend"
docker build -t mc-panel-server:latest .

# Create desktop shortcut
Write-Host "Creating shortcuts..." -ForegroundColor Cyan
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\EnderPanel.lnk")
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-Command `"cd '$InstallDir\backend'; python main.py`""
$Shortcut.IconLocation = "$InstallDir\electron\icon.png"
$Shortcut.Save()

Write-Host ""
Write-Host "=== Installation Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "To start EnderPanel:" -ForegroundColor White
Write-Host "  cd '$InstallDir\backend'" -ForegroundColor Gray
Write-Host "  python main.py" -ForegroundColor Gray
Write-Host ""
Write-Host "Then open http://localhost:8000" -ForegroundColor White
Write-Host ""

$start = Read-Host "Start EnderPanel now? (y/n)"
if ($start -eq "y") {
    Set-Location "$InstallDir\backend"
    python main.py
}

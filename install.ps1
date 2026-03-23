$ErrorActionPreference = "Stop"

# ── Config ────────────────────────────────────────────────────────────────────
$VERSION     = "1.0.0"
$BASE_URL    = "https://enderpanel.space"
$INSTALL_DIR = "C:\EnderPanel"

# ── Check admin ───────────────────────────────────────────────────────────────
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "  x  Please run PowerShell as Administrator and try again." -ForegroundColor Red
    exit 1
}

# ── Helpers ───────────────────────────────────────────────────────────────────
function Ok($msg)   { Write-Host "  " -NoNewline; Write-Host "v" -ForegroundColor Green -NoNewline; Write-Host "  $msg" }
function Warn($msg) { Write-Host "  " -NoNewline; Write-Host "!" -ForegroundColor Yellow -NoNewline; Write-Host "  $msg" }
function Err($msg)  { Write-Host "  " -NoNewline; Write-Host "x" -ForegroundColor Red -NoNewline; Write-Host "  $msg"; exit 1 }
function Info($msg) { Write-Host "  " -NoNewline; Write-Host ">" -ForegroundColor Cyan -NoNewline; Write-Host "  $msg" }

# ── Banner ────────────────────────────────────────────────────────────────────
Clear-Host
Write-Host ""
Write-Host "  EnderPanel v$VERSION" -ForegroundColor Magenta
Write-Host "  Your server, another dimension" -ForegroundColor Cyan
Write-Host "  enderpanel.space" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  ----------------------------------------"
Write-Host ""
Write-Host "  Starting installation..." -ForegroundColor White
Write-Host ""

# ── Check winget ──────────────────────────────────────────────────────────────
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Err "winget not found. Install it from: https://aka.ms/getwinget"
}
Ok "winget found"

# ── Python ────────────────────────────────────────────────────────────────────
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Info "Python not found. Installing..."
    winget install -e --id Python.Python.3.12 --silent
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Ok "Python installed"
} else {
    Ok "Python found ($((python --version 2>&1)))"
}

# ── Node.js ───────────────────────────────────────────────────────────────────
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Info "Node.js not found. Installing..."
    winget install -e --id OpenJS.NodeJS.LTS --silent
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Ok "Node.js installed"
} else {
    Ok "Node.js found ($((node --version)))"
}

# ── Java ──────────────────────────────────────────────────────────────────────
Info "Checking Java versions..."
$javaVersions = @(
    @{ Id = "EclipseAdoptium.Temurin.8.JRE";  Ver = "8"  },
    @{ Id = "EclipseAdoptium.Temurin.17.JRE"; Ver = "17" },
    @{ Id = "EclipseAdoptium.Temurin.21.JRE"; Ver = "21" }
)
foreach ($j in $javaVersions) {
    $path = "$env:ProgramFiles\Eclipse Adoptium\jre-$($j.Ver)*"
    if (Test-Path $path) {
        Ok "Java $($j.Ver) found"
    } else {
        Info "Installing Java $($j.Ver)..."
        winget install -e --id $j.Id --silent
        Ok "Java $($j.Ver) installed"
    }
}

# ── Docker ────────────────────────────────────────────────────────────────────
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Info "Docker not found. Installing..."

    $os = (Get-WmiObject Win32_OperatingSystem).Caption
    if ($os -like "*Server*") {
        Info "Windows Server detected — installing Docker Engine..."
        Install-Module -Name DockerMsftProvider -Repository PSGallery -Force -ErrorAction SilentlyContinue
        Install-Package -Name docker -ProviderName DockerMsftProvider -Force
        Start-Service docker
        Ok "Docker Engine installed"
    } else {
        Info "Downloading Docker Desktop installer..."
        $dockerInstaller = "$env:TEMP\DockerDesktopInstaller.exe"
        Invoke-WebRequest -Uri "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe" -OutFile $dockerInstaller -UseBasicParsing
        Start-Process -FilePath $dockerInstaller -Args "install --quiet" -Wait
        Remove-Item $dockerInstaller
        Warn "Docker Desktop installed. Please:"
        Warn "  1. Restart your computer"
        Warn "  2. Open Docker Desktop and let it finish starting"
        Warn "  3. Re-run this script"
        Write-Host ""
        Read-Host "  Press Enter to exit"
        exit 0
    }
} else {
    Ok "Docker found"
}

try {
    docker info 2>&1 | Out-Null
    Ok "Docker daemon running"
} catch {
    Err "Docker daemon is not running. Please open Docker Desktop and try again."
}

# ── Download release ──────────────────────────────────────────────────────────
Write-Host ""
Info "Downloading EnderPanel v${VERSION}..."

if (Test-Path $INSTALL_DIR) {
    Warn "Existing installation found — updating..."
    Remove-Item "$INSTALL_DIR\backend" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item "$INSTALL_DIR\frontend" -Recurse -Force -ErrorAction SilentlyContinue
}
New-Item -ItemType Directory -Force -Path $INSTALL_DIR | Out-Null

$tarPath = "$env:TEMP\enderpanel.tar.gz"
Invoke-WebRequest -Uri "$BASE_URL/releases/enderpanel-${VERSION}.tar.gz" -OutFile $tarPath -UseBasicParsing
tar -xzf $tarPath -C $INSTALL_DIR --strip-components=1
Remove-Item $tarPath
Ok "Downloaded and extracted to $INSTALL_DIR"

# ── Install dependencies ──────────────────────────────────────────────────────
Write-Host ""
Info "Installing backend dependencies..."
Set-Location "$INSTALL_DIR\backend"
python -m pip install -q -r requirements.txt
Ok "Backend dependencies installed"

Info "Installing frontend dependencies..."
Set-Location "$INSTALL_DIR\frontend"
npm install --silent
Ok "Frontend dependencies installed"

Info "Building frontend..."
npm run build --silent
Ok "Frontend built"

# ── Generate secret key ───────────────────────────────────────────────────────
$secret = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 64 | ForEach-Object { [char]$_ })
$configPath = "$INSTALL_DIR\backend\config.py"
(Get-Content $configPath) -replace "your-secret-key-change-this-in-production", $secret | Set-Content $configPath
Ok "Secret key generated"

# ── Windows Service ───────────────────────────────────────────────────────────
Info "Installing EnderPanel as a Windows service..."
$pythonPath = (Get-Command python).Source
$serviceName = "EnderPanel"

if (Get-Service -Name $serviceName -ErrorAction SilentlyContinue) {
    Stop-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
    sc.exe delete $serviceName | Out-Null
}

$binPath = "`"$pythonPath`" `"$INSTALL_DIR\backend\main.py`""
sc.exe create $serviceName binPath= $binPath start= auto DisplayName= "EnderPanel" | Out-Null
sc.exe description $serviceName "EnderPanel - Minecraft Server Management Panel" | Out-Null
Start-Service -Name $serviceName
Ok "EnderPanel service installed and started"

# ── CLI shortcut ──────────────────────────────────────────────────────────────
$cliScript = @'
param([string]$cmd)
switch ($cmd) {
    "start"   { Start-Service EnderPanel; Write-Host "EnderPanel started" -ForegroundColor Green }
    "stop"    { Stop-Service EnderPanel; Write-Host "EnderPanel stopped" -ForegroundColor Yellow }
    "restart" { Restart-Service EnderPanel; Write-Host "EnderPanel restarted" -ForegroundColor Green }
    "status"  { Get-Service EnderPanel | Format-List Name, Status, StartType }
    "logs"    { Get-EventLog -LogName Application -Source EnderPanel -Newest 50 }
    "update"  { irm https://enderpanel.space/install.ps1 | iex }
    default   { Write-Host "Usage: enderpanel {start|stop|restart|status|logs|update}" }
}
'@
Set-Content -Path "C:\Windows\System32\enderpanel.ps1" -Value $cliScript
Ok "CLI tool installed"

# ── Firewall ──────────────────────────────────────────────────────────────────
New-NetFirewallRule -DisplayName "EnderPanel" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -ErrorAction SilentlyContinue | Out-Null
Ok "Firewall rule added for port 8000"

# ── Done ──────────────────────────────────────────────────────────────────────
$localIP = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "*Ethernet*","*Wi-Fi*" -ErrorAction SilentlyContinue | Select-Object -First 1).IPAddress

Write-Host ""
Write-Host "  ----------------------------------------"
Write-Host ""
Write-Host "  EnderPanel installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "  Panel URL:  " -NoNewline; Write-Host "http://${localIP}:8000" -ForegroundColor Cyan
Write-Host "  Manage:     " -NoNewline; Write-Host "enderpanel start | stop | logs | update" -ForegroundColor Cyan
Write-Host "  Docs:       " -NoNewline; Write-Host "$BASE_URL/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "  ----------------------------------------"
Write-Host ""

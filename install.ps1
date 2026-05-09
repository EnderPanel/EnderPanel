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
$InstallDir = Join-Path $env:USERPROFILE "EnderPanel"
$ReleaseVersion = "__RELEASE_VERSION__"
$ReleaseUrl = "https://enderpanel.space/releases/latest.tar.gz?v=$ReleaseVersion"

function Refresh-Path {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}

function Resolve-CommandPath {
    param(
        [Parameter(Mandatory = $true)][string[]]$Candidates
    )

    foreach ($Candidate in $Candidates) {
        $Command = Get-Command $Candidate -ErrorAction SilentlyContinue
        if ($Command -and $Command.Source) {
            return $Command.Source
        }
    }

    return $null
}

function Install-DownloadedExe {
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [Parameter(Mandatory = $true)][string]$FileName,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    $DownloadPath = Join-Path $env:TEMP $FileName
    Invoke-WebRequest -Uri $Url -OutFile $DownloadPath
    try {
        $Process = Start-Process -FilePath $DownloadPath -ArgumentList $Arguments -Wait -PassThru
        if ($Process.ExitCode -ne 0) {
            throw "Installer exited with code $($Process.ExitCode)"
        }
    } finally {
        Remove-Item $DownloadPath -Force -ErrorAction SilentlyContinue
    }
}

function Install-DownloadedMsi {
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [Parameter(Mandatory = $true)][string]$FileName,
        [string[]]$ExtraArguments = @()
    )

    $DownloadPath = Join-Path $env:TEMP $FileName
    Invoke-WebRequest -Uri $Url -OutFile $DownloadPath
    try {
        $Arguments = @("/i", "`"$DownloadPath`"", "/qn", "/norestart") + $ExtraArguments
        $Process = Start-Process -FilePath "msiexec.exe" -ArgumentList $Arguments -Wait -PassThru
        if ($Process.ExitCode -ne 0) {
            throw "Installer exited with code $($Process.ExitCode)"
        }
    } finally {
        Remove-Item $DownloadPath -Force -ErrorAction SilentlyContinue
    }
}

function Test-JavaInstall {
    param(
        [Parameter(Mandatory = $true)][int]$MajorVersion
    )

    $patterns = @(
        (Join-Path $env:ProgramFiles "Eclipse Adoptium\jdk-$MajorVersion*"),
        (Join-Path $env:ProgramFiles "AdoptOpenJDK\jdk-$MajorVersion*")
    )

    if ($MajorVersion -eq 8) {
        $patterns += (Join-Path $env:ProgramFiles "Java\jdk1.8*")
    }

    foreach ($pattern in $patterns) {
        if (Get-ChildItem -Path $pattern -Directory -ErrorAction SilentlyContinue | Select-Object -First 1) {
            return $true
        }
    }

    return $false
}

# Install Python
Write-Host "Checking Python..." -ForegroundColor Cyan
try { python --version *>$null } catch {
    Write-Host "Installing Python 3.12.9..." -ForegroundColor Yellow
    Install-DownloadedExe `
        -Url "https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe" `
        -FileName "python-3.12.9-amd64.exe" `
        -Arguments @("/quiet", "InstallAllUsers=1", "PrependPath=1", "Include_test=0")
    Refresh-Path
}

# Install Node.js
Write-Host "Checking Node.js..." -ForegroundColor Cyan
try { node --version *>$null } catch {
    Write-Host "Installing Node.js 20 LTS..." -ForegroundColor Yellow
    Install-DownloadedMsi `
        -Url "https://nodejs.org/dist/v20.19.0/node-v20.19.0-x64.msi" `
        -FileName "node-v20.19.0-x64.msi"
    Refresh-Path
}

# Install Java
Write-Host "Checking Java installations..." -ForegroundColor Cyan
foreach ($JavaVersion in 8, 17, 21) {
    if (-not (Test-JavaInstall -MajorVersion $JavaVersion)) {
        Write-Host "Installing Java $JavaVersion..." -ForegroundColor Yellow
        Install-DownloadedMsi `
            -Url "https://api.adoptium.net/v3/installer/latest/$JavaVersion/ga/windows/x64/jdk/hotspot/normal/eclipse?project=jdk" `
            -FileName "OpenJDK${JavaVersion}U-jdk_x64_windows_hotspot.msi"
    } else {
        Write-Host "Java $JavaVersion found." -ForegroundColor Green
    }
}
Refresh-Path

# Install Docker Desktop
Write-Host "Checking Docker Desktop..." -ForegroundColor Cyan
try { docker --version *>$null } catch {
    Write-Host "Please install Docker Desktop from https://docker.com" -ForegroundColor Red
    Start-Process "https://www.docker.com/products/docker-desktop/"
    Read-Host "Press Enter after installing Docker Desktop"
}
# Configure Docker Desktop RAM allocation (Windows via WSL2)
Write-Host ""
Write-Host "Configuring Docker Desktop RAM allocation..." -ForegroundColor Cyan

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
    Invoke-WebRequest -Uri $ReleaseUrl -OutFile $TarPath
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
$NpmCmd = Resolve-CommandPath @("npm.cmd", "npm")
if (-not $NpmCmd) {
    throw "npm was not found after installation."
}
& $NpmCmd install
if ($LASTEXITCODE -ne 0) {
    throw "npm install failed with exit code $LASTEXITCODE"
}

# Build frontend
Write-Host "Building frontend..." -ForegroundColor Cyan
$NpxCmd = Resolve-CommandPath @("npx.cmd", "npx")
if (-not $NpxCmd) {
    throw "npx was not found after Node.js installation."
}
& $NpxCmd vite build
if ($LASTEXITCODE -ne 0) {
    throw "npx vite build failed with exit code $LASTEXITCODE"
}
if (-not (Test-Path "$InstallDir\frontend\dist\index.html")) {
    throw "Frontend build did not create frontend\\dist\\index.html"
}

# Build Docker image
Write-Host "Building Docker image..." -ForegroundColor Cyan
Set-Location "$InstallDir\backend"
docker build -t mc-panel-server:latest .

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
    $env:ENDERPANEL_DISABLE_FRONTEND_DEV = "1"
    python main.py
}

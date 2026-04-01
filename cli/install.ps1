# Axon CLI Installer for Windows
# Usage: irm https://get.useaxon.dev | iex
#
# Installs the `axon` CLI (PowerShell edition) to %LOCALAPPDATA%\Axon\bin.
# Only prerequisite: Docker Desktop for Windows.

$ErrorActionPreference = "Stop"

$Repo = "brandonkorous/axon"
$CliUrl = "https://raw.githubusercontent.com/$Repo/main/cli/axon.ps1"

# ── Colors ──────────────────────────────────────────────────────────────────
function Write-Info  { param($Msg) Write-Host "  >" $Msg -ForegroundColor Cyan }
function Write-Ok    { param($Msg) Write-Host "  +" $Msg -ForegroundColor Green }
function Write-Warn  { param($Msg) Write-Host "  !" $Msg -ForegroundColor Yellow }
function Write-Fail  { param($Msg) Write-Host "  x" $Msg -ForegroundColor Red; exit 1 }

# ── Banner ──────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "    ___   _  ______  _   __"  -ForegroundColor Cyan
Write-Host "   /   | | |/ / __ \/ | / /"  -ForegroundColor Cyan
Write-Host "  / /| | |   / / / /  |/ / "  -ForegroundColor Cyan
Write-Host " / ___ |/   / /_/ / /|  /  "  -ForegroundColor Cyan
Write-Host "/_/  |_/_/|_\____/_/ |_/   "  -ForegroundColor Cyan
Write-Host ""
Write-Host "  Self-hosted AI Command Center" -ForegroundColor White
Write-Host "  https://useaxon.dev" -ForegroundColor Cyan
Write-Host ""

# ── Check prerequisites ────────────────────────────────────────────────────
Write-Info "Checking prerequisites..."

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Warn "Docker not found. Axon needs Docker Desktop to run."
    Write-Host ""
    Write-Host "    1)" -ForegroundColor White -NoNewline; Write-Host " Download Docker Desktop " -NoNewline; Write-Host "(opens browser)" -ForegroundColor DarkGray
    Write-Host "    2)" -ForegroundColor White -NoNewline; Write-Host " Install via winget"
    Write-Host "    s)" -ForegroundColor White -NoNewline; Write-Host " Skip - I'll install Docker later"
    Write-Host ""
    Write-Host "  ? Choose [1/2/s]: " -ForegroundColor Cyan -NoNewline
    $choice = Read-Host
    switch ($choice) {
        "1" {
            Start-Process "https://docs.docker.com/desktop/install/windows-install/"
            Write-Info "Install Docker Desktop, then re-run this installer."
            exit 0
        }
        "2" {
            winget install -e --id Docker.DockerDesktop
            Write-Info "Restart your terminal after Docker Desktop finishes installing, then re-run this installer."
            exit 0
        }
        default {
            Write-Info "Install Docker Desktop before using Axon: https://docs.docker.com/desktop/install/windows-install/"
            Write-Info "Continuing with CLI install..."
        }
    }
} else {
    Write-Ok "Docker found"
}

# ── Install directory ──────────────────────────────────────────────────────
$InstallDir = "$env:LOCALAPPDATA\Axon\bin"
if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}
Write-Info "Install directory: $InstallDir"

# ── Download CLI ───────────────────────────────────────────────────────────
Write-Info "Downloading Axon CLI..."

$AxonScript = Join-Path $InstallDir "axon.ps1"
try {
    Invoke-RestMethod -Uri $CliUrl -OutFile $AxonScript
} catch {
    Write-Fail "Failed to download Axon CLI: $_"
}
Write-Ok "Downloaded axon.ps1"

# ── Create axon.cmd wrapper ───────────────────────────────────────────────
# Lets users just type `axon` instead of `powershell axon.ps1`
$WrapperPath = Join-Path $InstallDir "axon.cmd"
$WrapperContent = @"
@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0axon.ps1" %*
"@
Set-Content -Path $WrapperPath -Value $WrapperContent -Encoding ASCII
Write-Ok "Created axon.cmd wrapper"

# ── Update PATH ────────────────────────────────────────────────────────────
$NeedsRestart = $false
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notlike "*$InstallDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$InstallDir;$UserPath", "User")
    Write-Ok "Added $InstallDir to user PATH"
    $env:Path = "$InstallDir;$env:Path"
    $NeedsRestart = $true
} else {
    Write-Ok "Install directory already on PATH"
}

# ── Verify ─────────────────────────────────────────────────────────────────
Write-Ok "axon is ready!"

Write-Host ""
Write-Host "  Get started:" -ForegroundColor White
Write-Host "    axon init my-workspace" -ForegroundColor Cyan
Write-Host "    cd my-workspace" -ForegroundColor Cyan
Write-Host "    axon start" -ForegroundColor Cyan
Write-Host ""

if ($NeedsRestart) {
    Write-Host "  Note: Restart your terminal for PATH changes to take effect." -ForegroundColor Yellow
    Write-Host ""
}

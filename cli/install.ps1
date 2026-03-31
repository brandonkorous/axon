# Axon CLI Installer for Windows
# Usage: irm https://get.useaxon.dev | iex
#
# Installs the `axon` CLI to %LOCALAPPDATA%\Axon\bin and adds it to user PATH.
# Requires: Docker Desktop for Windows, Git Bash (bundled with Git for Windows).

$ErrorActionPreference = "Stop"

$Repo = "brandonkorous/axon"
$CliUrl = "https://raw.githubusercontent.com/$Repo/main/cli/axon"
$VersionUrl = "https://raw.githubusercontent.com/$Repo/main/cli/VERSION"

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

# Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Fail "Docker not found. Install Docker Desktop for Windows: https://docs.docker.com/desktop/install/windows-install/"
}
Write-Ok "Docker found"

# Git (ships with Git Bash which we need to run the CLI)
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Fail "Git not found. Install Git for Windows: https://git-scm.com/download/win"
}
Write-Ok "Git found"

# Find Git Bash
$GitDir = Split-Path (Split-Path (Get-Command git).Source)
$BashCandidates = @(
    "$GitDir\bin\bash.exe",
    "$GitDir\usr\bin\bash.exe",
    "$env:ProgramFiles\Git\bin\bash.exe",
    "${env:ProgramFiles(x86)}\Git\bin\bash.exe"
)
$BashExe = $null
foreach ($candidate in $BashCandidates) {
    if (Test-Path $candidate) {
        $BashExe = $candidate
        break
    }
}
if (-not $BashExe) {
    Write-Fail "Git Bash not found. Reinstall Git for Windows with 'Git Bash' option enabled."
}
Write-Ok "Git Bash found at $BashExe"

# ── Install directory ──────────────────────────────────────────────────────
$InstallDir = "$env:LOCALAPPDATA\Axon\bin"
if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}
Write-Info "Install directory: $InstallDir"

# ── Download CLI ───────────────────────────────────────────────────────────
Write-Info "Downloading Axon CLI..."

$AxonScript = Join-Path $InstallDir "axon"
try {
    Invoke-RestMethod -Uri $CliUrl -OutFile $AxonScript
} catch {
    Write-Fail "Failed to download Axon CLI: $_"
}
Write-Ok "Downloaded axon CLI script"

# ── Create axon.cmd wrapper ───────────────────────────────────────────────
# Windows can't execute bash scripts directly, so we create a .cmd wrapper
# that invokes the script via Git Bash.
$WrapperPath = Join-Path $InstallDir "axon.cmd"
$WrapperContent = @"
@echo off
setlocal
set "AXON_SCRIPT=%~dp0axon"
"$BashExe" "%AXON_SCRIPT%" %*
"@
Set-Content -Path $WrapperPath -Value $WrapperContent -Encoding ASCII
Write-Ok "Created axon.cmd wrapper"

# ── Update PATH ────────────────────────────────────────────────────────────
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
try {
    $null = & "$WrapperPath" version 2>&1
    Write-Ok "axon is ready!"
} catch {
    if ($NeedsRestart) {
        Write-Warn "PATH was updated. Restart your terminal for 'axon' to be available."
    } else {
        Write-Warn "Installation completed but verification failed. Try running 'axon version' manually."
    }
}

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

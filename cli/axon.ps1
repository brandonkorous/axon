# Axon CLI — Self-hosted AI Command Center
# https://useaxon.dev
# PowerShell edition — feature-equivalent to the bash CLI

$ErrorActionPreference = "Stop"

# Version: read from VERSION file if available, otherwise hardcoded
$VersionFile = Join-Path (Split-Path $PSScriptRoot) "VERSION"
if (Test-Path $VersionFile) {
    $AxonVersion = (Get-Content $VersionFile -Raw).Trim()
} else {
    $AxonVersion = "0.1.0"
}
$AxonRepo = "brandonkorous/axon"
$AxonImagePrefix = "ghcr.io/$AxonRepo"
$AxonMarker = ".axon"

# ── Output Helpers ─────────────────────────────────────────────────────────
function Write-Info  { param($Msg) Write-Host "  >" $Msg -ForegroundColor Cyan }
function Write-Ok    { param($Msg) Write-Host "  +" $Msg -ForegroundColor Green }
function Write-Warn  { param($Msg) Write-Host "  !" $Msg -ForegroundColor Yellow }
function Write-Fail  { param($Msg) Write-Host "  x" $Msg -ForegroundColor Red; exit 1 }
function Write-Step  { param($Msg) Write-Host ""; Write-Host "  $Msg" -ForegroundColor White }
function Write-Ask   { param($Msg) Write-Host "  ? $Msg " -ForegroundColor Cyan -NoNewline }

# ── Banner ─────────────────────────────────────────────────────────────────
function Show-Banner {
    Write-Host ""
    Write-Host "    ___   _  ______  _   __"  -ForegroundColor Cyan
    Write-Host "   /   | | |/ / __ \/ | / /"  -ForegroundColor Cyan
    Write-Host "  / /| | |   / / / /  |/ / "  -ForegroundColor Cyan
    Write-Host " / ___ |/   / /_/ / /|  /  "  -ForegroundColor Cyan
    Write-Host "/_/  |_/_/|_\____/_/ |_/   "  -ForegroundColor Cyan
    Write-Host "  v$AxonVersion" -ForegroundColor DarkGray
    Write-Host ""
}

# ══════════════════════════════════════════════════════════════════════════════
#  Hardware Detection
# ══════════════════════════════════════════════════════════════════════════════

function Get-RamGB {
    try {
        $os = Get-CimInstance Win32_OperatingSystem
        return [math]::Round($os.TotalVisibleMemorySize / 1MB)
    } catch {
        return 0
    }
}

function Get-GpuInfo {
    $gpu = @{ Name = ""; VramGB = 0 }
    try {
        # Try nvidia-smi first
        $nvSmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
        if ($nvSmi) {
            $gpu.Name = (& nvidia-smi --query-gpu=name --format=csv,noheader 2>$null | Select-Object -First 1).Trim()
            $vramMB = (& nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>$null | Select-Object -First 1).Trim()
            if ($vramMB) { $gpu.VramGB = [math]::Round([int]$vramMB / 1024) }
            return $gpu
        }

        # Fallback to WMI
        $adapter = Get-CimInstance Win32_VideoController | Select-Object -First 1
        if ($adapter) {
            $gpu.Name = $adapter.Name
            if ($adapter.AdapterRAM -and $adapter.AdapterRAM -gt 0) {
                $gpu.VramGB = [math]::Round($adapter.AdapterRAM / 1GB)
            }
        }
    } catch {}
    return $gpu
}

function Get-DiskGB {
    try {
        $drive = Get-PSDrive -Name (Get-Location).Drive.Name
        return [math]::Round($drive.Free / 1GB)
    } catch {
        return 0
    }
}

function Get-RecommendedTier {
    param($RamGB, $VramGB)
    if ($VramGB -ge 12 -or $RamGB -ge 48) { return 4 }
    if ($VramGB -ge 8  -or $RamGB -ge 32) { return 3 }
    if ($VramGB -ge 6  -or $RamGB -ge 16) { return 2 }
    return 1
}

function Show-HardwareSummary {
    $ramGB = Get-RamGB
    $gpu = Get-GpuInfo
    $diskGB = Get-DiskGB

    Write-Step "System hardware"
    Write-Info "RAM: $ramGB GB"

    if ($gpu.Name) {
        Write-Info "GPU: $($gpu.Name)"
        Write-Info "VRAM: $($gpu.VramGB) GB"
    } else {
        Write-Info "GPU: None detected"
    }

    Write-Info "Disk available: ~$diskGB GB"
}

# ══════════════════════════════════════════════════════════════════════════════
#  Docker Detection & Installation
# ══════════════════════════════════════════════════════════════════════════════

function Test-Docker {
    return [bool](Get-Command docker -ErrorAction SilentlyContinue)
}

function Test-DockerRunning {
    try { docker info 2>$null | Out-Null; return $true } catch { return $false }
}

function Get-ComposeCmd {
    # Compose v2 (plugin)
    try {
        docker compose version 2>$null | Out-Null
        return "docker compose"
    } catch {}
    # Compose v1 (standalone)
    if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
        return "docker-compose"
    }
    return $null
}

function Install-Docker {
    Write-Host ""
    Write-Host "  Docker not found." -ForegroundColor White -NoNewline
    Write-Host " Axon needs Docker to run."
    Write-Host "  How would you like to install it?"
    Write-Host ""
    Write-Host "    1)" -ForegroundColor White -NoNewline; Write-Host " Docker Desktop " -NoNewline; Write-Host "(recommended)" -ForegroundColor DarkGray
    Write-Host "    2)" -ForegroundColor White -NoNewline; Write-Host " winget " -NoNewline; Write-Host "(winget install Docker.DockerDesktop)" -ForegroundColor DarkGray
    Write-Host "    s)" -ForegroundColor White -NoNewline; Write-Host " Skip - I'll install it myself"
    Write-Host ""
    Write-Ask "Choose [1/2/s]:"
    $choice = Read-Host

    switch ($choice) {
        "1" {
            Write-Info "Downloading Docker Desktop installer..."
            $url = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
            $tmp = Join-Path $env:TEMP "DockerDesktopInstaller.exe"
            Invoke-WebRequest -Uri $url -OutFile $tmp -UseBasicParsing
            Write-Info "Launching installer... Follow the prompts to complete installation."
            Start-Process -FilePath $tmp -ArgumentList "install", "--quiet" -Wait
            Write-Info "After installation completes, restart your terminal and re-run this command."
            exit 0
        }
        "2" {
            Write-Info "Installing via winget..."
            winget install -e --id Docker.DockerDesktop
            if ($LASTEXITCODE -ne 0) { Write-Fail "winget install failed. Try option 1 or install manually." }
            Write-Info "Restart your terminal and re-run this command."
            exit 0
        }
        { $_ -in "s", "S" } {
            Write-Host ""
            Write-Info "Install Docker Desktop: https://docs.docker.com/desktop/install/windows-install/"
            Write-Info "Then re-run this command."
            exit 0
        }
        default { Write-Fail "Invalid choice" }
    }
}

function Start-DockerDesktop {
    Write-Info "Docker is installed but not running. Starting..."
    $dockerDesktop = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if (Test-Path $dockerDesktop) {
        Start-Process -FilePath $dockerDesktop
    } else {
        Write-Info "Start Docker Desktop from your Start menu."
    }
    Wait-ForDocker
}

function Wait-ForDocker {
    Write-Info "Waiting for Docker to be ready..."
    $attempts = 0
    $maxAttempts = 60
    while (-not (Test-DockerRunning)) {
        $attempts++
        if ($attempts -ge $maxAttempts) {
            Write-Fail "Docker did not start within 60 seconds. Start it manually and retry."
        }
        Write-Host "`r  ... Waiting for Docker... (${attempts}s)" -NoNewline
        Start-Sleep -Seconds 1
    }
    Write-Host ""
    Write-Ok "Docker is running"
}

function Assert-Docker {
    Write-Step "Checking dependencies..."

    if (-not (Test-Docker)) {
        Install-Docker
        if (-not (Test-Docker)) {
            Write-Fail "Docker installation did not complete. Install manually and retry."
        }
    } else {
        Write-Ok "Docker installed"
    }

    if (-not (Test-DockerRunning)) {
        Start-DockerDesktop
    } else {
        Write-Ok "Docker running"
    }

    $script:ComposeCmd = Get-ComposeCmd
    if (-not $script:ComposeCmd) {
        Write-Fail "Docker Compose not found. Install it: https://docs.docker.com/compose/install/"
    } else {
        Write-Ok "Docker Compose available"
    }
}

# ══════════════════════════════════════════════════════════════════════════════
#  Workspace Templates
# ══════════════════════════════════════════════════════════════════════════════

function Write-ComposeFile {
    param($Dir)
    $content = @'
# Axon — Docker Compose (managed by axon CLI)
# Docs: https://useaxon.dev

services:
  backend:
    image: ghcr.io/brandonkorous/axon-backend:latest
    ports:
      - "${AXON_PORT_BACKEND:-8000}:8000"
    volumes:
      - ${AXON_ORGS_DIR:-./orgs}:/orgs
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
      - DEFAULT_MODEL=${DEFAULT_MODEL:-anthropic/claude-sonnet-4-20250514}
      - OLLAMA_BASE_URL=http://ollama:11434
      - AXON_ORGS_DIR=/orgs
      - AXON_LOG_LEVEL=${AXON_LOG_LEVEL:-INFO}
      - DB_ENCRYPTION_KEY=${DB_ENCRYPTION_KEY:-}
    depends_on:
      ollama:
        condition: service_started
        required: false
    restart: unless-stopped

  frontend:
    image: ghcr.io/brandonkorous/axon-frontend:latest
    ports:
      - "${AXON_PORT_FRONTEND:-3000}:3000"
    depends_on:
      - backend
    restart: unless-stopped

  searxng:
    image: searxng/searxng:latest
    ports:
      - "${AXON_PORT_SEARCH:-8080}:8080"
    environment:
      - SEARXNG_BASE_URL=http://searxng:8080
    volumes:
      - searxng_data:/etc/searxng
    profiles:
      - web-search

  ollama:
    image: ollama/ollama:latest
    ports:
      - "${AXON_PORT_OLLAMA:-11434}:11434"
    volumes:
      - ollama_models:/root/.ollama
    profiles:
      - local-llm
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  ollama-init:
    image: ollama/ollama:latest
    profiles:
      - local-llm
    depends_on:
      - ollama
    restart: "no"
    entrypoint: ["/bin/sh", "-c"]
    command:
      - |
        echo "Waiting for Ollama..."
        until curl -s http://ollama:11434/api/tags > /dev/null 2>&1; do sleep 1; done
        echo "Pulling models..."
        curl -s http://ollama:11434/api/pull -d "{\"name\":\"${OLLAMA_NAVIGATOR_MODEL:-qwen2.5:7b}\"}"
        curl -s http://ollama:11434/api/pull -d "{\"name\":\"${OLLAMA_MEMORY_MODEL:-llama3:8b}\"}"
        curl -s http://ollama:11434/api/pull -d "{\"name\":\"${OLLAMA_MODEL:-qwen2.5:14b}\"}"
        echo "Models ready."
    environment:
      - OLLAMA_MODEL=${OLLAMA_MODEL:-qwen2.5:14b}
      - OLLAMA_NAVIGATOR_MODEL=${OLLAMA_NAVIGATOR_MODEL:-qwen2.5:7b}
      - OLLAMA_MEMORY_MODEL=${OLLAMA_MEMORY_MODEL:-llama3:8b}

volumes:
  ollama_models:
  searxng_data:
'@
    Set-Content -Path (Join-Path $Dir "docker-compose.yml") -Value $content -Encoding UTF8
}

function Write-EnvFile {
    param($Dir, $ApiKey = "")
    # Generate encryption key
    $encKey = ""
    try {
        $bytes = New-Object byte[] 32
        [System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
        $encKey = [Convert]::ToBase64String($bytes)
    } catch {}

    $content = @"
# Axon Configuration
# Docs: https://useaxon.dev

# -- API Keys (at least one required) ------------------------------------
ANTHROPIC_API_KEY=$ApiKey
OPENAI_API_KEY=

# -- Model ----------------------------------------------------------------
# LiteLLM format: provider/model-name
DEFAULT_MODEL=anthropic/claude-sonnet-4-20250514

# -- Data -----------------------------------------------------------------
AXON_ORGS_DIR=./orgs

# -- Ports ----------------------------------------------------------------
AXON_PORT_FRONTEND=3000
AXON_PORT_BACKEND=8000

# -- Local LLMs (optional) -----------------------------------------------
# Enable with: axon start --local
OLLAMA_MODEL=qwen2.5:14b

# -- Database -------------------------------------------------------------
# Leave empty for SQLite (default). Postgres: postgresql+asyncpg://user:pass@host/axon
DATABASE_URL=

# -- Security -------------------------------------------------------------
# Auto-generated encryption key for OAuth token storage
DB_ENCRYPTION_KEY=$encKey
"@
    Set-Content -Path (Join-Path $Dir ".env") -Value $content -Encoding UTF8
}

function Write-GitignoreFile {
    param($Dir)
    Set-Content -Path (Join-Path $Dir ".gitignore") -Value ".env`norgs/`n*.db" -Encoding UTF8
}

# ══════════════════════════════════════════════════════════════════════════════
#  Local Model Selection
# ══════════════════════════════════════════════════════════════════════════════

function Select-LocalModel {
    $ramGB = Get-RamGB
    $gpu = Get-GpuInfo
    $tier = Get-RecommendedTier -RamGB $ramGB -VramGB $gpu.VramGB

    Write-Host ""
    Write-Step "Local LLM Setup"
    Write-Host ""
    Write-Info "RAM: $ramGB GB"
    if ($gpu.Name) {
        Write-Info "GPU: $($gpu.Name) ($($gpu.VramGB) GB VRAM)"
    } else {
        Write-Info "GPU: None detected (models will run on CPU - slower but functional)"
    }
    Write-Host ""

    switch ($tier) {
        1 {
            Write-Host "  Limited hardware detected." -ForegroundColor Yellow
            Write-Host "  With $ramGB GB RAM, only small models will run reliably."
            Write-Host ""
            Write-Host "    1)" -ForegroundColor White -NoNewline; Write-Host " llama3:8b " -NoNewline; Write-Host "(~5 GB - recommended for your system)" -ForegroundColor DarkGray
            Write-Host "    2)" -ForegroundColor White -NoNewline; Write-Host " qwen2.5:7b " -NoNewline; Write-Host "(~4.5 GB - may be tight on memory)" -ForegroundColor DarkGray
            Write-Host "    3)" -ForegroundColor White -NoNewline; Write-Host " phi4-mini:3.8b " -NoNewline; Write-Host "(~2.5 GB - fastest, least capable)" -ForegroundColor DarkGray
            Write-Host "    c)" -ForegroundColor White -NoNewline; Write-Host " Custom model name"
            $defaults = @{ "1" = "llama3:8b"; "2" = "qwen2.5:7b"; "3" = "phi4-mini:3.8b" }
            $fallback = "llama3:8b"
        }
        2 {
            Write-Host "  Moderate hardware detected. Good for medium models." -ForegroundColor Cyan
            Write-Host ""
            Write-Host "    1)" -ForegroundColor White -NoNewline; Write-Host " qwen2.5:7b " -NoNewline; Write-Host "(~4.5 GB - recommended for your system)" -ForegroundColor DarkGray
            Write-Host "    2)" -ForegroundColor White -NoNewline; Write-Host " llama3:8b " -NoNewline; Write-Host "(~5 GB - solid general purpose)" -ForegroundColor DarkGray
            Write-Host "    3)" -ForegroundColor White -NoNewline; Write-Host " mistral:7b " -NoNewline; Write-Host "(~4.5 GB - fast reasoning)" -ForegroundColor DarkGray
            Write-Host "    4)" -ForegroundColor White -NoNewline; Write-Host " codellama:7b " -NoNewline; Write-Host "(~4 GB - code-focused)" -ForegroundColor DarkGray
            Write-Host "    c)" -ForegroundColor White -NoNewline; Write-Host " Custom model name"
            $defaults = @{ "1" = "qwen2.5:7b"; "2" = "llama3:8b"; "3" = "mistral:7b"; "4" = "codellama:7b" }
            $fallback = "qwen2.5:7b"
        }
        3 {
            Write-Host "  Strong hardware detected. You can run larger models." -ForegroundColor Green
            Write-Host ""
            Write-Host "    1)" -ForegroundColor White -NoNewline; Write-Host " qwen2.5:14b " -NoNewline; Write-Host "(~9 GB - recommended for your system)" -ForegroundColor DarkGray
            Write-Host "    2)" -ForegroundColor White -NoNewline; Write-Host " mistral-small:22b " -NoNewline; Write-Host "(~13 GB - excellent reasoning)" -ForegroundColor DarkGray
            Write-Host "    3)" -ForegroundColor White -NoNewline; Write-Host " llama3:8b " -NoNewline; Write-Host "(~5 GB - lighter, faster)" -ForegroundColor DarkGray
            Write-Host "    4)" -ForegroundColor White -NoNewline; Write-Host " codellama:13b " -NoNewline; Write-Host "(~8 GB - code-focused)" -ForegroundColor DarkGray
            Write-Host "    c)" -ForegroundColor White -NoNewline; Write-Host " Custom model name"
            $defaults = @{ "1" = "qwen2.5:14b"; "2" = "mistral-small:22b"; "3" = "llama3:8b"; "4" = "codellama:13b" }
            $fallback = "qwen2.5:14b"
        }
        4 {
            Write-Host "  Excellent hardware detected. You can run large models." -ForegroundColor Green
            Write-Host ""
            Write-Host "    1)" -ForegroundColor White -NoNewline; Write-Host " qwen2.5:32b " -NoNewline; Write-Host "(~20 GB - recommended for your system)" -ForegroundColor DarkGray
            Write-Host "    2)" -ForegroundColor White -NoNewline; Write-Host " llama3.1:70b " -NoNewline; Write-Host "(~40 GB - maximum capability)" -ForegroundColor DarkGray
            Write-Host "    3)" -ForegroundColor White -NoNewline; Write-Host " qwen2.5:14b " -NoNewline; Write-Host "(~9 GB - fast + capable)" -ForegroundColor DarkGray
            Write-Host "    4)" -ForegroundColor White -NoNewline; Write-Host " mistral-small:22b " -NoNewline; Write-Host "(~13 GB - strong reasoning)" -ForegroundColor DarkGray
            Write-Host "    c)" -ForegroundColor White -NoNewline; Write-Host " Custom model name"
            $defaults = @{ "1" = "qwen2.5:32b"; "2" = "llama3.1:70b"; "3" = "qwen2.5:14b"; "4" = "mistral-small:22b" }
            $fallback = "qwen2.5:32b"
        }
    }

    Write-Host ""
    Write-Ask "Choose model:"
    $choice = Read-Host

    if ($choice -in "c", "C") {
        Write-Ask "Model name (e.g. mistral:7b):"
        $model = Read-Host
    } elseif ($defaults.ContainsKey($choice)) {
        $model = $defaults[$choice]
    } else {
        $model = $fallback
        Write-Warn "Defaulting to $fallback"
    }

    Write-Ok "Selected model: $model"
    Write-Info "qwen2.5:7b (navigator) and llama3:8b (memory) will also be pulled"
    return $model
}

# ══════════════════════════════════════════════════════════════════════════════
#  Commands
# ══════════════════════════════════════════════════════════════════════════════

function Invoke-Compose {
    param([string[]]$Arguments)
    $parts = $script:ComposeCmd -split " "
    $cmd = $parts[0]
    $allArgs = @()
    if ($parts.Count -gt 1) { $allArgs += $parts[1..($parts.Count - 1)] }
    $allArgs += $Arguments
    & $cmd @allArgs
}

# ── axon init <name> ───────────────────────────────────────────────────────
function Invoke-Init {
    param($Name)
    if (-not $Name) { Write-Fail "Usage: axon init <workspace-name>" }

    Show-Banner
    Assert-Docker

    Write-Step "Creating workspace: $Name/"

    if ((Test-Path $Name) -and (Test-Path (Join-Path $Name $AxonMarker))) {
        Write-Fail "Axon workspace '$Name' already exists"
    }

    New-Item -ItemType Directory -Path $Name -Force | Out-Null

    # Ask for API key
    Write-Host ""
    Write-Host "  Axon needs at least one LLM provider." -ForegroundColor White
    Write-Host "  You can always change this later in " -NoNewline; Write-Host ".env" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "    1)" -ForegroundColor White -NoNewline; Write-Host " Anthropic Claude " -NoNewline; Write-Host "(recommended)" -ForegroundColor DarkGray
    Write-Host "    2)" -ForegroundColor White -NoNewline; Write-Host " OpenAI"
    Write-Host "    3)" -ForegroundColor White -NoNewline; Write-Host " Local only " -NoNewline; Write-Host "(Ollama - no API key needed)" -ForegroundColor DarkGray
    Write-Host "    s)" -ForegroundColor White -NoNewline; Write-Host " Skip - I'll configure later"
    Write-Host ""
    Write-Ask "Choose [1/2/3/s]:"
    $providerChoice = Read-Host

    $apiKey = ""
    $useLocal = $false
    $localModel = ""

    switch ($providerChoice) {
        "1" {
            Write-Ask "Anthropic API key:"
            $apiKey = Read-Host
            if (-not $apiKey) { Write-Warn "No key entered. You can add it later in .env" }
        }
        "2" {
            Write-Ask "OpenAI API key:"
            $apiKey = Read-Host
        }
        "3" {
            $useLocal = $true
            $localModel = Select-LocalModel
        }
        { $_ -in "s", "S" } {
            Write-Info "Skipping API key setup. Edit .env before starting."
        }
        default {
            Write-Warn "Invalid choice - skipping. Edit .env before starting."
        }
    }

    # Write workspace files
    Write-ComposeFile -Dir $Name
    Write-EnvFile -Dir $Name -ApiKey $apiKey
    Write-GitignoreFile -Dir $Name
    New-Item -ItemType Directory -Path (Join-Path $Name "orgs") -Force | Out-Null

    # Write marker file
    Set-Content -Path (Join-Path $Name $AxonMarker) -Value $AxonVersion -Encoding UTF8

    # If OpenAI was chosen, swap the key placement
    if ($providerChoice -eq "2" -and $apiKey) {
        $envPath = Join-Path $Name ".env"
        $envContent = Get-Content $envPath -Raw
        $envContent = $envContent -replace "ANTHROPIC_API_KEY=.*", "ANTHROPIC_API_KEY="
        $envContent = $envContent -replace "OPENAI_API_KEY=.*", "OPENAI_API_KEY=$apiKey"
        $envContent = $envContent -replace "DEFAULT_MODEL=.*", "DEFAULT_MODEL=openai/gpt-4o"
        Set-Content -Path $envPath -Value $envContent -Encoding UTF8
    }

    # If local-only, set the model
    if ($useLocal) {
        $chosenModel = if ($localModel) { $localModel } else { "llama3:8b" }
        $envPath = Join-Path $Name ".env"
        $envContent = Get-Content $envPath -Raw
        $envContent = $envContent -replace "ANTHROPIC_API_KEY=.*", "ANTHROPIC_API_KEY="
        $envContent = $envContent -replace "DEFAULT_MODEL=.*", "DEFAULT_MODEL=ollama/$chosenModel"
        $envContent = $envContent -replace "OLLAMA_MODEL=.*", "OLLAMA_MODEL=$chosenModel"
        Set-Content -Path $envPath -Value $envContent -Encoding UTF8
    }

    Write-Ok "Workspace created"

    Write-Host ""
    Write-Host "  Ready!" -ForegroundColor Green
    Write-Host ""
    Write-Host "    cd $Name" -ForegroundColor Cyan
    if ($useLocal) {
        Write-Host "    axon start --local" -ForegroundColor Cyan
    } else {
        Write-Host "    axon start" -ForegroundColor Cyan
    }
    Write-Host ""
    Write-Host "  Open http://localhost:3000 after startup" -ForegroundColor DarkGray
    Write-Host ""
}

# ── axon start ─────────────────────────────────────────────────────────────
function Invoke-Start {
    param([string[]]$Options)
    Assert-Workspace

    Show-Banner
    Assert-Docker

    Write-Step "Starting Axon..."

    $profiles = @()
    foreach ($opt in $Options) {
        switch ($opt) {
            { $_ -in "--local", "--ollama" } {
                $profiles += "--profile"
                $profiles += "local-llm"
                Write-Info "Local LLM mode enabled (Ollama)"
            }
            { $_ -in "--search", "--web-search" } {
                $profiles += "--profile"
                $profiles += "web-search"
                Write-Info "Web search enabled (SearXNG)"
            }
        }
    }

    Invoke-Compose (@("up", "-d") + $profiles)

    # Read ports from .env or use defaults
    $frontendPort = $env:AXON_PORT_FRONTEND
    if (-not $frontendPort) { $frontendPort = "3000" }
    $backendPort = $env:AXON_PORT_BACKEND
    if (-not $backendPort) { $backendPort = "8000" }

    Write-Host ""
    Write-Ok "Axon is running"
    Write-Host ""
    Write-Host "  Dashboard:  " -ForegroundColor White -NoNewline; Write-Host "http://localhost:$frontendPort" -ForegroundColor Cyan
    Write-Host "  API:        " -ForegroundColor White -NoNewline; Write-Host "http://localhost:$backendPort" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Logs:  axon logs" -ForegroundColor DarkGray
    Write-Host "  Stop:  axon stop" -ForegroundColor DarkGray
    Write-Host ""
}

# ── axon stop ──────────────────────────────────────────────────────────────
function Invoke-Stop {
    Assert-Workspace
    Write-Step "Stopping Axon..."
    Invoke-Compose @("down")
    Write-Ok "Axon stopped"
}

# ── axon restart ───────────────────────────────────────────────────────────
function Invoke-Restart {
    param([string[]]$Options)
    Invoke-Stop
    Invoke-Start -Options $Options
}

# ── axon logs ──────────────────────────────────────────────────────────────
function Invoke-Logs {
    param($Service)
    Assert-Workspace
    if ($Service) {
        Invoke-Compose @("logs", "-f", $Service)
    } else {
        Invoke-Compose @("logs", "-f")
    }
}

# ── axon status ────────────────────────────────────────────────────────────
function Invoke-Status {
    Assert-Workspace
    Invoke-Compose @("ps")
}

# ── axon update ────────────────────────────────────────────────────────────
function Invoke-Update {
    param([string[]]$Options)
    Assert-Workspace

    Write-Step "Updating Axon..."
    Invoke-Compose @("pull")
    Write-Ok "Images updated"

    Write-Ask "Restart now? [Y/n]:"
    $restart = Read-Host
    if ($restart -in "n", "N", "no") {
        Write-Info "Run 'axon restart' when ready."
    } else {
        Invoke-Restart -Options $Options
    }
}

# ── axon doctor ────────────────────────────────────────────────────────────
function Invoke-Doctor {
    Show-Banner

    Write-Step "Checking system..."

    # Docker
    if (Test-Docker) {
        $dockerVersion = (docker --version 2>$null) -join " "
        Write-Ok "Docker installed ($dockerVersion)"
    } else {
        Write-Fail "Docker not installed"
    }

    if (Test-DockerRunning) {
        Write-Ok "Docker daemon running"
    } else {
        Write-Warn "Docker daemon not running"
    }

    $compose = Get-ComposeCmd
    if ($compose) {
        Write-Ok "Docker Compose available"
    } else {
        Write-Warn "Docker Compose not found"
    }

    # Workspace
    if (Test-Path $AxonMarker) {
        $wsVersion = (Get-Content $AxonMarker -Raw).Trim()
        Write-Ok "Inside Axon workspace (v$wsVersion)"
    } else {
        Write-Warn "Not inside an Axon workspace"
    }

    # .env
    if (Test-Path ".env") {
        Write-Ok ".env file present"
        $envContent = Get-Content ".env" -Raw
        if ($envContent -match "ANTHROPIC_API_KEY=." -or $envContent -match "OPENAI_API_KEY=.") {
            Write-Ok "API key configured"
        } else {
            Write-Warn "No API key found in .env (needed unless using local LLMs only)"
        }
    } else {
        Write-Warn "No .env file"
    }

    # Hardware
    Write-Step "Checking hardware..."

    $ramGB = Get-RamGB
    if ($ramGB -ge 16) { Write-Ok "RAM: $ramGB GB" }
    elseif ($ramGB -ge 8) { Write-Warn "RAM: $ramGB GB (16 GB+ recommended for local LLMs)" }
    else { Write-Warn "RAM: $ramGB GB (minimum 8 GB required, 16 GB+ recommended)" }

    $gpu = Get-GpuInfo
    if ($gpu.Name) {
        Write-Ok "GPU: $($gpu.Name)"
        if ($gpu.VramGB -ge 8) { Write-Ok "VRAM: $($gpu.VramGB) GB" }
        elseif ($gpu.VramGB -gt 0) { Write-Warn "VRAM: $($gpu.VramGB) GB (8 GB+ recommended for local LLMs)" }
    } else {
        Write-Info "GPU: None detected (local LLMs will use CPU)"
    }

    $diskGB = Get-DiskGB
    if ($diskGB -ge 20) { Write-Ok "Disk: ~$diskGB GB available" }
    else { Write-Warn "Disk: ~$diskGB GB available (20 GB+ recommended for model storage)" }

    # Model recommendations
    $tier = Get-RecommendedTier -RamGB $ramGB -VramGB $gpu.VramGB
    Write-Host ""
    switch ($tier) {
        1 { Write-Info "Local LLM tier: Basic - small models only (llama3:8b, phi4-mini)" }
        2 { Write-Info "Local LLM tier: Moderate - medium models (qwen2.5:7b, mistral:7b)" }
        3 { Write-Info "Local LLM tier: Strong - large models (qwen2.5:14b, mistral-small:22b)" }
        4 { Write-Info "Local LLM tier: Excellent - very large models (qwen2.5:32b, llama3.1:70b)" }
    }

    # Port availability
    Write-Step "Checking ports..."
    foreach ($port in @(3000, 8000)) {
        try {
            $tcp = New-Object System.Net.Sockets.TcpClient
            $tcp.Connect("localhost", $port)
            $tcp.Close()
            Write-Warn "Port $port in use"
        } catch {
            Write-Ok "Port $port available"
        }
    }
    Write-Host ""
}

# ── axon self-update ───────────────────────────────────────────────────────
function Invoke-SelfUpdate {
    Write-Info "Updating Axon CLI..."
    $cliUrl = "https://raw.githubusercontent.com/$AxonRepo/main/cli/axon.ps1"
    $selfPath = $MyInvocation.ScriptName
    if (-not $selfPath) { $selfPath = $PSCommandPath }
    if (-not $selfPath) { Write-Fail "Cannot determine script location" }

    try {
        $tmpPath = "$selfPath.tmp"
        Invoke-RestMethod -Uri $cliUrl -OutFile $tmpPath
        Move-Item -Path $tmpPath -Destination $selfPath -Force
        Write-Ok "Updated to latest version"
    } catch {
        Write-Fail "Update failed: $_"
    }
}

# ── axon version ───────────────────────────────────────────────────────────
function Invoke-Version {
    Write-Host "  CLI:    $AxonVersion"

    if ((Test-Path $AxonMarker) -and (Test-Docker) -and (Test-DockerRunning)) {
        $backendPort = $env:AXON_PORT_BACKEND
        if (-not $backendPort) { $backendPort = "8000" }
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:$backendPort/api/version" -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($response.version) {
                Write-Host "  Server: $($response.version)"
                if ($AxonVersion -ne $response.version) {
                    Write-Warn "Version mismatch - run 'axon update' to sync"
                }
            } else {
                Write-Host "  Server: " -NoNewline; Write-Host "not running" -ForegroundColor DarkGray
            }
        } catch {
            Write-Host "  Server: " -NoNewline; Write-Host "not running" -ForegroundColor DarkGray
        }
    }
}

# ── Helpers ────────────────────────────────────────────────────────────────
function Assert-Workspace {
    # Load .env if present
    if (Test-Path ".env") {
        Get-Content ".env" | ForEach-Object {
            if ($_ -match "^\s*([^#][^=]+)=(.*)$") {
                [Environment]::SetEnvironmentVariable($Matches[1].Trim(), $Matches[2].Trim(), "Process")
            }
        }
    }

    if (-not (Test-Path $AxonMarker)) {
        Write-Fail "Not an Axon workspace. Run 'axon init <name>' first or cd into your workspace."
    }

    $script:ComposeCmd = Get-ComposeCmd
    if (-not $script:ComposeCmd) {
        Write-Fail "Docker Compose not found"
    }
}

# ── Usage ──────────────────────────────────────────────────────────────────
function Show-Usage {
    Show-Banner
    Write-Host "  Usage: axon <command> [options]"
    Write-Host ""
    Write-Host "  Commands:"
    Write-Host "    init" -ForegroundColor Cyan -NoNewline; Write-Host " <name>      Create a new Axon workspace"
    Write-Host "    start" -ForegroundColor Cyan -NoNewline; Write-Host "            Start Axon services"
    Write-Host "    stop" -ForegroundColor Cyan -NoNewline; Write-Host "             Stop Axon services"
    Write-Host "    restart" -ForegroundColor Cyan -NoNewline; Write-Host "          Restart Axon services"
    Write-Host "    logs" -ForegroundColor Cyan -NoNewline; Write-Host " [service]   Tail logs (optionally for one service)"
    Write-Host "    status" -ForegroundColor Cyan -NoNewline; Write-Host "           Show running services"
    Write-Host "    update" -ForegroundColor Cyan -NoNewline; Write-Host "           Pull latest Axon images"
    Write-Host "    doctor" -ForegroundColor Cyan -NoNewline; Write-Host "           Check system dependencies"
    Write-Host "    self-update" -ForegroundColor Cyan -NoNewline; Write-Host "      Update the Axon CLI itself"
    Write-Host "    version" -ForegroundColor Cyan -NoNewline; Write-Host "          Show version"
    Write-Host ""
    Write-Host "  Start options:"
    Write-Host "    --local          Enable local LLMs via Ollama" -ForegroundColor DarkGray
    Write-Host "    --search         Enable web search via SearXNG" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  Examples:"
    Write-Host "    axon init my-workspace" -ForegroundColor DarkGray
    Write-Host "    cd my-workspace; axon start" -ForegroundColor DarkGray
    Write-Host "    axon start --local --search" -ForegroundColor DarkGray
    Write-Host ""
}

# ── Main ───────────────────────────────────────────────────────────────────
$cmd = if ($args.Count -gt 0) { $args[0] } else { "" }
$rest = if ($args.Count -gt 1) { $args[1..($args.Count - 1)] } else { @() }

switch ($cmd) {
    "init"        { Invoke-Init -Name ($rest | Select-Object -First 1) }
    "start"       { Invoke-Start -Options $rest }
    "stop"        { Invoke-Stop }
    "restart"     { Invoke-Restart -Options $rest }
    "logs"        { Invoke-Logs -Service ($rest | Select-Object -First 1) }
    "status"      { Invoke-Status }
    "update"      { Invoke-Update -Options $rest }
    "doctor"      { Invoke-Doctor }
    "self-update" { Invoke-SelfUpdate }
    { $_ -in "version", "-v", "--version" } { Invoke-Version }
    { $_ -in "help", "-h", "--help", "" }   { Show-Usage }
    default       { Write-Fail "Unknown command: $cmd (run 'axon help' for usage)" }
}

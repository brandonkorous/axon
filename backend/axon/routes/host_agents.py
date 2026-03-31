"""Host agent CRUD routes — register, list, health-check host agent services."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import httpx
import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import axon.registry as registry
from axon.config import settings
from axon.org import HostAgentConfig

logger = logging.getLogger(__name__)

org_router = APIRouter()

MANAGER_URL = f"http://host.docker.internal:{os.environ.get('HOST_AGENT_MANAGER_PORT', '9099')}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_org_or_404(org_id: str):
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Org not found: {org_id}")
    return org


def _persist_host_agents(org_id: str, host_agents: list[HostAgentConfig]) -> None:
    """Write host_agents section back to org.yaml."""
    yaml_path = Path(settings.axon_orgs_dir) / org_id / "org.yaml"
    if not yaml_path.exists():
        return
    try:
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        data["host_agents"] = [
            ha.model_dump(mode="json") for ha in host_agents
        ]

        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    except Exception:
        logger.warning("Failed to persist host_agents for org %s", org_id)


async def _check_host_agent_health(config: HostAgentConfig) -> dict:
    """Ping a host agent to check if it's running."""
    url = f"http://{config.host}:{config.port}/health"
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                return {"status": "running", **resp.json()}
    except Exception:
        pass
    return {"status": "stopped"}


def _find_agent_config(org, agent_id: str) -> HostAgentConfig | None:
    """Find a host agent config by ID within an org."""
    for ha in org.config.host_agents:
        if ha.id == agent_id:
            return ha
    return None


async def _manager_request(method: str, endpoint: str, payload: dict = None) -> dict:
    """Send a request to the host agent manager."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            if method == "POST":
                resp = await client.post(f"{MANAGER_URL}{endpoint}", json=payload)
            else:
                resp = await client.get(f"{MANAGER_URL}{endpoint}")
            return resp.json()
    except Exception as e:
        raise HTTPException(503, f"Host agent manager not reachable: {e}")


def _write_manager_scripts(orgs_dir: str = "/orgs") -> None:
    """Write host manager startup scripts to the orgs directory."""
    orgs_path = Path(orgs_dir)
    if not orgs_path.exists():
        return

    # Windows: PowerShell script that runs manager and minimizes to system tray
    ps1_path = orgs_path / "host-manager.ps1"
    ps1_content = '''# Axon Host Agent Manager — minimizes to system tray
$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$hostAgentDir = Join-Path $PSScriptRoot "..\\axon\\host-agent"
$managerJs = Join-Path $hostAgentDir "manager.js"

if (-not (Test-Path $managerJs)) {
    [System.Windows.Forms.MessageBox]::Show(
        "manager.js not found at:`n$managerJs`n`nMake sure the host-agent directory exists next to the orgs directory.",
        "Axon Host Manager", "OK", "Error")
    exit 1
}

# Create notify icon in system tray
$icon = [System.Drawing.SystemIcons]::Application
$notifyIcon = New-Object System.Windows.Forms.NotifyIcon
$notifyIcon.Icon = $icon
$notifyIcon.Text = "Axon Host Manager (port 9099)"
$notifyIcon.Visible = $true

# Context menu with Exit option
$menu = New-Object System.Windows.Forms.ContextMenuStrip
$exitItem = $menu.Items.Add("Stop Host Manager")
$exitItem.Add_Click({
    $global:shouldExit = $true
    if ($global:nodeProcess -and -not $global:nodeProcess.HasExited) {
        $global:nodeProcess.Kill()
    }
    $notifyIcon.Visible = $false
    [System.Windows.Forms.Application]::Exit()
})
$notifyIcon.ContextMenuStrip = $menu

# Balloon notification
$notifyIcon.BalloonTipTitle = "Axon Host Manager"
$notifyIcon.BalloonTipText = "Host Manager is running on port 9099. Right-click the tray icon to stop."
$notifyIcon.BalloonTipIcon = "Info"

# Start node manager.js as a background process
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "node"
$psi.Arguments = "`"$managerJs`""
$psi.WorkingDirectory = $hostAgentDir
$psi.WindowStyle = "Hidden"
$psi.CreateNoWindow = $true
$psi.UseShellExecute = $false
$global:nodeProcess = [System.Diagnostics.Process]::Start($psi)

$notifyIcon.ShowBalloonTip(3000)

# Keep running until exit
$global:shouldExit = $false
$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 2000
$timer.Add_Tick({
    if ($global:nodeProcess.HasExited -and -not $global:shouldExit) {
        $notifyIcon.BalloonTipTitle = "Axon Host Manager"
        $notifyIcon.BalloonTipText = "Host Manager process stopped unexpectedly."
        $notifyIcon.BalloonTipIcon = "Warning"
        $notifyIcon.ShowBalloonTip(3000)
        $notifyIcon.Text = "Axon Host Manager (stopped)"
    }
})
$timer.Start()

[System.Windows.Forms.Application]::Run()
'''
    ps1_path.write_text(ps1_content, encoding="utf-8")

    # Windows: .cmd wrapper that launches the PowerShell script hidden
    cmd_path = orgs_path / "host-manager.cmd"
    cmd_content = '@echo off\r\n'\
        'REM Axon Host Agent Manager — launches minimized to system tray\r\n'\
        'powershell -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0host-manager.ps1"\r\n'
    cmd_path.write_text(cmd_content, encoding="utf-8")

    # Unix shell script — runs in background with start/stop/status/logs commands
    sh_path = orgs_path / "host-manager.sh"
    sh_content = '''#!/usr/bin/env bash
# Axon Host Agent Manager
# Usage: ./host-manager.sh [start|stop|status|logs]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MANAGER_DIR="$SCRIPT_DIR/../axon/host-agent"
PID_FILE="$SCRIPT_DIR/.host-manager.pid"
LOG_FILE="$SCRIPT_DIR/.host-manager.log"

case "${1:-start}" in
  start)
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      echo "Host Manager is already running (PID $(cat "$PID_FILE"))"
      exit 0
    fi
    if [ ! -f "$MANAGER_DIR/manager.js" ]; then
      echo "ERROR: manager.js not found at $MANAGER_DIR/manager.js"
      exit 1
    fi
    cd "$MANAGER_DIR"
    nohup node manager.js > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    echo "Axon Host Manager started (PID $!, port 9099)"
    echo "Logs: $LOG_FILE"
    echo "Stop: $0 stop"
    ;;
  stop)
    if [ -f "$PID_FILE" ]; then
      PID=$(cat "$PID_FILE")
      if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        echo "Host Manager stopped (PID $PID)"
      else
        echo "Host Manager was not running"
      fi
      rm -f "$PID_FILE"
    else
      echo "Host Manager is not running"
    fi
    ;;
  status)
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      echo "Host Manager is running (PID $(cat "$PID_FILE"))"
    else
      echo "Host Manager is not running"
    fi
    ;;
  logs)
    if [ -f "$LOG_FILE" ]; then
      tail -f "$LOG_FILE"
    else
      echo "No log file found"
    fi
    ;;
  *)
    echo "Usage: $0 {start|stop|status|logs}"
    exit 1
    ;;
esac
'''
    sh_path.write_text(sh_content, encoding="utf-8")
    try:
        sh_path.chmod(0o755)
    except Exception:
        pass

    logger.info("Host manager startup scripts written to %s", orgs_path)


async def _get_manager_status() -> dict:
    """Get status of all agents from the manager."""
    try:
        result = await _manager_request("GET", "/status")
        return result.get("agents", {})
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class RegisterHostAgentRequest(BaseModel):
    id: str
    name: str = ""
    path: str
    port: int = 9100
    host: str = "host.docker.internal"
    executables: list[str] = Field(default_factory=list)


class UpdateHostAgentRequest(BaseModel):
    name: str | None = None
    path: str | None = None
    port: int | None = None
    host: str | None = None
    executables: list[str] | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@org_router.get("")
async def list_host_agents(org_id: str):
    """List all registered host agents with live status."""
    org = _get_org_or_404(org_id)
    manager_status = await _get_manager_status()
    results = []
    for ha in org.config.host_agents:
        mgr = manager_status.get(ha.id, {})
        if mgr.get("status") == "running":
            ha.status = "running"
            results.append({**ha.model_dump(), **mgr})
        else:
            health = await _check_host_agent_health(ha)
            ha.status = health["status"]
            results.append({**ha.model_dump(), **health})
    return {"host_agents": results}


@org_router.post("", status_code=201)
async def register_host_agent(org_id: str, body: RegisterHostAgentRequest):
    """Register a new host agent."""
    org = _get_org_or_404(org_id)

    if any(ha.id == body.id for ha in org.config.host_agents):
        raise HTTPException(409, f"Host agent already registered: {body.id}")

    ha = HostAgentConfig(
        id=body.id,
        name=body.name or body.id,
        path=body.path,
        port=body.port,
        host=body.host,
        executables=body.executables,
    )
    org.config.host_agents.append(ha)
    _persist_host_agents(org_id, org.config.host_agents)
    _write_manager_scripts()
    return {"status": "registered", "host_agent": ha.model_dump()}


@org_router.get("/manager-status")
async def get_manager_status(org_id: str):
    """Check if the host agent manager is running and return script paths."""
    _get_org_or_404(org_id)

    manager_running = False
    try:
        await _manager_request("GET", "/status")
        manager_running = True
    except Exception:
        pass

    orgs_path = Path("/orgs")
    cmd_exists = (orgs_path / "host-manager.cmd").exists()
    sh_exists = (orgs_path / "host-manager.sh").exists()

    # Try to resolve host-side path from env or Docker mount info
    host_orgs_path = os.environ.get("AXON_ORGS_HOST_PATH", "")

    return {
        "manager_running": manager_running,
        "scripts_generated": cmd_exists or sh_exists,
        "host_orgs_path": host_orgs_path,
    }


@org_router.post("/regenerate-scripts")
async def regenerate_scripts(org_id: str):
    """Regenerate the host manager startup scripts in the orgs directory."""
    _get_org_or_404(org_id)
    _write_manager_scripts()
    return {"ok": True, "message": "Startup scripts regenerated in orgs folder"}


@org_router.get("/{agent_id}")
async def get_host_agent(org_id: str, agent_id: str):
    """Get a specific host agent."""
    org = _get_org_or_404(org_id)
    for ha in org.config.host_agents:
        if ha.id == agent_id:
            health = await _check_host_agent_health(ha)
            ha.status = health["status"]
            return {**ha.model_dump(), **health}
    raise HTTPException(404, f"Host agent not found: {agent_id}")


@org_router.patch("/{agent_id}")
async def update_host_agent(org_id: str, agent_id: str, body: UpdateHostAgentRequest):
    """Update a host agent."""
    org = _get_org_or_404(org_id)
    for ha in org.config.host_agents:
        if ha.id == agent_id:
            if body.name is not None:
                ha.name = body.name
            if body.path is not None:
                ha.path = body.path
            if body.port is not None:
                ha.port = body.port
            if body.host is not None:
                ha.host = body.host
            if body.executables is not None:
                ha.executables = body.executables
            _persist_host_agents(org_id, org.config.host_agents)
            # If the agent was running, restart with new config
            try:
                manager_status = await _get_manager_status()
                if manager_status.get(agent_id, {}).get("status") == "running":
                    await _manager_request("POST", "/restart", {
                        "id": ha.id,
                        "path": ha.path,
                        "port": ha.port,
                        "executables": ha.executables,
                    })
            except Exception:
                pass  # Manager not available — user will restart manually
            return {"status": "updated", "host_agent": ha.model_dump()}
    raise HTTPException(404, f"Host agent not found: {agent_id}")


@org_router.post("/{agent_id}/start")
async def start_host_agent(org_id: str, agent_id: str):
    """Start a host agent via the manager."""
    org = _get_org_or_404(org_id)
    config = _find_agent_config(org, agent_id)
    if not config:
        raise HTTPException(404, f"Host agent not found: {agent_id}")

    result = await _manager_request("POST", "/start", {
        "id": config.id,
        "path": config.path,
        "port": config.port,
        "executables": config.executables,
    })
    return result


@org_router.post("/{agent_id}/stop")
async def stop_host_agent(org_id: str, agent_id: str):
    """Stop a host agent via the manager."""
    org = _get_org_or_404(org_id)
    config = _find_agent_config(org, agent_id)
    if not config:
        raise HTTPException(404, f"Host agent not found: {agent_id}")

    result = await _manager_request("POST", "/stop", {"id": config.id})
    return result


@org_router.post("/{agent_id}/restart")
async def restart_host_agent(org_id: str, agent_id: str):
    """Restart a host agent with current config via the manager."""
    org = _get_org_or_404(org_id)
    config = _find_agent_config(org, agent_id)
    if not config:
        raise HTTPException(404, f"Host agent not found: {agent_id}")

    result = await _manager_request("POST", "/restart", {
        "id": config.id,
        "path": config.path,
        "port": config.port,
        "executables": config.executables,
    })
    return result


@org_router.delete("/{agent_id}")
async def delete_host_agent(org_id: str, agent_id: str):
    """Delete a host agent."""
    org = _get_org_or_404(org_id)
    before = len(org.config.host_agents)
    org.config.host_agents = [
        ha for ha in org.config.host_agents if ha.id != agent_id
    ]
    if len(org.config.host_agents) == before:
        raise HTTPException(404, f"Host agent not found: {agent_id}")
    _persist_host_agents(org_id, org.config.host_agents)
    return {"status": "deleted", "agent_id": agent_id}


@org_router.get("/{agent_id}/health")
async def host_agent_health(org_id: str, agent_id: str):
    """Check health of a specific host agent."""
    org = _get_org_or_404(org_id)
    for ha in org.config.host_agents:
        if ha.id == agent_id:
            return await _check_host_agent_health(ha)
    raise HTTPException(404, f"Host agent not found: {agent_id}")

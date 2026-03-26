"""Axon — FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from axon.audit import AuditLogger
from axon.usage import UsageTracker
from axon.config import (
    AgentType,
    PersonaConfig,
    discover_agents_from_vaults,
    settings,
)
from axon.agents.agent import Agent
from axon.agents.axon_agent import AxonAgent
from axon.agents.external_agent import ExternalAgent
from axon.agents.huddle import Huddle
from axon.org import (
    OrgConfig,
    OrgInstance,
    discover_orgs,
    ensure_huddle,
    load_org_config,
    scaffold_org,
)
import axon.registry as registry
from axon.vault.vault import VaultManager
from axon.routes import achievements as achievements_routes
from axon.routes import agents as agents_routes
from axon.routes import audit as audit_routes
from axon.routes import conversations as conversations_routes
from axon.routes import huddle as huddle_routes
from axon.routes import dashboard as dashboard_routes
from axon.routes import issues as issues_routes
from axon.routes import lifecycle as lifecycle_routes
from axon.routes import org_chart as org_chart_routes
from axon.routes import tasks as tasks_routes
from axon.routes import vaults as vaults_routes
from axon.routes import orgs as orgs_routes
from axon.routes import voices as voices_routes
from axon.routes import external_agents as external_agents_routes
from axon.routes import approvals as approvals_routes
from axon.routes import recruitment as recruitment_routes
from axon.routes import usage as usage_routes
from axon.routes import worker_control as worker_control_routes
from axon.routes import worker_setup as worker_setup_routes
from axon.routes import credentials as credentials_routes


logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    """Configure logging based on AXON_LOG_LEVEL setting (default: INFO)."""
    level = settings.axon_log_level.upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    # Always show memory pipeline at configured level
    for module in (
        "axon.vault.memory_manager",
        "axon.vault.memory_recall",
        "axon.vault.memory_learning",
        "axon.vault.memory_prompts",
        "axon.agents.agent",
    ):
        logging.getLogger(module).setLevel(getattr(logging, level, logging.INFO))


def _export_api_keys() -> None:
    """Push API keys from settings into os.environ for LiteLLM."""
    import os
    if settings.anthropic_api_key:
        os.environ.setdefault("ANTHROPIC_API_KEY", settings.anthropic_api_key)
    if settings.openai_api_key:
        os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)
    if settings.ollama_base_url:
        os.environ.setdefault("OLLAMA_API_BASE", settings.ollama_base_url)


def _init_org_agents(
    org_dir: Path,
    org_config: OrgConfig,
) -> OrgInstance:
    """Initialize all agents for a single organization."""
    data_dir = str(org_dir / "data")
    vaults_dir = org_dir / "vaults"

    # Discover agents from vault folders containing agent.yaml
    agents = discover_agents_from_vaults(vaults_dir)

    logger.debug(f"[{org_config.id}] Loaded {len(agents)} agents: {list(agents.keys())}")

    # Initialize shared vault
    shared_vault_path = vaults_dir / "shared"
    shared_vault: VaultManager | None = None
    if shared_vault_path.exists():
        shared_vault = VaultManager(str(shared_vault_path), "second-brain.md")

    # Initialize audit logger (writes to shared vault's audit/ branch)
    audit_logger: AuditLogger | None = None
    if shared_vault_path.exists():
        audit_logger = AuditLogger(str(shared_vault_path))

    # Initialize usage tracker (writes to data/usage/)
    usage_tracker = UsageTracker(data_dir)

    org = OrgInstance(
        config=org_config,
        shared_vault=shared_vault,
        audit_logger=audit_logger,
        usage_tracker=usage_tracker,
    )

    # Org-level comms config (for agents with comms enabled)
    org_comms = org_config.comms

    # Initialize specialist agents (type-based dispatch)
    specialists: dict[str, PersonaConfig] = {}
    for persona_id, config in agents.items():
        if config.type in (AgentType.ORCHESTRATOR, AgentType.HUDDLE):
            continue
        is_external = config.type == AgentType.EXTERNAL or config.external
        AgentClass = ExternalAgent if is_external else Agent
        agent = AgentClass(
            config, data_dir=data_dir,
            shared_vault=shared_vault,
            audit_logger=audit_logger,
            usage_tracker=usage_tracker,
            org_id=org_config.id,
            org_comms_config=org_comms,
        )
        org.agent_registry[persona_id] = agent
        if not is_external:
            specialists[persona_id] = config

    # Initialize orchestrators
    for persona_id, config in agents.items():
        if config.type != AgentType.ORCHESTRATOR:
            continue
        axon = AxonAgent(
            config, specialists, data_dir=data_dir,
            shared_vault=shared_vault,
            audit_logger=audit_logger,
            usage_tracker=usage_tracker,
            org_id=org_config.id,
            org_comms_config=org_comms,
        )
        org.agent_registry[persona_id] = axon

    # Initialize huddles
    for persona_id, config in agents.items():
        if config.type != AgentType.HUDDLE:
            continue
        advisor_configs = {
            k: v for k, v in agents.items()
            if v.type == AgentType.ADVISOR
        }
        advisor_agents = {
            k: org.agent_registry[k] for k in advisor_configs
            if k in org.agent_registry
        }
        org.huddle = Huddle(
            config, advisor_configs, data_dir=data_dir,
            usage_tracker=usage_tracker,
            shared_vault=shared_vault,
            org_id=org_config.id,
            advisor_agents=advisor_agents,
        )

    # Auto-create huddle if advisors exist but no huddle persona was defined
    if not org.huddle:
        ensure_huddle(org, settings.axon_orgs_dir)

    return org


def init_orgs() -> None:
    """Load all organizations and initialize their agents."""
    _configure_logging()
    _export_api_keys()

    orgs_dir = settings.axon_orgs_dir
    orgs_path = Path(orgs_dir)

    if not orgs_path.exists():
        raise RuntimeError(f"AXON_ORGS_DIR does not exist: {orgs_dir}")

    logger.info(f"Loading organizations from: {orgs_dir}")
    for org_path in discover_orgs(orgs_dir):
        org_config = load_org_config(org_path)
        logger.debug(f"Initializing org: {org_config.name} ({org_config.id})")
        org = _init_org_agents(org_path, org_config)
        registry.org_registry[org_config.id] = org

    if not registry.org_registry:
        raise RuntimeError(f"No organizations found in: {orgs_dir}")

    # Set default org: prefer "default", then the org with most agents
    if "default" in registry.org_registry:
        registry.default_org_id = "default"
    else:
        registry.default_org_id = max(
            registry.org_registry,
            key=lambda k: len(registry.org_registry[k].agent_registry),
        )

    # Populate legacy aliases from the default org
    default_org = registry.get_default_org()
    if default_org:
        registry.agent_registry = default_org.agent_registry
        registry.huddle_instance = default_org.huddle

    org_count = len(registry.org_registry)
    total_agents = sum(len(o.agent_registry) for o in registry.org_registry.values())
    logger.info(f"Ready: {org_count} org(s), {total_agents} agent(s)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    init_orgs()

    # Initialize database (SQLite by default, Postgres via DATABASE_URL)
    from axon.db import init_db, shutdown_db
    await init_db()

    # Clean up stale runner PIDs from previous backend runs
    from axon.runner_manager import runner_manager
    runner_manager.cleanup_stale_pids()

    # Start agent scheduler (proactive checks heartbeat)
    from axon.scheduler import scheduler
    scheduler.start()

    # Start Discord bot if configured
    discord_bot = None
    try:
        from axon.discord_bot import start_discord_bot
        discord_bot = await start_discord_bot()
    except ImportError:
        pass  # discord.py not installed
    except Exception as e:
        print(f"[AXON] Discord bot failed to start: {e}")

    # Start inbound email poller (for orgs with Resend configured)
    email_poller = None
    try:
        from axon.comms.inbound import InboundEmailPoller
        email_poller = InboundEmailPoller()
        await email_poller.start()
    except Exception as e:
        print(f"[AXON] Email poller failed to start: {e}")

    yield

    # Cleanup — stop vault file watchers
    for org in registry.org_registry.values():
        for agent in org.agent_registry.values():
            if hasattr(agent, "vault"):
                agent.vault.shutdown()

    # Stop all managed runner processes
    from axon.runner_manager import runner_manager
    await runner_manager.shutdown_all()

    await scheduler.stop()
    if email_poller:
        await email_poller.stop()
    await shutdown_db()
    if discord_bot:
        await discord_bot.close()


app = FastAPI(
    title="Axon",
    description="Self-hosted AI command center",
    version="0.2.0",
    lifespan=lifespan,
)

# ── Org-scoped routes ───────────────────────────────────────────────
app.include_router(orgs_routes.router, prefix="/api/orgs", tags=["orgs"])
app.include_router(agents_routes.org_router, prefix="/api/orgs/{org_id}/agents", tags=["agents"])
app.include_router(conversations_routes.org_router, prefix="/api/orgs/{org_id}/conversations", tags=["conversations"])
app.include_router(huddle_routes.org_router, prefix="/api/orgs/{org_id}/huddle", tags=["huddle"])
app.include_router(dashboard_routes.org_router, prefix="/api/orgs/{org_id}/dashboard", tags=["dashboard"])
app.include_router(vaults_routes.org_router, prefix="/api/orgs/{org_id}/vaults", tags=["vaults"])
app.include_router(tasks_routes.org_router, prefix="/api/orgs/{org_id}/tasks", tags=["tasks"])
app.include_router(issues_routes.org_router, prefix="/api/orgs/{org_id}/issues", tags=["issues"])
app.include_router(audit_routes.org_router, prefix="/api/orgs/{org_id}/audit", tags=["audit"])
app.include_router(lifecycle_routes.org_router, prefix="/api/orgs/{org_id}/lifecycle", tags=["lifecycle"])
app.include_router(achievements_routes.org_router, prefix="/api/orgs/{org_id}/achievements", tags=["achievements"])
app.include_router(org_chart_routes.org_router, prefix="/api/orgs/{org_id}/org-chart", tags=["org-chart"])
app.include_router(external_agents_routes.org_router, prefix="/api/orgs/{org_id}/external", tags=["external-agents"])
app.include_router(approvals_routes.org_router, prefix="/api/orgs/{org_id}/approvals", tags=["approvals"])
app.include_router(recruitment_routes.org_router, prefix="/api/orgs/{org_id}/recruitment", tags=["recruitment"])
app.include_router(worker_setup_routes.org_router, prefix="/api/orgs/{org_id}/workers", tags=["workers"])
app.include_router(worker_control_routes.org_router, prefix="/api/orgs/{org_id}/workers", tags=["workers"])
app.include_router(usage_routes.org_router, prefix="/api/orgs/{org_id}/usage", tags=["usage"])
app.include_router(credentials_routes.org_router, prefix="/api/orgs/{org_id}/credentials", tags=["credentials"])

# ── Legacy routes (backward compat — route to default org) ─────────
app.include_router(agents_routes.router, prefix="/api/agents", tags=["agents"])
app.include_router(conversations_routes.router, prefix="/api/conversations", tags=["conversations"])
app.include_router(huddle_routes.router, prefix="/api/huddle", tags=["huddle"])
app.include_router(dashboard_routes.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(vaults_routes.router, prefix="/api/vaults", tags=["vaults"])
app.include_router(tasks_routes.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(issues_routes.router, prefix="/api/issues", tags=["issues"])
app.include_router(audit_routes.router, prefix="/api/audit", tags=["audit"])
app.include_router(lifecycle_routes.router, prefix="/api/lifecycle", tags=["lifecycle"])
app.include_router(achievements_routes.router, prefix="/api/achievements", tags=["achievements"])
app.include_router(org_chart_routes.router, prefix="/api/org-chart", tags=["org-chart"])
app.include_router(voices_routes.router, prefix="/api/voices", tags=["voices"])
app.include_router(usage_routes.router, prefix="/api/usage", tags=["usage"])


@app.get("/api/health")
async def health():
    try:
        from axon.voice import is_available
        voice_available = is_available()
    except ImportError:
        voice_available = False

    return {
        "status": "ok",
        "orgs": list(registry.org_registry.keys()),
        "agents": list(registry.agent_registry.keys()),
        "huddle": registry.huddle_instance is not None,
        "voice": voice_available,
    }


@app.get("/api/debug/scheduler")
async def debug_scheduler():
    """Diagnostic endpoint — shows scheduler state and pending tasks."""
    from axon.scheduler import scheduler, AgentScheduler

    result = {
        "scheduler_running": scheduler._task is not None and not scheduler._task.done(),
        "last_runs": {k: v.isoformat() for k, v in scheduler._last_run.items()},
        "agents": {},
    }

    for org_id, org in registry.org_registry.items():
        for agent_id, agent in org.agent_registry.items():
            checks = getattr(agent.config.behavior, "proactive_checks", [])
            lock_held = (
                hasattr(agent, "_processing_lock") and agent._processing_lock.locked()
            )
            tasks = AgentScheduler._find_agent_tasks(agent, agent_id)
            result["agents"][agent_id] = {
                "proactive_checks": [
                    {"action": c.action, "trigger": c.trigger} for c in checks
                ],
                "processing_lock_held": lock_held,
                "has_shared_vault": agent.shared_vault is not None,
                "in_progress_tasks": [
                    {
                        "path": t["path"],
                        "name": t.get("name"),
                        "assignee": t.get("assignee"),
                        "conversation_id": t.get("conversation_id", "")[:8] + "...",
                    }
                    for t in tasks
                ],
            }

    return result


@app.post("/api/debug/trigger-tasks/{agent_id}")
async def debug_trigger_tasks(agent_id: str):
    """Manually trigger task execution for an agent."""
    from axon.scheduler import scheduler

    for org_id, org in registry.org_registry.items():
        if agent_id in org.agent_registry:
            await scheduler.trigger_task_execution(org_id, agent_id)
            return {"status": "triggered", "org_id": org_id, "agent_id": agent_id}

    return {"status": "error", "detail": f"Agent {agent_id} not found"}

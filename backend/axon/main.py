"""Axon — FastAPI application entry point."""

from __future__ import annotations

import asyncio
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
from axon.routes import approvals as approvals_routes
from axon.routes import recruitment as recruitment_routes
from axon.routes import usage as usage_routes
from axon.routes import credentials as credentials_routes
from axon.routes import sandbox as sandbox_routes
from axon.routes import sandbox_images as sandbox_images_routes
from axon.routes import discovery as discovery_routes
from axon.routes import plugin_instances as plugin_instances_routes
from axon.routes import plugins as plugins_routes
from axon.routes import skills as skills_routes
from axon.routes import user_prefs as user_prefs_routes
from axon.routes import teams_webhook as teams_webhook_routes
from axon.routes import zoom_webhook as zoom_webhook_routes
from axon.routes import push as push_routes
from axon.routes import git_repos as git_repos_routes
from axon.routes import models as models_routes
from axon.routes import host_agents as host_agents_routes
from axon.routes import pipelines as pipelines_routes
from axon.routes import performance as performance_routes
from axon.routes import analytics as analytics_routes
from axon.routes import calendar as calendar_routes


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
    agents = discover_agents_from_vaults(vaults_dir, org_model_config=org_config.models)

    # Auto-wire parent delegation: parent can_delegate_to children
    for agent_id, config in agents.items():
        if config.parent_id and config.parent_id in agents:
            parent_cfg = agents[config.parent_id]
            if agent_id not in parent_cfg.delegation.can_delegate_to and "*" not in parent_cfg.delegation.can_delegate_to:
                parent_cfg.delegation.can_delegate_to.append(agent_id)

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
        agent = Agent(
            config, data_dir=data_dir,
            shared_vault=shared_vault,
            audit_logger=audit_logger,
            usage_tracker=usage_tracker,
            org_id=org_config.id,
            org_comms_config=org_comms,
            org_model_config=org_config.models,
        )
        org.agent_registry[persona_id] = agent
        if not config.parent_id:
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
            org_model_config=org_config.models,
        )
        org.agent_registry[persona_id] = axon

    # Initialize huddles
    for persona_id, config in agents.items():
        if config.type != AgentType.HUDDLE:
            continue
        advisor_configs = {
            k: v for k, v in agents.items()
            if v.type == AgentType.ADVISOR and not v.parent_id
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

    # Migrate legacy per-agent plugin configs → org-level instances
    if not org_config.plugin_instances:
        from axon.plugins.migration import migrate_plugin_configs, persist_instances_to_org
        instances = migrate_plugin_configs(org_dir, org.agent_registry)
        if instances:
            org_config.plugin_instances = instances
            persist_instances_to_org(org_dir, instances)

    # Build peer rosters — each agent learns about its immediate teammates
    for agent_id, agent in org.agent_registry.items():
        if hasattr(agent, "build_roster") and not isinstance(agent, AxonAgent):
            agent.build_roster(agents)

    # Load org principles from shared vault and inject into all agents + huddle
    principles_text = ""
    if shared_vault:
        principles_file = org_config.principles_file or "principles.md"
        principles_path = shared_vault_path / principles_file
        if principles_path.exists():
            principles_text = principles_path.read_text(encoding="utf-8").strip()
            logger.info("[%s] Loaded org principles from %s (%d chars)", org_config.id, principles_file, len(principles_text))

    if principles_text:
        for agent in org.agent_registry.values():
            if hasattr(agent, "_org_principles"):
                agent._org_principles = principles_text
        if org.huddle:
            org.huddle._org_principles = principles_text

    # Load pipeline definitions
    from axon.pipelines.loader import load_org_pipelines
    load_org_pipelines(org_dir, org_config.id)

    return org


def init_orgs() -> None:
    """Load all organizations and initialize their agents."""
    _configure_logging()
    _export_api_keys()

    # Discover available integrations, then register all plugins (including integration adapters)
    from axon.integrations.registry import discover_integrations
    discover_integrations()

    from axon.plugins.registry import discover_plugins
    discover_plugins()

    from axon.skills.registry import discover_skills
    discover_skills()

    from axon.patterns.registry import discover_patterns
    discover_patterns()

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

    # Rediscover running sandbox containers from Docker (survives backend restart)
    from axon.sandbox.manager import sandbox_manager
    try:
        recovered = await sandbox_manager.rediscover()
        if recovered:
            logger.info("Rediscovered %d running sandbox container(s)", recovered)
    except Exception:
        pass

    # Initialize database (SQLite by default, Postgres via DATABASE_URL)
    from axon.db import init_db, shutdown_db
    await init_db()

    # Seed org settings into central DB from org.yaml (first-run migration)
    from axon.db.engine import get_session as _get_session
    from axon.db.crud import org_settings as org_settings_crud

    async for session in _get_session():
        for org_id, org in registry.org_registry.items():
            await org_settings_crud.seed_from_config(
                session,
                org_id=org_id,
                name=org.config.name,
                description=org.config.description,
                org_type=org.config.type.value if hasattr(org.config.type, "value") else str(org.config.type),
                comms={
                    "require_approval": org.config.comms.require_approval,
                    "email_domain": org.config.comms.email_domain,
                    "email_signature": org.config.comms.email_signature,
                    "inbound_polling": org.config.comms.inbound_polling,
                },
            )

    # Load integration credentials now that DB is available
    for org in registry.org_registry.values():
        for agent in org.agent_registry.values():
            if hasattr(agent, "setup"):
                await agent.setup()

    # Start agent scheduler (proactive checks heartbeat)
    from axon.scheduler import scheduler
    scheduler.start()

    # Warm vault caches in background threads so lazy-load doesn't block the
    # event loop later (which would starve Discord/Slack heartbeats).
    vault_warm_tasks = []
    for org in registry.org_registry.values():
        for agent in org.agent_registry.values():
            if hasattr(agent, "vault") and agent.vault is not None:
                vault_warm_tasks.append(agent.vault.warm_cache())
    if vault_warm_tasks:
        await asyncio.gather(*vault_warm_tasks, return_exceptions=True)
        logger.info("Vault caches warmed for %d agent(s)", len(vault_warm_tasks))

    # Generate host manager startup scripts in the orgs directory
    from axon.routes.host_agents import _write_manager_scripts
    _write_manager_scripts()

    # Warm local LLM models (navigator, memory) so first request isn't slow
    async def _warm_local_models() -> None:
        """Send a tiny prompt to each local model so Ollama loads them into memory."""
        warmed: set[str] = set()
        for org in registry.org_registry.values():
            if not org.config.models:
                continue
            roles = org.config.models.roles
            for model_id in [roles.navigator, roles.memory]:
                if not model_id or not model_id.startswith("ollama/") or model_id in warmed:
                    continue
                try:
                    from axon.agents.provider import complete
                    await asyncio.wait_for(
                        complete("hi", model=model_id, max_tokens=1, temperature=0),
                        timeout=60,
                    )
                    warmed.add(model_id)
                    logger.info("[WARMUP] Loaded %s into memory", model_id)
                except Exception as e:
                    logger.warning("[WARMUP] Failed to warm %s: %s", model_id, e)

    asyncio.create_task(_warm_local_models())

    # Start Discord and Slack bots if configured (also supports hot-start later)
    from axon.bot_manager import set_discord_bot, set_slack_bot

    try:
        from axon.discord_bot import start_discord_bot
        discord_bot = await start_discord_bot()
        if discord_bot:
            set_discord_bot(discord_bot)
            print("[AXON] Discord bot started")
        else:
            print("[AXON] Discord bot skipped (no token or no channel mappings)")
    except ImportError:
        print("[AXON] Discord bot skipped (discord.py not installed)")
    except Exception as e:
        print(f"[AXON] Discord bot failed to start: {e}")

    try:
        from axon.slack_bot import start_slack_bot
        slack_bot = await start_slack_bot()
        if slack_bot:
            set_slack_bot(slack_bot)
            print("[AXON] Slack bot started")
        else:
            print("[AXON] Slack bot skipped (no token or no channel mappings)")
    except ImportError:
        print("[AXON] Slack bot skipped (slack_bolt not installed)")
    except Exception as e:
        print(f"[AXON] Slack bot failed to start: {e}")

    # Initialize Teams bot if configured (webhook-based, no background task)
    try:
        from axon.teams_bot import create_teams_bot
        from axon.routes.teams_webhook import set_teams_bot
        from axon.comms.credentials import resolve_credential
        teams_bot = create_teams_bot()
        if teams_bot:
            teams_creds: dict[str, tuple[str, str]] = {}
            for org_id, org in registry.org_registry.items():
                if org.config.comms.teams:
                    app_id = await resolve_credential(org_id, "teams_app_id") or ""
                    app_secret = await resolve_credential(org_id, "teams_app_secret") or ""
                    if app_id:
                        teams_creds[org_id] = (app_id, app_secret)
            set_teams_bot(teams_bot, teams_creds)
            print(f"[AXON] Teams bot initialized ({len(teams_creds)} org(s))")
        else:
            print("[AXON] Teams bot skipped (no config)")
    except ImportError:
        print("[AXON] Teams bot skipped (dependencies not installed)")
    except Exception as e:
        print(f"[AXON] Teams bot failed to initialize: {e}")

    # Initialize Zoom bot if configured (webhook-based)
    try:
        from axon.zoom_bot import create_zoom_bot
        from axon.routes.zoom_webhook import set_zoom_bot
        from axon.comms.credentials import resolve_credential as _resolve_cred
        zoom_bot = create_zoom_bot()
        if zoom_bot:
            zoom_creds: dict[str, tuple[str, str, str]] = {}
            for org_id, org in registry.org_registry.items():
                if org.config.comms.zoom:
                    acct = await _resolve_cred(org_id, "zoom_account_id") or ""
                    cid = await _resolve_cred(org_id, "zoom_client_id") or ""
                    csec = await _resolve_cred(org_id, "zoom_client_secret") or ""
                    if acct:
                        zoom_creds[org_id] = (acct, cid, csec)
            verification = await _resolve_cred(
                next(iter(zoom_creds), ""), "zoom_verification_token",
            ) or ""
            set_zoom_bot(zoom_bot, zoom_creds, verification)
            print(f"[AXON] Zoom bot initialized ({len(zoom_creds)} org(s))")
        else:
            print("[AXON] Zoom bot skipped (no config)")
    except ImportError:
        print("[AXON] Zoom bot skipped (dependencies not installed)")
    except Exception as e:
        print(f"[AXON] Zoom bot failed to initialize: {e}")

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

    await scheduler.stop()
    if email_poller:
        await email_poller.stop()
    from axon.db.agent_engine import shutdown_all_agent_dbs
    await shutdown_all_agent_dbs()
    await shutdown_db()
    from axon.bot_manager import shutdown as shutdown_bots
    await shutdown_bots()


def _read_version() -> str:
    """Read version from VERSION file at project root."""
    for candidate in [Path("/app/VERSION"), Path(__file__).resolve().parents[2] / "VERSION"]:
        if candidate.is_file():
            return candidate.read_text().strip()
    return "0.0.0-dev"


AXON_VERSION = _read_version()

app = FastAPI(
    title="Axon",
    description="Self-hosted AI command center",
    version=AXON_VERSION,
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
app.include_router(approvals_routes.org_router, prefix="/api/orgs/{org_id}/approvals", tags=["approvals"])
app.include_router(recruitment_routes.org_router, prefix="/api/orgs/{org_id}/recruitment", tags=["recruitment"])
app.include_router(sandbox_images_routes.org_router, prefix="/api/orgs/{org_id}/sandbox/images", tags=["sandbox-images"])
app.include_router(sandbox_routes.org_router, prefix="/api/orgs/{org_id}/sandbox", tags=["sandbox"])
app.include_router(discovery_routes.org_router, prefix="/api/orgs/{org_id}/discovery", tags=["discovery"])
app.include_router(models_routes.org_router, prefix="/api/orgs/{org_id}/models", tags=["models"])
app.include_router(host_agents_routes.org_router, prefix="/api/orgs/{org_id}/host-agents", tags=["host-agents"])
app.include_router(plugins_routes.org_router, prefix="/api/orgs/{org_id}/plugins", tags=["plugins"])
app.include_router(plugin_instances_routes.org_router, prefix="/api/orgs/{org_id}/plugins", tags=["plugin-instances"])
app.include_router(skills_routes.org_router, prefix="/api/orgs/{org_id}/skills", tags=["skills"])
app.include_router(usage_routes.org_router, prefix="/api/orgs/{org_id}/usage", tags=["usage"])
app.include_router(credentials_routes.org_router, prefix="/api/orgs/{org_id}/credentials", tags=["credentials"])
app.include_router(git_repos_routes.org_router, prefix="/api/orgs/{org_id}/git-repos", tags=["git-repos"])
app.include_router(pipelines_routes.org_router, prefix="/api/orgs/{org_id}/pipelines", tags=["pipelines"])
app.include_router(performance_routes.org_router, prefix="/api/orgs/{org_id}", tags=["performance"])
app.include_router(analytics_routes.org_router, prefix="/api/orgs/{org_id}/analytics", tags=["analytics"])
app.include_router(calendar_routes.org_router, prefix="/api/orgs/{org_id}/calendar", tags=["calendar"])

# ── Global routes (not org-scoped) ─────────────────────────────────
app.include_router(user_prefs_routes.router, prefix="/api/preferences", tags=["preferences"])
app.include_router(teams_webhook_routes.router, prefix="/api/teams", tags=["teams"])
app.include_router(zoom_webhook_routes.router, prefix="/api/zoom", tags=["zoom"])
app.include_router(push_routes.router, prefix="/api/push", tags=["push"])

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
app.include_router(analytics_routes.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(calendar_routes.router, prefix="/api/calendar", tags=["calendar"])


@app.get("/api/version")
async def version():
    return {"version": AXON_VERSION}


@app.get("/api/health")
async def health():
    try:
        from axon.voice import is_available
        voice_available = is_available()
    except ImportError:
        voice_available = False

    return {
        "status": "ok",
        "version": AXON_VERSION,
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
            has_pending_inbox = False  # Inbox concept removed — kept for API compat
            result["agents"][agent_id] = {
                "proactive_checks": [
                    {"action": c.action, "trigger": c.trigger} for c in checks
                ],
                "processing_lock_held": lock_held,
                "has_shared_vault": agent.shared_vault is not None,
                "has_pending_inbox": has_pending_inbox,
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

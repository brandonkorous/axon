"""Axon — FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from axon.config import PersonaConfig, load_all_personas, settings
from axon.agents.agent import Agent
from axon.agents.axon_agent import AxonAgent
from axon.agents.boardroom import Boardroom
from axon.routes import agents as agents_routes
from axon.routes import conversations as conversations_routes
from axon.routes import boardroom as boardroom_routes
from axon.routes import dashboard as dashboard_routes
from axon.routes import vaults as vaults_routes


# Global state — agent instances
agent_registry: dict[str, Agent] = {}
boardroom_instance: Boardroom | None = None


def init_agents() -> None:
    """Load all persona configs and initialize agent instances."""
    global boardroom_instance

    personas = load_all_personas(settings.axon_personas_dir)

    # Initialize specialist agents first
    specialists: dict[str, PersonaConfig] = {}
    for persona_id, config in personas.items():
        if persona_id in ("axon", "boardroom"):
            continue
        agent = Agent(config, data_dir=settings.axon_data_dir)
        agent_registry[persona_id] = agent
        specialists[persona_id] = config

    # Initialize Axon orchestrator
    axon_config = personas.get("axon")
    if axon_config:
        axon = AxonAgent(axon_config, specialists, data_dir=settings.axon_data_dir)
        agent_registry["axon"] = axon

    # Initialize Boardroom
    boardroom_config = personas.get("boardroom")
    if boardroom_config:
        advisor_configs = {k: v for k, v in personas.items() if k not in ("axon", "boardroom")}
        boardroom_instance = Boardroom(
            boardroom_config, advisor_configs, data_dir=settings.axon_data_dir
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    init_agents()
    yield


app = FastAPI(
    title="Axon",
    description="Self-hosted AI command center",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
app.include_router(agents_routes.router, prefix="/api/agents", tags=["agents"])
app.include_router(conversations_routes.router, prefix="/api/conversations", tags=["conversations"])
app.include_router(boardroom_routes.router, prefix="/api/boardroom", tags=["boardroom"])
app.include_router(dashboard_routes.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(vaults_routes.router, prefix="/api/vaults", tags=["vaults"])


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "agents": list(agent_registry.keys()),
        "boardroom": boardroom_instance is not None,
    }

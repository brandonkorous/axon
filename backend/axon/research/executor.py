"""ResearchToolExecutor — orchestrates multi-step research workflows.

Uses a two-tier LLM strategy:
- Local model (Ollama): compresses raw sources from ~4000 to ~500 chars each
- Agent model (Claude/GPT): does the actual thinking, analysis, and writing

This keeps costs low while maintaining quality. The expensive model only
sees pre-digested, high-signal content.
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from axon.logging import get_logger
from axon.research.config import ArtifactType, ResearchConfig, ResearchDepth
from axon.research.templates import get_template

logger = get_logger(__name__)


class ResearchSession:
    """Tracks state for an in-progress research task."""

    def __init__(self, config: ResearchConfig) -> None:
        self.config = config
        self.sources: list[dict[str, Any]] = []
        self.synthesis: str = ""

    def add_source(self, title: str, content: str, url: str = "", relevance: str = "medium") -> int:
        self.sources.append({
            "title": title,
            "url": url,
            "content": content,
            "relevance": relevance,
        })
        return len(self.sources)

    def source_summary(self) -> str:
        lines = []
        for i, s in enumerate(self.sources, 1):
            url_part = f" — {s['url']}" if s["url"] else ""
            lines.append(f"{i}. [{s['relevance']}] {s['title']}{url_part}")
        return "\n".join(lines)


class ResearchToolExecutor:
    """Handles research_* tool calls for a single agent."""

    def __init__(self, vault_write_fn: Any = None) -> None:
        self._sessions: dict[str, ResearchSession] = {}  # agent_id → session
        self._vault_write = vault_write_fn

    def _session(self, agent_id: str) -> ResearchSession | None:
        return self._sessions.get(agent_id)

    async def execute(self, tool_name: str, arguments: str, agent_id: str = "") -> str:
        args = json.loads(arguments) if arguments else {}

        if tool_name == "research_start":
            return self._handle_start(agent_id, args)
        elif tool_name == "research_add_source":
            return await self._handle_add_source(agent_id, args)
        elif tool_name == "research_synthesize":
            return await self._handle_synthesize(agent_id, args)
        elif tool_name == "research_publish":
            return await self._handle_publish(agent_id, args)
        else:
            return json.dumps({"error": f"Unknown research tool: {tool_name}"})

    def _handle_start(self, agent_id: str, args: dict) -> str:
        config = ResearchConfig(
            topic=args["topic"],
            artifact_type=ArtifactType(args.get("artifact_type", "report")),
            depth=ResearchDepth(args.get("depth", "standard")),
            focus_areas=args.get("focus_areas", []),
        )
        self._sessions[agent_id] = ResearchSession(config)

        return json.dumps({
            "status": "started",
            "topic": config.topic,
            "artifact_type": config.artifact_type.value,
            "depth": config.depth.value,
            "max_sources": config.max_sources,
            "local_synthesis": config.synthesize_locally,
            "next_step": "Use web_search and research_add_source to gather sources",
        })

    async def _handle_add_source(self, agent_id: str, args: dict) -> str:
        session = self._session(agent_id)
        if not session:
            return json.dumps({"error": "No active research session. Call research_start first."})

        raw_content = args["content"]
        title = args["title"]

        # Compress source via local LLM if enabled
        content = raw_content
        digested = False
        if session.config.synthesize_locally and len(raw_content) > 1000:
            from axon.research.synthesizer import digest_source
            content = await digest_source(
                content=raw_content,
                title=title,
                topic=session.config.topic,
                model=session.config.synthesis_model,
            )
            digested = content != raw_content

        count = session.add_source(
            title=title,
            content=content,
            url=args.get("url", ""),
            relevance=args.get("relevance", "medium"),
        )

        return json.dumps({
            "status": "source_added",
            "source_count": count,
            "max_sources": session.config.max_sources,
            "ready_to_synthesize": count >= 2,
            "digested": digested,
            "original_length": len(raw_content),
            "stored_length": len(content),
        })

    async def _handle_synthesize(self, agent_id: str, args: dict) -> str:
        session = self._session(agent_id)
        if not session:
            return json.dumps({"error": "No active research session."})

        if not session.sources:
            return json.dumps({"error": "No sources added yet."})

        # Use local LLM for multi-source synthesis if enabled
        if session.config.synthesize_locally:
            from axon.research.synthesizer import synthesize_sources
            synthesis = await synthesize_sources(
                sources=session.sources,
                topic=session.config.topic,
                model=session.config.synthesis_model,
            )
            session.synthesis = synthesis

            return json.dumps({
                "status": "synthesized",
                "source_count": len(session.sources),
                "synthesis": synthesis,
                "next_step": "Use research_publish to create the final artifact",
            })

        # Fallback — build raw context for agent's LLM
        source_texts = []
        for i, s in enumerate(session.sources, 1):
            source_texts.append(
                f"### Source {i}: {s['title']} [{s['relevance']}]\n{s['content']}"
            )

        synthesis_context = (
            f"## Research Topic: {session.config.topic}\n\n"
            f"## Sources ({len(session.sources)} gathered):\n\n"
            + "\n\n".join(source_texts)
        )

        prompt = args.get("synthesis_prompt", "")
        if prompt:
            synthesis_context += f"\n\n## Synthesis Guidance:\n{prompt}"

        return json.dumps({
            "status": "ready_to_synthesize",
            "source_count": len(session.sources),
            "context": synthesis_context,
            "next_step": "Use research_publish to create the final artifact",
        })

    async def _handle_publish(self, agent_id: str, args: dict) -> str:
        session = self._session(agent_id)
        if not session:
            return json.dumps({"error": "No active research session."})

        title = args["title"]
        summary = args["summary"]
        findings = args["findings"]
        analysis = args.get("analysis", "")
        vault_path = args.get("vault_path", "")

        # Build source attribution
        sources_md = _format_sources(session.sources)

        # Fill template
        template = get_template(session.config.artifact_type)
        content = template.format(
            title=title,
            summary=summary,
            findings=findings,
            analysis=analysis,
            sources=sources_md,
            depth=session.config.depth.value,
            source_count=len(session.sources),
            date=date.today().isoformat(),
            implications=analysis,
            recommendation=analysis,
        )

        # Determine vault path
        if not vault_path:
            slug = title.lower().replace(" ", "-")[:50]
            vault_path = f"research/{slug}"

        # Clean up session
        del self._sessions[agent_id]

        return json.dumps({
            "status": "published",
            "vault_path": vault_path,
            "artifact_type": session.config.artifact_type.value,
            "source_count": len(session.sources),
            "content": content,
            "message": f"Research artifact '{title}' ready. Write to vault at {vault_path}.",
        })


def _format_sources(sources: list[dict[str, Any]]) -> str:
    """Format sources as markdown reference list."""
    lines = []
    for i, s in enumerate(sources, 1):
        if s["url"]:
            lines.append(f"{i}. [{s['title']}]({s['url']})")
        else:
            lines.append(f"{i}. {s['title']}")
    return "\n".join(lines) if lines else "No external sources."

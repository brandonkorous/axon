"""Slash commands — direct user commands that bypass the LLM pipeline."""

from __future__ import annotations

import logging
import re
from datetime import date
from typing import Any, Callable, Awaitable

from fastapi import WebSocket

logger = logging.getLogger("axon.commands")


# ── Command registry ─────────────────────────────────────────────

COMMAND_REGISTRY: dict[str, dict[str, Any]] = {
    "sleep": {"description": "Trigger memory consolidation", "has_args": False},
    "remember": {"description": "Force-write a vault entry", "has_args": True, "arg_hint": "<text>"},
    "forget": {"description": "Archive matching vault entries", "has_args": True, "arg_hint": "<query>"},
    "recall": {"description": "Search memory and surface results", "has_args": True, "arg_hint": "<query>"},
    "tasks": {"description": "Show running/pending tasks", "has_args": False},
    "status": {"description": "Agent status and memory stats", "has_args": False},
    "discover": {"description": "Search available capabilities", "has_args": True, "arg_hint": "<query>"},
}


async def execute_command(agent: Any, name: str, args: str, websocket: WebSocket) -> None:
    """Route a slash command to its handler."""
    handler = _HANDLERS.get(name)
    if not handler:
        await _send_result(websocket, agent.id, name, f"Unknown command: /{name}", success=False)
        return
    await handler(agent, args, websocket)


async def _send_result(
    ws: WebSocket, agent_id: str, command: str, content: str, *, success: bool = True,
) -> None:
    await ws.send_json({
        "type": "command_result",
        "agent_id": agent_id,
        "command": command,
        "content": content,
        "success": success,
    })


# ── /sleep — trigger memory consolidation ────────────────────────

async def _cmd_sleep(agent: Any, args: str, ws: WebSocket) -> None:
    if not agent.memory_manager:
        await _send_result(ws, agent.id, "sleep", "Memory manager not enabled for this agent.", success=False)
        return

    await _send_result(ws, agent.id, "sleep", "Running memory consolidation...")

    try:
        if agent.memory_manager.config.deep_consolidation_enabled:
            await agent.memory_manager.deep_consolidate()
            # Read the report from the consolidation
            learnings = agent.vault.list_branch("learnings")
            active = sum(1 for l in learnings if _is_active(agent.vault, l))
            await _send_result(
                ws, agent.id, "sleep",
                f"Deep consolidation complete.\n"
                f"  Learnings in vault: {len(learnings)}\n"
                f"  Active: {active}\n"
                f"  Archived: {len(learnings) - active}",
            )
        else:
            await agent.memory_manager.consolidate()
            learnings = agent.vault.list_branch("learnings")
            await _send_result(
                ws, agent.id, "sleep",
                f"Consolidation complete (confidence decay applied).\n"
                f"  Learnings in vault: {len(learnings)}",
            )
    except Exception as e:
        logger.error("Slash /sleep failed: %s", e, exc_info=True)
        await _send_result(ws, agent.id, "sleep", f"Consolidation failed: {e}", success=False)


def _is_active(vault: Any, entry: dict) -> bool:
    """Check if a vault entry is active (not archived)."""
    path = entry.get("path", "")
    if not path:
        return False
    try:
        metadata, _ = vault.read_file(path)
        return metadata.get("status", "active") == "active"
    except Exception:
        return False


# ── /remember — force-write a vault entry ────────────────────────

async def _cmd_remember(agent: Any, args: str, ws: WebSocket) -> None:
    if not args.strip():
        await _send_result(ws, agent.id, "remember", "Usage: /remember <text to save>", success=False)
        return

    today = str(date.today())
    text = args.strip()

    # Generate slug from text
    slug = text[:50].lower().replace(" ", "-")
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    filename = f"{today}-{slug}"

    metadata: dict[str, Any] = {
        "name": text[:100],
        "description": text[:200],
        "type": "learning",
        "learning_type": "manual",
        "confidence": 0.9,
        "confidence_history": [{
            "date": today,
            "value": 0.9,
            "reason": "manually saved via /remember",
        }],
        "validated_by": [],
        "contradicted_by": [],
        "last_validated": today,
        "source_conversations": 1,
        "tags": "",
        "status": "active",
        "date": today,
    }

    body = f"## Insight\n{text}\n"

    try:
        path = agent.vault.create_file("learnings", filename, metadata, body)
        await _send_result(ws, agent.id, "remember", f"Saved to vault: {path}")
    except Exception as e:
        logger.error("Slash /remember failed: %s", e, exc_info=True)
        await _send_result(ws, agent.id, "remember", f"Failed to save: {e}", success=False)


# ── /forget — archive matching vault entries ─────────────────────

async def _cmd_forget(agent: Any, args: str, ws: WebSocket) -> None:
    if not args.strip():
        await _send_result(ws, agent.id, "forget", "Usage: /forget <query>", success=False)
        return

    results = agent.vault.search(args.strip(), max_results=10)
    if not results:
        await _send_result(ws, agent.id, "forget", f"No entries found matching: {args.strip()}")
        return

    archived: list[str] = []
    for result in results:
        path = result.get("path", "")
        if not path:
            continue
        try:
            metadata, body = agent.vault.read_file(path)
            if metadata.get("status") == "archived":
                continue
            metadata["status"] = "archived"
            history = metadata.get("confidence_history", [])
            history.append({
                "date": str(date.today()),
                "value": float(metadata.get("confidence", 0.5)),
                "reason": "archived via /forget command",
            })
            metadata["confidence_history"] = history
            agent.vault.write_file(path, metadata, body)
            archived.append(metadata.get("name", path))
        except Exception as e:
            logger.warning("Failed to archive %s: %s", path, e)

    if archived:
        names = "\n".join(f"  - {n}" for n in archived)
        await _send_result(ws, agent.id, "forget", f"Archived {len(archived)} entries:\n{names}")
    else:
        await _send_result(ws, agent.id, "forget", "No active entries to archive.")


# ── /recall — search memory and surface results ─────────────────

async def _cmd_recall(agent: Any, args: str, ws: WebSocket) -> None:
    if not args.strip():
        await _send_result(ws, agent.id, "recall", "Usage: /recall <query>", success=False)
        return

    try:
        if agent.memory_manager:
            context = await agent.memory_manager.recall(args.strip())
        else:
            results = agent.vault.search(args.strip(), max_results=10)
            lines: list[str] = []
            for r in results:
                name = r.get("name", r.get("path", "unknown"))
                path = r.get("path", "")
                lines.append(f"- **{name}** (`{path}`)")
            context = "\n".join(lines) if lines else "No results found."

        await _send_result(ws, agent.id, "recall", context if context else "No relevant memories found.")
    except Exception as e:
        logger.error("Slash /recall failed: %s", e, exc_info=True)
        await _send_result(ws, agent.id, "recall", f"Recall failed: {e}", success=False)


# ── /tasks — show running/pending tasks ──────────────────────────

async def _cmd_tasks(agent: Any, args: str, ws: WebSocket) -> None:
    if not agent.shared_vault:
        await _send_result(ws, agent.id, "tasks", "No shared vault configured.", success=False)
        return

    try:
        entries = agent.shared_vault.list_branch("tasks")
        tasks: list[str] = []
        for entry in entries:
            path = entry.get("path", "")
            if not path or path.endswith("-index.md"):
                continue
            try:
                metadata, _ = agent.shared_vault.read_file(path)
                status = metadata.get("status", "unknown")
                assignee = metadata.get("assignee", "unassigned")
                name = metadata.get("name", path)
                if status in ("done", "cancelled"):
                    continue
                marker = "*" if assignee == agent.id else " "
                tasks.append(f"  [{marker}] {name}  ({status}, assignee: {assignee})")
            except Exception:
                continue

        if tasks:
            header = f"Tasks ({len(tasks)} active):\n"
            await _send_result(ws, agent.id, "tasks", header + "\n".join(tasks))
        else:
            await _send_result(ws, agent.id, "tasks", "No active tasks.")
    except Exception as e:
        logger.error("Slash /tasks failed: %s", e, exc_info=True)
        await _send_result(ws, agent.id, "tasks", f"Failed to list tasks: {e}", success=False)


# ── /status — agent status and memory stats ──────────────────────

async def _cmd_status(agent: Any, args: str, ws: WebSocket) -> None:
    try:
        lines: list[str] = []

        # Lifecycle
        lc = agent.lifecycle.to_dict()
        lines.append(f"Status: {lc['status']}")
        if lc.get("strategy_override"):
            lines.append(f"Strategy: {lc['strategy_override'][:80]}...")
        lines.append(f"Rate limit: {lc['rate_limit']['count']}/{lc['rate_limit']['max_per_minute']} per min")
        if lc.get("queued_messages"):
            lines.append(f"Queued messages: {lc['queued_messages']}")

        # Model
        lines.append(f"Model: {agent.config.model.reasoning}")

        # Conversation
        lines.append(f"Conversation messages: {len(agent.conversation.messages)}")

        # Memory
        if agent.memory_manager:
            lines.append(f"Memory turns processed: {agent.memory_manager._turn_count}")
            learnings = agent.vault.list_branch("learnings")
            lines.append(f"Vault learnings: {len(learnings)}")

        # Graph
        stats = agent.vault.graph.get_stats()
        lines.append(f"Vault graph: {stats.get('nodes', 0)} nodes, {stats.get('edges', 0)} edges")

        await _send_result(ws, agent.id, "status", "\n".join(lines))
    except Exception as e:
        logger.error("Slash /status failed: %s", e, exc_info=True)
        await _send_result(ws, agent.id, "status", f"Failed to get status: {e}", success=False)


# ── /discover — search available capabilities ──────────────────

async def _cmd_discover(agent: Any, args: str, ws: WebSocket) -> None:
    if not args.strip():
        await _send_result(ws, agent.id, "discover", "Usage: /discover <query>", success=False)
        return

    try:
        from axon.discovery.searcher import search_capabilities
        from axon.discovery.store import list_requests
        from axon.discovery.models import RequestStatus

        config = agent.config
        matches = search_capabilities(
            query=args.strip(),
            enabled_plugins=config.plugins.enabled if config.plugins else [],
            enabled_skills=config.skills.enabled if config.skills else [],
            enabled_integrations=config.integrations.enabled if config.integrations else [],
        )

        lines: list[str] = []
        if matches:
            lines.append(f"Capabilities matching '{args.strip()}' ({len(matches)} results):\n")
            for m in matches:
                status = "ENABLED" if m.is_enabled else "available"
                creds = " [needs credentials]" if m.requires_credentials else ""
                sandbox = f" [sandbox: {m.sandbox_type}]" if m.sandbox_type else ""
                lines.append(f"  [{m.type.value:11s}] {m.name:30s} ({status}){creds}{sandbox}")
                if m.description:
                    lines.append(f"               {m.description[:80]}")
        else:
            lines.append(f"No capabilities found matching '{args.strip()}'.")
            lines.append("The agent can use plugins_request to submit a gap request.")

        # Show pending requests for this agent
        org_id = getattr(agent, "_org_id", "")
        if org_id:
            pending = list_requests(org_id, status=RequestStatus.PENDING, agent_id=agent.id)
            if pending:
                lines.append(f"\nPending requests from this agent ({len(pending)}):")
                for r in pending[:5]:
                    label = r.capability_name or r.description[:50]
                    gap = " [GAP]" if r.is_gap else ""
                    lines.append(f"  {r.id}: {label}{gap}")

        await _send_result(ws, agent.id, "discover", "\n".join(lines))
    except Exception as e:
        logger.error("Slash /discover failed: %s", e, exc_info=True)
        await _send_result(ws, agent.id, "discover", f"Discovery failed: {e}", success=False)


# ── Handler map ──────────────────────────────────────────────────

_HANDLERS: dict[str, Callable[..., Awaitable[None]]] = {
    "sleep": _cmd_sleep,
    "remember": _cmd_remember,
    "forget": _cmd_forget,
    "recall": _cmd_recall,
    "tasks": _cmd_tasks,
    "status": _cmd_status,
    "discover": _cmd_discover,
}

"""Scheduler job handlers — domain logic for scheduled agent work.

Contains all the "what to do" methods extracted from the scheduler.
The scheduler orchestration ("when to fire") lives in scheduler.py.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from axon.logging import get_logger

if TYPE_CHECKING:
    from axon.agents.agent import Agent

logger = get_logger(__name__)

# Max time (seconds) for a single scheduler-triggered agent.process() call
TASK_TIMEOUT = 300  # 5 minutes

# Built-in action prompts — what the agent "hears" when a check fires
ACTION_PROMPTS = {
    "work_on_tasks": (
        "[SYSTEM] You have an in_progress task to complete. Here are the details:\n\n"
        "{task_details}\n\n"
        "Execute the work described in the task:\n"
        "1. Do the research, analysis, or work described — be thorough and substantive\n"
        "2. Write your findings to the vault using memory_write — this is the primary deliverable. "
        "Create a well-structured document with clear sections, specific details, data points, "
        "and actionable insights. The vault document IS the work product.\n"
        "3. Provide a brief conversational summary to the user highlighting key findings "
        "and linking to the vault document\n"
        "4. Update the task status to 'done' via task_update with the exact path and a message summarizing what you accomplished\n"
        "The vault document should be comprehensive enough that someone reading it "
        "gets real value without needing to ask follow-up questions."
    ),
    "review_knowledge": (
        "[SYSTEM] A team member has shared knowledge for your review.\n\n"
        "{task_details}\n\n"
        "Review the shared knowledge document:\n"
        "1. Read the knowledge document from the shared vault using the path in the task\n"
        "2. Extract insights that are specifically relevant to YOUR domain and expertise\n"
        "3. Save your key takeaways to your own vault under learnings/ using memory_write — "
        "focus on what matters for your role, not a generic summary\n"
        "4. If you spot concerns, gaps, or conflicts with your existing knowledge, note them\n"
        "5. Update the task status to 'done' via task_update with the exact path and a message summarizing what you learned\n"
        "Be selective — only save what genuinely informs your future advice."
    ),
}

DEFAULT_PROMPT = (
    "[SYSTEM] Execute your scheduled proactive check: {action}\n"
    "Description: {description}"
)


async def consume_stream(
    agent: "Agent", prompt: str, *, save_history: bool = False,
) -> str:
    """Consume an agent.process() stream, returning the full text."""
    response_text = ""
    async for chunk in agent.process(prompt, save_history=save_history):
        if chunk.type == "text":
            response_text += chunk.content
    return response_text


async def fire_proactive_check(
    org_id: str,
    agent_id: str,
    agent: "Agent",
    action: str,
    description: str,
) -> None:
    """Fire a generic proactive check (not task work or memory consolidation)."""
    log = logger.bind(org_id=org_id, agent_id=agent_id, action=action)
    log.info("proactive_check_firing")

    prompt = ACTION_PROMPTS.get(
        action,
        DEFAULT_PROMPT.format(action=action, description=description),
    )

    try:
        response_text = await asyncio.wait_for(
            consume_stream(agent, prompt, save_history=False),
            timeout=TASK_TIMEOUT,
        )
        log.info("proactive_check_complete", response_chars=len(response_text))
    except asyncio.TimeoutError:
        log.error("proactive_check_timeout", timeout=TASK_TIMEOUT)
    except Exception as e:
        log.error("proactive_check_failed", error=str(e))


async def fire_memory_consolidation(
    org_id: str,
    agent_id: str,
    agent: "Agent",
) -> None:
    """Run LLM-driven memory consolidation directly (bypasses agent.process)."""
    if not hasattr(agent, "memory_manager") or not agent.memory_manager:
        return

    log = logger.bind(org_id=org_id, agent_id=agent_id)
    log.info("memory_consolidation_firing")

    try:
        await asyncio.wait_for(
            agent.memory_manager.deep_consolidate(),
            timeout=TASK_TIMEOUT,
        )
    except asyncio.TimeoutError:
        log.error("memory_consolidation_timeout", timeout=TASK_TIMEOUT)
    except Exception as e:
        log.error("memory_consolidation_failed", error=str(e))


async def fire_task_work(
    org_id: str,
    agent_id: str,
    agent: "Agent",
    in_flight_tasks: set[str],
) -> bool:
    """Find in_progress tasks for this agent and process them.

    Returns True if any tasks were found (regardless of success).
    """
    pending_tasks = find_agent_tasks(agent, agent_id)
    if not pending_tasks:
        return False

    log = logger.bind(org_id=org_id, agent_id=agent_id)
    log.info("task_work_start", task_count=len(pending_tasks))

    for task_meta in pending_tasks:
        task_path = task_meta["path"]
        task_title = task_meta.get("name", "Unknown task")
        conversation_id = task_meta["conversation_id"]
        ws_target = task_meta.get("ws_target", agent_id)
        is_external = (ws_target != agent_id)

        if task_path in in_flight_tasks:
            log.info("task_skipped_in_flight", task=task_title)
            continue

        log.info("task_processing", task=task_title, ws_target=ws_target)
        in_flight_tasks.add(task_path)

        # Build task-specific prompt
        prompt = _build_task_prompt(agent, agent_id, task_meta)

        try:
            if is_external:
                await process_external_task(
                    agent, agent_id, ws_target, conversation_id,
                    task_path, task_title, prompt,
                )
            else:
                await process_local_task(
                    agent, agent_id, conversation_id,
                    task_path, task_title, prompt,
                )
            auto_complete_task(agent, task_path, task_title)
        finally:
            in_flight_tasks.discard(task_path)

    return True


async def fire_review_done(
    org_id: str,
    agent_id: str,
    agent: "Agent",
) -> bool:
    """Check for tasks this agent created that are now done, wake agent to review.

    Returns True if any tasks were found for review.
    """
    shared_vault = agent.shared_vault
    if not shared_vault:
        return False

    tasks_dir = Path(shared_vault.vault_path) / "tasks"
    if not tasks_dir.exists():
        return False

    done_tasks = []
    for md_file in tasks_dir.glob("*.md"):
        if md_file.name.endswith("-index.md"):
            continue
        try:
            metadata, body = shared_vault.read_file(f"tasks/{md_file.name}")
            owner = metadata.get("owner", "") or metadata.get("created_by", "")
            status = metadata.get("status", "")
            if owner == agent_id and status == "done":
                done_tasks.append({
                    **metadata,
                    "path": f"tasks/{md_file.name}",
                    "body": body,
                })
        except Exception:
            continue

    if not done_tasks:
        return False

    log = logger.bind(org_id=org_id, agent_id=agent_id)
    log.info("review_done_start", task_count=len(done_tasks))

    task_summaries = []
    for t in done_tasks[:5]:
        responses = t.get("responses", [])
        last_response = responses[-1]["content"][:500] if responses else "No response recorded."
        task_summaries.append(
            f"- **{t.get('name', '?')}** (`{t['path']}`)\n"
            f"  Assignee: {t.get('assignee', '?')}\n"
            f"  Latest response: {last_response}"
        )

    prompt = (
        "[SYSTEM] The following tasks you created have been marked as done and need your review.\n\n"
        + "\n".join(task_summaries) + "\n\n"
        "For each task:\n"
        "1. Review the work and responses\n"
        "2. If satisfied, update the task status to 'accepted' via task_update with a message confirming acceptance\n"
        "3. If more work is needed, add a response via task_respond explaining what's missing, "
        "then set the status back to 'in_progress' or 'pending' via task_update with a message\n"
    )

    try:
        await asyncio.wait_for(
            consume_stream(agent, prompt, save_history=False),
            timeout=TASK_TIMEOUT,
        )
    except asyncio.TimeoutError:
        log.error("review_done_timeout")
    except Exception as e:
        log.error("review_done_failed", error=str(e))
    return True


# ── Task processing ─────────────────────────────────────────────


async def process_local_task(
    agent: "Agent",
    agent_id: str,
    conversation_id: str,
    task_path: str,
    task_title: str,
    prompt: str,
) -> None:
    """Process a task on the agent's own conversation (direct chat)."""
    import axon.ws_registry as ws_registry

    if hasattr(agent, "_processing_lock") and agent._processing_lock.locked():
        logger.info("task_deferred_busy", agent_id=agent_id, task=task_title)
        return

    original_conv_id = agent.conversation_manager.active_id
    switched = False

    try:
        if conversation_id != original_conv_id:
            agent.conversation_manager.switch(conversation_id)
            switched = True

        await ws_registry.push(agent_id, conversation_id, {
            "type": "task_update",
            "agent_id": agent_id,
            "task_path": task_path,
            "task_title": task_title,
            "status": "in_progress",
        })

        await ws_registry.push(agent_id, conversation_id, {
            "type": "thinking",
            "agent_id": agent_id,
            "content": "",
            "task_path": task_path,
        })

        async def _stream_task() -> str:
            text = ""
            async for chunk in agent.process(prompt, save_history=False):
                msg = {
                    "type": chunk.type,
                    "agent_id": chunk.agent_id,
                    "content": chunk.content,
                    "task_path": task_path,
                }
                if chunk.metadata:
                    msg["metadata"] = chunk.metadata
                await ws_registry.push(agent_id, conversation_id, msg)
                if chunk.type == "text":
                    text += chunk.content
            return text

        response_text = await asyncio.wait_for(
            _stream_task(), timeout=TASK_TIMEOUT,
        )

        if response_text:
            agent.conversation.add_assistant_message(
                response_text, agent_id=agent_id,
            )

        save_task_response(agent, agent_id, task_path, response_text)

        await ws_registry.push(agent_id, conversation_id, {
            "type": "task_update",
            "agent_id": agent_id,
            "task_path": task_path,
            "task_title": task_title,
            "status": "done",
        })

        sent = await ws_registry.push(agent_id, conversation_id, {
            "type": "agent_result",
            "agent_id": agent_id,
            "content": response_text[:500] if response_text else "",
            "metadata": {
                "source_agent": agent_id,
                "task_summary": task_title,
                "task_path": task_path,
                "status": "success",
            },
        })

        if sent == 0:
            from axon.push import fire_push_notification
            fire_push_notification(
                "task_done",
                agent_id=agent_id,
                agent_name=getattr(agent, "name", agent_id),
                task_title=task_title,
                org_id="",
            )

        agent.conversation.add_system_message(
            task_title,
            metadata={
                "type": "agent_result",
                "source_agent": agent_id,
                "task_summary": task_title,
                "status": "success",
            },
        )

        logger.info(
            "task_complete", agent_id=agent_id,
            task=task_title, response_chars=len(response_text),
        )

    except asyncio.TimeoutError:
        logger.error("task_timeout", agent_id=agent_id, task=task_title, timeout=TASK_TIMEOUT)
        save_task_response(
            agent, agent_id, task_path,
            f"Task timed out after {TASK_TIMEOUT}s", status="blocked",
        )
        sent = await ws_registry.push(agent_id, conversation_id, {
            "type": "task_update",
            "agent_id": agent_id,
            "task_path": task_path,
            "task_title": task_title,
            "status": "blocked",
        })
        if sent == 0:
            from axon.push import fire_push_notification
            fire_push_notification(
                "task_failed",
                agent_id=agent_id,
                agent_name=getattr(agent, "name", agent_id),
                task_title=task_title,
            )
    except Exception as e:
        logger.error("task_failed", agent_id=agent_id, task=task_title, error=str(e))
        save_task_response(
            agent, agent_id, task_path,
            f"Task failed: {e}", status="blocked",
        )
        sent = await ws_registry.push(agent_id, conversation_id, {
            "type": "task_update",
            "agent_id": agent_id,
            "task_path": task_path,
            "task_title": task_title,
            "status": "blocked",
        })
        if sent == 0:
            from axon.push import fire_push_notification
            fire_push_notification(
                "task_failed",
                agent_id=agent_id,
                agent_name=getattr(agent, "name", agent_id),
                task_title=task_title,
            )
    finally:
        if switched:
            try:
                agent.conversation_manager.switch(original_conv_id)
            except ValueError:
                pass


async def process_external_task(
    agent: "Agent",
    agent_id: str,
    ws_target: str,
    conversation_id: str,
    task_path: str,
    task_title: str,
    prompt: str,
) -> None:
    """Process a task that originated elsewhere (e.g., huddle)."""
    import axon.ws_registry as ws_registry

    if hasattr(agent, "_processing_lock") and agent._processing_lock.locked():
        logger.info("external_task_deferred_busy", agent_id=agent_id, task=task_title)
        return

    try:
        await ws_registry.push(ws_target, conversation_id, {
            "type": "task_update",
            "agent_id": agent_id,
            "task_path": task_path,
            "task_title": task_title,
            "status": "in_progress",
        })

        await ws_registry.push(ws_target, conversation_id, {
            "type": "thinking",
            "agent_id": agent_id,
            "content": "",
            "task_path": task_path,
        })

        async def _stream_external() -> str:
            text = ""
            async for chunk in agent.process(prompt, save_history=False):
                msg = {
                    "type": chunk.type,
                    "agent_id": chunk.agent_id,
                    "content": chunk.content,
                    "speaker": agent_id,
                    "task_path": task_path,
                }
                if chunk.metadata:
                    msg["metadata"] = chunk.metadata
                await ws_registry.push(ws_target, conversation_id, msg)
                if chunk.type == "text":
                    text += chunk.content
            return text

        response_text = await asyncio.wait_for(
            _stream_external(), timeout=TASK_TIMEOUT,
        )

        if response_text:
            _append_to_external_conversation(
                ws_target, conversation_id, response_text, agent_id,
            )

        save_task_response(agent, agent_id, task_path, response_text)

        await ws_registry.push(ws_target, conversation_id, {
            "type": "task_update",
            "agent_id": agent_id,
            "task_path": task_path,
            "task_title": task_title,
            "status": "done",
        })

        sent = await ws_registry.push(ws_target, conversation_id, {
            "type": "agent_result",
            "agent_id": agent_id,
            "content": response_text[:500] if response_text else "",
            "metadata": {
                "source_agent": agent_id,
                "task_summary": task_title,
                "task_path": task_path,
                "status": "success",
            },
        })

        if sent == 0:
            from axon.push import fire_push_notification
            fire_push_notification(
                "task_done",
                agent_id=agent_id,
                agent_name=getattr(agent, "name", agent_id),
                task_title=task_title,
            )

        # Inject result into delegator's conversation history
        if ws_target:
            import axon.registry as _reg
            delegator = None
            for _oid, _org in _reg.org_registry.items():
                if ws_target in _org.agent_registry:
                    delegator = _org.agent_registry[ws_target]
                    break
            if delegator and hasattr(delegator, "conversation"):
                delegator.conversation.add_system_message(
                    task_title,
                    metadata={
                        "type": "agent_result",
                        "source_agent": agent_id,
                        "task_summary": task_title,
                        "status": "success",
                    },
                )

        logger.info(
            "external_task_complete", agent_id=agent_id,
            task=task_title, ws_target=ws_target, response_chars=len(response_text),
        )

    except asyncio.TimeoutError:
        logger.error("external_task_timeout", agent_id=agent_id, task=task_title, timeout=TASK_TIMEOUT)
        save_task_response(
            agent, agent_id, task_path,
            f"Task timed out after {TASK_TIMEOUT}s", status="blocked",
        )
        sent = await ws_registry.push(ws_target, conversation_id, {
            "type": "task_update",
            "agent_id": agent_id,
            "task_path": task_path,
            "task_title": task_title,
            "status": "blocked",
        })
        if sent == 0:
            from axon.push import fire_push_notification
            fire_push_notification(
                "task_failed",
                agent_id=agent_id,
                agent_name=getattr(agent, "name", agent_id),
                task_title=task_title,
            )
    except Exception as e:
        logger.error("external_task_failed", agent_id=agent_id, task=task_title, error=str(e))
        save_task_response(
            agent, agent_id, task_path,
            f"Task failed: {e}", status="blocked",
        )
        sent = await ws_registry.push(ws_target, conversation_id, {
            "type": "task_update",
            "agent_id": agent_id,
            "task_path": task_path,
            "task_title": task_title,
            "status": "blocked",
        })
        if sent == 0:
            from axon.push import fire_push_notification
            fire_push_notification(
                "task_failed",
                agent_id=agent_id,
                agent_name=getattr(agent, "name", agent_id),
                task_title=task_title,
            )


# ── Helpers ─────────────────────────────────────────────────────


def _build_task_prompt(agent: "Agent", agent_id: str, task_meta: dict) -> str:
    """Build the system prompt for a task, including response thread."""
    task_title = task_meta.get("name", "Unknown task")
    task_path = task_meta["path"]
    task_details = (
        f"**Task:** {task_title}\n"
        f"**Path:** {task_path}\n"
        f"**Owner:** {task_meta.get('owner', 'unknown')}\n"
        f"**Description:**\n{task_meta.get('body', 'No description')}"
    )
    responses = task_meta.get("responses", [])
    if responses:
        task_details += "\n\n**Thread:**"
        for resp in responses:
            from_agent = resp.get("from", "unknown")
            ts = resp.get("timestamp", "")
            task_details += f"\n---\n**{from_agent}** ({ts}):\n{resp.get('content', '')}"
            for att in resp.get("attachments", []):
                task_details += f"\n  - [{att.get('label', 'attachment')}] → {att.get('path', '')}"

    task_labels = task_meta.get("labels", [])
    if isinstance(task_labels, str):
        task_labels = [l.strip() for l in task_labels.split(",")]
    action_key = (
        "review_knowledge" if "knowledge-review" in task_labels
        else "work_on_tasks"
    )
    prompt = ACTION_PROMPTS[action_key].format(task_details=task_details)

    delegates = agent.config.delegation.can_delegate_to if hasattr(agent, "config") else []
    if delegates and action_key == "work_on_tasks":
        names = ", ".join(delegates)
        prompt += (
            f"\n\n**IMPORTANT — Delegation:** You can delegate work to: {names}. "
            f"If this task involves code implementation, code changes, or technical "
            f"execution, use `delegate_task` to assign the work to the appropriate "
            f"agent rather than doing it yourself. Provide clear, detailed instructions "
            f"including file paths, expected behavior, and acceptance criteria."
        )

    return prompt


def save_task_response(
    agent: "Agent",
    agent_id: str,
    task_path: str,
    response_text: str,
    status: str = "success",
) -> None:
    """Write the agent's response to the task's responses[] array in the vault."""
    shared_vault = agent.shared_vault
    if not shared_vault or not response_text:
        return
    try:
        metadata, body = shared_vault.read_file(task_path)
        if "responses" not in metadata:
            metadata["responses"] = []
        metadata["responses"].append({
            "from": agent_id,
            "content": response_text,
            "attachments": [],
            "timestamp": datetime.now().isoformat() + "Z",
            "status": status,
        })
        metadata["updated_at"] = datetime.now().isoformat() + "Z"
        shared_vault.write_file(task_path, metadata, body)
        logger.info(
            "task_response_saved", agent_id=agent_id,
            task_path=task_path, response_chars=len(response_text),
        )
    except Exception as e:
        logger.warning(
            "task_response_save_failed",
            task_path=task_path, error=str(e),
        )


def auto_complete_task(agent: "Agent", task_path: str, task_title: str) -> None:
    """Auto-mark a task as done if the agent didn't do it during processing."""
    shared_vault = agent.shared_vault
    if not shared_vault:
        return
    try:
        metadata, body = shared_vault.read_file(task_path)
        if metadata.get("status") in ("pending", "in_progress"):
            metadata["status"] = "done"
            metadata["updated_at"] = datetime.now().isoformat() + "Z"
            shared_vault.write_file(task_path, metadata, body)
            logger.info("task_auto_completed", task=task_title, path=task_path)
    except Exception as e:
        logger.warning("task_auto_complete_failed", task=task_title, error=str(e))


def find_agent_tasks(agent: "Agent", agent_id: str) -> list[dict]:
    """Find actionable tasks assigned to this agent that have a conversation_id."""
    shared_vault = agent.shared_vault
    if not shared_vault:
        return []

    tasks_dir = Path(shared_vault.vault_path) / "tasks"
    if not tasks_dir.exists():
        return []

    results = []
    for md_file in tasks_dir.glob("*.md"):
        if md_file.name.endswith("-index.md"):
            continue
        try:
            metadata, body = shared_vault.read_file(f"tasks/{md_file.name}")
            assignee = metadata.get("assignee", "")
            status = metadata.get("status", "")
            conv_id = metadata.get("conversation_id", "")
            if status in ("done", "accepted", "blocked"):
                continue
            start_date = metadata.get("start_date", "")
            if start_date:
                today = datetime.now().strftime("%Y-%m-%d")
                if start_date > today:
                    continue

            if (
                assignee == agent_id
                and status in ("pending", "in_progress")
                and conv_id
            ):
                metadata["path"] = f"tasks/{md_file.name}"
                metadata["body"] = body
                results.append(metadata)
        except Exception as e:
            logger.warning("task_read_error", file=md_file.name, error=str(e))
            continue

    return results


def _append_to_external_conversation(
    ws_target: str,
    conversation_id: str,
    content: str,
    speaker_id: str,
) -> None:
    """Append a message to an external conversation's history file."""
    import axon.registry as registry

    if ws_target == "huddle":
        for org in registry.org_registry.values():
            if org.huddle:
                conv_mgr = org.huddle.conversation_manager
                break
        else:
            logger.warning("external_append_no_huddle")
            return
    else:
        logger.warning("external_append_unknown_target", ws_target=ws_target)
        return

    original_id = conv_mgr.active_id
    switched = False
    try:
        if conversation_id != original_id:
            conv_mgr.switch(conversation_id)
            switched = True
        conv_mgr.active.add_assistant_message(content, agent_id=speaker_id)
    except ValueError:
        logger.warning("external_append_failed", conversation_id=conversation_id)
    finally:
        if switched:
            try:
                conv_mgr.switch(original_id)
            except ValueError:
                pass

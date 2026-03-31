"""AgentScheduler — background heartbeat for proactive agent behaviors.

Wakes agents on their configured intervals (hourly/daily/weekly) to
execute proactive checks like processing assigned tasks.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from axon.agents.agent import Agent

logger = logging.getLogger(__name__)

# How often the scheduler loop ticks (seconds)
TICK_INTERVAL = 60

# Max time (seconds) for a single scheduler-triggered agent.process() call
TASK_TIMEOUT = 300  # 5 minutes

# Interval durations
INTERVAL_SECONDS = {
    "frequent": 120,
    "hourly": 3600,
    "daily": 86400,
    "weekly": 604800,
}

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


def _make_system_message(content: str) -> "Message":
    """Create a system message for conversation history injection."""
    from axon.agents.conversation import Message
    return Message(role="system", content=content)


class AgentScheduler:
    """Background loop that fires proactive checks for all agents."""

    def __init__(self) -> None:
        self._last_run: dict[str, datetime] = {}  # "org:agent:action" → last fire time
        self._task: asyncio.Task | None = None
        self._in_flight_tasks: set[str] = set()  # task paths currently being processed

    def start(self) -> None:
        """Start the scheduler as a background asyncio task."""
        if self._task and not self._task.done():
            return
        self._task = asyncio.create_task(self._loop())
        logger.info("[SCHEDULER] Started — tick every %ds", TICK_INTERVAL)

    async def stop(self) -> None:
        """Cancel the scheduler."""
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("[SCHEDULER] Stopped")

    async def trigger_task_execution(self, org_id: str, agent_id: str) -> None:
        """Immediately trigger task execution for a specific agent.

        Called when a task is created/updated to in_progress so the agent
        starts working right away instead of waiting for the next scheduled tick.
        """
        import axon.registry as registry

        org = registry.org_registry.get(org_id)
        if not org:
            logger.warning("[SCHEDULER] trigger_task_execution: org %s not found", org_id)
            return

        agent = org.agent_registry.get(agent_id)
        if not agent:
            logger.warning("[SCHEDULER] trigger_task_execution: agent %s not found", agent_id)
            return

        key = f"{org_id}:{agent_id}:work_on_tasks"
        now = datetime.now()

        logger.info("[SCHEDULER] Immediate task trigger for %s/%s", org_id, agent_id)
        await self._fire_task_work(org_id, agent_id, agent, key, now)

    async def _loop(self) -> None:
        """Main scheduler loop — ticks every TICK_INTERVAL seconds."""
        import axon.registry as registry

        # Wait for startup to settle before first tick
        await asyncio.sleep(30)
        logger.info("[SCHEDULER] First tick starting")

        while True:
            try:
                now = datetime.now()
                org_count = len(registry.org_registry)
                logger.debug("[SCHEDULER] Tick — %d orgs", org_count)
                for org_id, org in registry.org_registry.items():
                    for agent_id, agent in org.agent_registry.items():
                        # Always check for in_progress tasks if agent has a shared vault
                        if agent.shared_vault:
                            key = f"{org_id}:{agent_id}:work_on_tasks"
                            last = self._last_run.get(key)
                            interval = INTERVAL_SECONDS["frequent"]
                            if not last or (now - last).total_seconds() >= interval:
                                fired = await self._fire_task_work(
                                    org_id, agent_id, agent, key, now,
                                )
                                if fired:
                                    await asyncio.sleep(5)

                        # Check for tasks this agent created that are now done
                        if agent.shared_vault:
                            key_review = f"{org_id}:{agent_id}:review_done"
                            last_review = self._last_run.get(key_review)
                            interval = INTERVAL_SECONDS["frequent"]
                            if not last_review or (now - last_review).total_seconds() >= interval:
                                fired = await self._fire_review_done(
                                    org_id, agent_id, agent, key_review, now,
                                )
                                if fired:
                                    await asyncio.sleep(5)

                        # Run any additional configured proactive checks
                        checks = agent.config.behavior.proactive_checks
                        for check in checks:
                            if check.action in ("work_on_tasks",):
                                continue  # Handled above
                            fired = await self._maybe_fire(
                                org_id, agent_id, agent, check, now,
                            )
                            if fired:
                                await asyncio.sleep(5)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error("[SCHEDULER] Tick error: %s", e, exc_info=True)

            await asyncio.sleep(TICK_INTERVAL)

    async def _maybe_fire(
        self,
        org_id: str,
        agent_id: str,
        agent: "Agent",
        check: "ProactiveCheck",
        now: datetime,
    ) -> bool:
        """Fire a proactive check if its interval has elapsed. Returns True if fired."""
        key = f"{org_id}:{agent_id}:{check.action}"
        interval = INTERVAL_SECONDS.get(check.trigger, INTERVAL_SECONDS["daily"])
        last = self._last_run.get(key)

        if last and (now - last).total_seconds() < interval:
            return False  # Not time yet

        # work_on_tasks is special — only fire if there are pending tasks
        if check.action == "work_on_tasks":
            return await self._fire_task_work(org_id, agent_id, agent, key, now)

        # consolidate_memory bypasses agent.process() — calls memory manager directly
        if check.action == "consolidate_memory":
            return await self._fire_memory_consolidation(org_id, agent_id, agent, key, now)

        logger.info(
            "[SCHEDULER] Firing %s for %s/%s",
            check.action, org_id, agent_id,
        )
        self._last_run[key] = now

        # Build the prompt for this action
        prompt = ACTION_PROMPTS.get(
            check.action,
            DEFAULT_PROMPT.format(action=check.action, description=check.description),
        )

        try:
            response_text = await asyncio.wait_for(
                self._consume_stream(agent, prompt, save_history=False),
                timeout=TASK_TIMEOUT,
            )
            logger.info(
                "[SCHEDULER] %s/%s:%s complete — %d chars response",
                org_id, agent_id, check.action, len(response_text),
            )
        except asyncio.TimeoutError:
            logger.error(
                "[SCHEDULER] %s/%s:%s timed out after %ds",
                org_id, agent_id, check.action, TASK_TIMEOUT,
            )
        except Exception as e:
            logger.error(
                "[SCHEDULER] %s/%s:%s failed: %s",
                org_id, agent_id, check.action, e,
            )
        return True

    @staticmethod
    async def _consume_stream(
        agent: "Agent", prompt: str, *, save_history: bool = False,
    ) -> str:
        """Consume an agent.process() stream, returning the full text."""
        response_text = ""
        async for chunk in agent.process(prompt, save_history=save_history):
            if chunk.type == "text":
                response_text += chunk.content
        return response_text

    async def _fire_memory_consolidation(
        self,
        org_id: str,
        agent_id: str,
        agent: "Agent",
        key: str,
        now: datetime,
    ) -> bool:
        """Run LLM-driven memory consolidation directly (bypasses agent.process)."""
        if not hasattr(agent, "memory_manager") or not agent.memory_manager:
            return False

        logger.info("[SCHEDULER] Firing memory consolidation for %s/%s", org_id, agent_id)
        self._last_run[key] = now

        try:
            await asyncio.wait_for(
                agent.memory_manager.deep_consolidate(),
                timeout=TASK_TIMEOUT,
            )
        except asyncio.TimeoutError:
            logger.error(
                "[SCHEDULER] Memory consolidation timed out for %s/%s after %ds",
                org_id, agent_id, TASK_TIMEOUT,
            )
        except Exception as e:
            logger.error(
                "[SCHEDULER] Memory consolidation failed for %s/%s: %s",
                org_id, agent_id, e,
            )
        return True

    async def _fire_task_work(
        self,
        org_id: str,
        agent_id: str,
        agent: "Agent",
        key: str,
        now: datetime,
    ) -> bool:
        """Find in_progress tasks for this agent and process them on the correct conversation."""
        import axon.ws_registry as ws_registry

        # Find in_progress tasks assigned to this agent with a conversation_id
        pending_tasks = self._find_agent_tasks(agent, agent_id)
        if not pending_tasks:
            return False  # Nothing to do — don't update last_run

        logger.info(
            "[SCHEDULER] work_on_tasks for %s/%s — %d tasks",
            org_id, agent_id, len(pending_tasks),
        )

        for task_meta in pending_tasks:
            task_path = task_meta["path"]
            task_title = task_meta.get("name", "Unknown task")
            conversation_id = task_meta["conversation_id"]
            ws_target = task_meta.get("ws_target", agent_id)
            is_external = (ws_target != agent_id)

            # Skip tasks already being processed
            if task_path in self._in_flight_tasks:
                logger.info(
                    "[SCHEDULER] Task '%s' already in-flight — skipping",
                    task_title,
                )
                continue

            logger.info(
                "[SCHEDULER] Processing task '%s' → %s/%s",
                task_title, ws_target, conversation_id,
            )

            self._in_flight_tasks.add(task_path)

            # Build task-specific prompt (including response thread)
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

            # If agent can delegate, append delegation instructions
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

            try:
                if is_external:
                    # Huddle-originated task: process standalone, push to ws_target
                    await self._process_external_task(
                        agent, agent_id, ws_target, conversation_id,
                        task_path, task_title, prompt,
                    )
                else:
                    # Direct chat task: switch conversation, save history
                    await self._process_local_task(
                        agent, agent_id, conversation_id,
                        task_path, task_title, prompt,
                    )

                # Auto-complete: if agent didn't mark the task done, do it now
                self._auto_complete_task(agent, task_path, task_title)
            finally:
                self._in_flight_tasks.discard(task_path)

        # Only mark as run after all tasks processed successfully
        self._last_run[key] = now
        return True

    async def _fire_review_done(
        self,
        org_id: str,
        agent_id: str,
        agent: "Agent",
        key: str,
        now: datetime,
    ) -> bool:
        """Check for tasks this agent created/owns that are now in 'done' status, and wake agent to review."""
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

        logger.info(
            "[SCHEDULER] review_done for %s/%s — %d tasks to review",
            org_id, agent_id, len(done_tasks),
        )
        self._last_run[key] = now

        # Build review prompt
        task_summaries = []
        for t in done_tasks[:5]:  # Cap at 5 per cycle
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
                self._consume_stream(agent, prompt, save_history=False),
                timeout=TASK_TIMEOUT,
            )
        except asyncio.TimeoutError:
            logger.error("[SCHEDULER] review_done timed out for %s/%s", org_id, agent_id)
        except Exception as e:
            logger.error("[SCHEDULER] review_done failed for %s/%s: %s", org_id, agent_id, e)
        return True

    async def _process_local_task(
        self,
        agent: "Agent",
        agent_id: str,
        conversation_id: str,
        task_path: str,
        task_title: str,
        prompt: str,
    ) -> None:
        """Process a task on the agent's own conversation (direct chat)."""
        import axon.ws_registry as ws_registry

        # Skip if agent is already processing (e.g. user is chatting)
        if hasattr(agent, "_processing_lock") and agent._processing_lock.locked():
            logger.info(
                "[SCHEDULER] Agent %s is busy — deferring task '%s'",
                agent_id, task_title,
            )
            return  # Don't mark done — scheduler will retry next tick

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

            response_text = ""

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

            # Save only the agent's response to history (not the [SYSTEM] prompt)
            if response_text:
                agent.conversation.add_assistant_message(
                    response_text, agent_id=agent_id,
                )

            # Persist agent response to the task's response thread in the vault
            self._save_task_response(agent, agent_id, task_path, response_text)

            await ws_registry.push(agent_id, conversation_id, {
                "type": "task_update",
                "agent_id": agent_id,
                "task_path": task_path,
                "task_title": task_title,
                "status": "done",
            })

            # Emit agent_result so the frontend can show completion inline
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

            # No browser tab open — send push notification
            if sent == 0:
                from axon.push import fire_push_notification
                fire_push_notification(
                    "task_done",
                    agent_id=agent_id,
                    agent_name=getattr(agent, "name", agent_id),
                    task_title=task_title,
                    org_id="",
                )

            # Persist the agent_result as a system message so it survives refresh
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
                "[SCHEDULER] Task '%s' complete — %d chars",
                task_title, len(response_text),
            )

        except asyncio.TimeoutError:
            logger.error(
                "[SCHEDULER] Task '%s' timed out after %ds",
                task_title, TASK_TIMEOUT,
            )
            self._save_task_response(
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
            logger.error("[SCHEDULER] Task '%s' failed: %s", task_title, e)
            self._save_task_response(
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

    async def _process_external_task(
        self,
        agent: "Agent",
        agent_id: str,
        ws_target: str,
        conversation_id: str,
        task_path: str,
        task_title: str,
        prompt: str,
    ) -> None:
        """Process a task that originated elsewhere (e.g., huddle).

        Does NOT switch the agent's conversation. Pushes results to ws_target
        and appends to the source conversation's history file.
        """
        import axon.ws_registry as ws_registry

        # Skip if agent is already processing
        if hasattr(agent, "_processing_lock") and agent._processing_lock.locked():
            logger.info(
                "[SCHEDULER] Agent %s is busy — deferring external task '%s'",
                agent_id, task_title,
            )
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

            # Append result to the source conversation history
            if response_text:
                self._append_to_external_conversation(
                    ws_target, conversation_id, response_text, agent_id,
                )

            # Persist agent response to the task's response thread in the vault
            self._save_task_response(agent, agent_id, task_path, response_text)

            await ws_registry.push(ws_target, conversation_id, {
                "type": "task_update",
                "agent_id": agent_id,
                "task_path": task_path,
                "task_title": task_title,
                "status": "done",
            })

            # Emit agent_result so the delegating agent's conversation gets the output
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

            # Inject result into the delegating agent's conversation history
            if ws_target:
                import axon.registry as _reg
                # Find delegator in any org — try each until found
                delegator = None
                for _oid, _org in _reg.org_registry.items():
                    if ws_target in _org.agent_registry:
                        delegator = _org.agent_registry[ws_target]
                        break
                if delegator and hasattr(delegator, "conversation"):
                    # Persist as activity badge so it renders on refresh
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
                "[SCHEDULER] External task '%s' → %s complete — %d chars",
                task_title, ws_target, len(response_text),
            )

        except asyncio.TimeoutError:
            logger.error(
                "[SCHEDULER] External task '%s' timed out after %ds",
                task_title, TASK_TIMEOUT,
            )
            self._save_task_response(
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
            logger.error("[SCHEDULER] External task '%s' failed: %s", task_title, e)
            self._save_task_response(
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

    @staticmethod
    def _append_to_external_conversation(
        ws_target: str,
        conversation_id: str,
        content: str,
        speaker_id: str,
    ) -> None:
        """Append a message to an external conversation's history file."""
        import axon.registry as registry
        from axon.agents.conversation import ConversationManager

        # Find the conversation manager for the target
        if ws_target == "huddle":
            for org in registry.org_registry.values():
                if org.huddle:
                    conv_mgr = org.huddle.conversation_manager
                    break
            else:
                logger.warning("No huddle found for external conversation append")
                return
        else:
            logger.warning("Unknown ws_target '%s' for external append", ws_target)
            return

        # Save to the conversation if it matches the active one
        original_id = conv_mgr.active_id
        switched = False
        try:
            if conversation_id != original_id:
                conv_mgr.switch(conversation_id)
                switched = True
            conv_mgr.active.add_assistant_message(content, agent_id=speaker_id)
        except ValueError:
            logger.warning("Could not append to conversation %s", conversation_id)
        finally:
            if switched:
                try:
                    conv_mgr.switch(original_id)
                except ValueError:
                    pass

    @staticmethod
    def _save_task_response(
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
                "[SCHEDULER] Saved response (%d chars) to task '%s'",
                len(response_text), task_path,
            )
        except Exception as e:
            logger.warning(
                "[SCHEDULER] Failed to save response to task '%s': %s",
                task_path, e,
            )

    @staticmethod
    def _auto_complete_task(agent: "Agent", task_path: str, task_title: str) -> None:
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
                logger.info(
                    "[SCHEDULER] Auto-completed task '%s' (%s)",
                    task_title, task_path,
                )
        except Exception as e:
            logger.warning(
                "[SCHEDULER] Failed to auto-complete task '%s': %s",
                task_title, e,
            )

    @staticmethod
    def _find_agent_tasks(agent: "Agent", agent_id: str) -> list[dict]:
        """Find actionable tasks assigned to this agent that have a conversation_id."""
        shared_vault = agent.shared_vault
        if not shared_vault:
            logger.debug("[SCHEDULER] %s has no shared_vault — skipping task scan", agent_id)
            return []

        tasks_dir = Path(shared_vault.vault_path) / "tasks"
        if not tasks_dir.exists():
            logger.debug("[SCHEDULER] Tasks dir does not exist: %s", tasks_dir)
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
                # Skip completed tasks early — no need to log or evaluate them
                if status in ("done", "accepted", "blocked"):
                    continue
                logger.debug(
                    "[SCHEDULER] Task %s: assignee=%r status=%r conv_id=%r (want agent=%r)",
                    md_file.name, assignee, status, bool(conv_id), agent_id,
                )
                # Skip tasks with a future start_date
                start_date = metadata.get("start_date", "")
                if start_date:
                    today = datetime.now().strftime("%Y-%m-%d")
                    if start_date > today:
                        logger.debug(
                            "[SCHEDULER] Task %s: start_date %s is in the future — skipping",
                            md_file.name, start_date,
                        )
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
                logger.warning("[SCHEDULER] Error reading task %s: %s", md_file.name, e)
                continue

        return results


# Singleton
scheduler = AgentScheduler()

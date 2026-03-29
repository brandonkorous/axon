"""Pipeline engine -- executes pipeline definitions step by step."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, AsyncIterator

from axon.pipelines.models import (
    AutoResolve,
    PipelineDefinition,
    PipelineRun,
    PipelineStep,
    PipelineStepType,
    StepResult,
)

if TYPE_CHECKING:
    from axon.agents.agent import Agent, StreamChunk
    from axon.org import OrgInstance

logger = logging.getLogger(__name__)


@dataclass
class PipelineEvent:
    """Events emitted during pipeline execution."""

    type: str  # step_start | step_complete | pipeline_complete | pipeline_failed | text
    step_id: str = ""
    agent_id: str = ""
    content: str = ""
    metadata: dict[str, Any] | None = None


class PipelineEngine:
    """Executes pipeline definitions against an org's agent registry."""

    def __init__(self, org: "OrgInstance"):
        self.org = org

    async def run(
        self, definition: PipelineDefinition, input_message: str,
    ) -> AsyncIterator[PipelineEvent]:
        """Execute a pipeline from start to finish, yielding events."""
        run = PipelineRun(
            pipeline_name=definition.name,
            input_message=input_message,
        )

        # Determine starting step
        initial_id = definition.initial_step or (
            definition.steps[0].id if definition.steps else ""
        )
        if not initial_id:
            yield PipelineEvent(type="pipeline_failed", content="No steps defined")
            return

        current_step_id = initial_id
        prior_context: dict[str, StepResult] = {}

        while current_step_id:
            step = definition.get_step(current_step_id)
            if not step:
                yield PipelineEvent(
                    type="pipeline_failed",
                    content=f"Step '{current_step_id}' not found",
                )
                run.status = "failed"
                return

            run.current_step = current_step_id
            yield PipelineEvent(
                type="step_start",
                step_id=step.id,
                agent_id=step.agent_id or ",".join(step.agent_ids),
            )

            # Execute step based on type
            result: StepResult
            next_override = ""

            if step.type == PipelineStepType.AGENT:
                result = await self._execute_agent_step(
                    step, input_message, prior_context,
                )
            elif step.type == PipelineStepType.PARALLEL:
                result = await self._execute_parallel_step(
                    step, input_message, prior_context,
                )
            elif step.type == PipelineStepType.SYNTHESIZE:
                result = await self._execute_synthesis_step(
                    step, input_message, prior_context,
                )
            elif step.type == PipelineStepType.CONDITIONAL:
                result, next_override = self._evaluate_condition(
                    step, prior_context,
                )
                if next_override:
                    current_step_id = next_override
                    continue
            else:
                result = StepResult(
                    step_id=step.id, status="failed",
                    content="Unknown step type",
                )

            prior_context[step.id] = result
            run.step_results[step.id] = result.model_dump()

            yield PipelineEvent(
                type="step_complete",
                step_id=step.id,
                agent_id=result.agent_id,
                content=result.content[:500],
                metadata={
                    "confidence": result.confidence,
                    "status": result.status,
                },
            )

            if result.status == "failed":
                run.status = "failed"
                yield PipelineEvent(
                    type="pipeline_failed",
                    content=f"Step '{step.id}' failed: {result.content[:200]}",
                )
                return

            # Move to next step
            current_step_id = step.next_step

        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc).isoformat()

        yield PipelineEvent(
            type="pipeline_complete",
            metadata={"run": run.model_dump()},
        )

    async def _execute_agent_step(
        self,
        step: PipelineStep,
        input_message: str,
        prior_context: dict[str, StepResult],
    ) -> StepResult:
        """Execute a single-agent step."""
        agent = self.org.agent_registry.get(step.agent_id)
        if not agent:
            return StepResult(
                step_id=step.id, agent_id=step.agent_id,
                status="failed",
                content=f"Agent '{step.agent_id}' not found",
            )

        prompt = self._build_step_prompt(input_message, prior_context)
        return await self._run_agent(agent, step.id, prompt)

    async def _execute_parallel_step(
        self,
        step: PipelineStep,
        input_message: str,
        prior_context: dict[str, StepResult],
    ) -> StepResult:
        """Execute multiple agents in parallel and merge results."""
        prompt = self._build_step_prompt(input_message, prior_context)

        tasks = []
        for agent_id in step.agent_ids:
            agent = self.org.agent_registry.get(agent_id)
            if agent:
                tasks.append(self._run_agent(agent, step.id, prompt))

        if not tasks:
            return StepResult(
                step_id=step.id, status="failed",
                content="No agents found for parallel step",
            )

        results = await asyncio.gather(*tasks, return_exceptions=True)
        valid_results = [
            r for r in results
            if isinstance(r, StepResult) and r.status == "completed"
        ]

        if not valid_results:
            return StepResult(
                step_id=step.id, status="failed",
                content="All parallel agents failed",
            )

        return self._resolve_parallel(step, valid_results)

    async def _execute_synthesis_step(
        self,
        step: PipelineStep,
        input_message: str,
        prior_context: dict[str, StepResult],
    ) -> StepResult:
        """Synthesize results from prior steps."""
        summaries = []
        for sid, result in prior_context.items():
            summaries.append(
                f"**Step {sid}** (confidence: {result.confidence}):\n"
                f"{result.content}"
            )

        synthesis_prompt = (
            "Synthesize the following analysis results into a unified "
            "recommendation.\n\n"
            f"Original question: {input_message}\n\n"
            + "\n\n---\n\n".join(summaries)
            + "\n\nProvide a clear, actionable synthesis."
        )

        # Use the orchestrator for synthesis, or fall back to first agent
        synth_agent = None
        for agent in self.org.agent_registry.values():
            from axon.config import AgentType
            if agent.config.type == AgentType.ORCHESTRATOR:
                synth_agent = agent
                break
        if not synth_agent:
            synth_agent = next(
                iter(self.org.agent_registry.values()), None,
            )

        if not synth_agent:
            return StepResult(
                step_id=step.id, status="failed",
                content="No agent for synthesis",
            )

        return await self._run_agent(synth_agent, step.id, synthesis_prompt)

    def _evaluate_condition(
        self,
        step: PipelineStep,
        prior_context: dict[str, StepResult],
    ) -> tuple[StepResult, str]:
        """Evaluate a conditional step and return next step override."""
        condition = step.condition
        parts = condition.split(".", 1) if "." in condition else [condition, ""]
        step_id = parts[0]
        field_name = parts[1] if len(parts) > 1 else ""

        prior = prior_context.get(step_id)
        if not prior or not prior.structured_data:
            return (
                StepResult(step_id=step.id, status="completed"),
                step.next_step,
            )

        value = str(prior.structured_data.get(field_name, "")).lower()
        next_step = step.branches.get(value, step.next_step)

        return (
            StepResult(
                step_id=step.id, status="completed",
                content=f"Condition: {value}",
            ),
            next_step,
        )

    def _build_step_prompt(
        self,
        input_message: str,
        prior_context: dict[str, StepResult],
    ) -> str:
        """Build the prompt for a step, injecting prior step results."""
        if not prior_context:
            return input_message

        context_parts = []
        for step_id, result in prior_context.items():
            context_parts.append(
                f"### Prior analysis -- {step_id}\n{result.content}"
            )

        return (
            f"## Original Question\n{input_message}\n\n"
            f"## Prior Analysis\n\n"
            + "\n\n".join(context_parts)
            + "\n\n## Your Task\n"
            "Review the prior analysis and provide your perspective. "
            "Build on what's been said -- add your domain expertise, "
            "challenge assumptions, and provide your recommendation."
        )

    async def _run_agent(
        self,
        agent: "Agent",
        step_id: str,
        prompt: str,
    ) -> StepResult:
        """Run an agent and collect its full response."""
        full_response = ""
        structured_data = None
        confidence = 0.5

        try:
            async for chunk in agent.process(prompt, save_history=False):
                if chunk.type == "text":
                    full_response += chunk.content
                elif (
                    chunk.type == "structured_output"
                    and chunk.metadata
                ):
                    structured_data = chunk.metadata.get("data")
                    confidence = chunk.metadata.get("confidence", 0.5)
        except Exception as e:
            return StepResult(
                step_id=step_id, agent_id=agent.id,
                status="failed", content=str(e),
            )

        return StepResult(
            step_id=step_id,
            agent_id=agent.id,
            content=full_response,
            structured_data=structured_data,
            confidence=confidence,
        )

    def _resolve_parallel(
        self, step: PipelineStep, results: list[StepResult],
    ) -> StepResult:
        """Resolve multiple parallel results into a single result."""
        if step.auto_resolve == AutoResolve.FIRST_RESPONSE:
            return results[0]

        if step.auto_resolve == AutoResolve.HIGHEST_CONFIDENCE:
            return max(results, key=lambda r: r.confidence)

        # CONSENSUS: merge all responses
        combined = "\n\n---\n\n".join(
            f"**{r.agent_id}** (confidence: {r.confidence}):\n{r.content}"
            for r in results
        )
        avg_confidence = sum(r.confidence for r in results) / len(results)
        return StepResult(
            step_id=step.id,
            agent_id=",".join(r.agent_id for r in results),
            content=combined,
            confidence=avg_confidence,
        )

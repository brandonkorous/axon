"""Pipeline models -- define sequential and parallel agent workflows."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid

from pydantic import BaseModel


class PipelineStepType(str, Enum):
    AGENT = "agent"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    SYNTHESIZE = "synthesize"


class AutoResolve(str, Enum):
    FIRST_RESPONSE = "first_response"
    CONSENSUS = "consensus"
    HIGHEST_CONFIDENCE = "highest_confidence"


class PipelineStep(BaseModel):
    """A single step in a pipeline."""

    id: str
    type: PipelineStepType = PipelineStepType.AGENT
    agent_id: str = ""  # for AGENT type
    agent_ids: list[str] = []  # for PARALLEL type
    condition: str = ""  # for CONDITIONAL: simple key=value match
    branches: dict[str, str] = {}  # condition_value -> next_step_id
    next_step: str = ""  # default next step (empty = end)
    auto_resolve: AutoResolve = AutoResolve.CONSENSUS
    timeout_seconds: int = 120
    output_schema: str = ""  # name of OutputSchema to enforce


class PipelineDefinition(BaseModel):
    """A complete pipeline workflow."""

    name: str
    description: str = ""
    version: str = "1.0"
    steps: list[PipelineStep] = []
    initial_step: str = ""  # defaults to first step's id

    def get_step(self, step_id: str) -> PipelineStep | None:
        for step in self.steps:
            if step.id == step_id:
                return step
        return None


class StepResult(BaseModel):
    """Result from executing a single pipeline step."""

    step_id: str
    agent_id: str = ""
    content: str = ""
    structured_data: dict[str, Any] | None = None
    confidence: float = 0.5
    status: str = "completed"  # completed | failed | timeout


class PipelineRun(BaseModel):
    """A single execution of a pipeline."""

    id: str = ""
    pipeline_name: str = ""
    status: str = "running"  # running | completed | failed | stalled
    current_step: str = ""
    step_results: dict[str, Any] = {}  # step_id -> StepResult dict
    started_at: str = ""
    completed_at: str = ""
    conversation_id: str = ""
    input_message: str = ""

    def model_post_init(self, __context: Any) -> None:
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if not self.started_at:
            self.started_at = datetime.now(timezone.utc).isoformat()

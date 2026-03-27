"""Research configuration — artifact types, depth levels, source limits."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ArtifactType(str, Enum):
    REPORT = "report"
    ANALYSIS = "analysis"
    BRIEF = "brief"
    COMPARISON = "comparison"


class ResearchDepth(str, Enum):
    QUICK = "quick"       # 2-3 sources, brief summary
    STANDARD = "standard"  # 5-8 sources, full report
    DEEP = "deep"          # 10+ sources, comprehensive analysis


class ResearchConfig(BaseModel):
    """Configuration for a research task."""

    topic: str = Field(description="Primary research topic or question")
    artifact_type: ArtifactType = Field(default=ArtifactType.REPORT)
    depth: ResearchDepth = Field(default=ResearchDepth.STANDARD)
    max_sources: int = Field(default=8, description="Maximum sources to consult")
    focus_areas: list[str] = Field(default_factory=list, description="Specific sub-topics")
    constraints: str = Field(default="", description="Any constraints or requirements")
    synthesize_locally: bool = Field(
        default=True,
        description="Use local LLM to compress sources before agent analysis",
    )
    synthesis_model: str = Field(
        default="ollama/llama3:8b",
        description="Local model for source compression",
    )


DEPTH_SOURCE_LIMITS: dict[ResearchDepth, int] = {
    ResearchDepth.QUICK: 3,
    ResearchDepth.STANDARD: 8,
    ResearchDepth.DEEP: 15,
}

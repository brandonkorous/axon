"""Media configuration — enabled providers and summary settings."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MediaConfig(BaseModel):
    """Configuration for media consumption tools."""

    enabled: bool = Field(default=False, description="Enable media tools for this agent")
    max_transcript_length: int = Field(default=10000, description="Max transcript chars to return")
    summary_length: int = Field(default=500, description="Target summary length in words")
    synthesize_locally: bool = Field(
        default=True,
        description="Use local LLM to compress transcripts before agent analysis",
    )
    synthesis_model: str = Field(
        default="ollama/llama3:8b",
        description="Local model for transcript compression",
    )

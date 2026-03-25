"""Reasoning engine configuration — canonical definition is in axon.config.

This module exists so that `from axon.reasoning.config import ReasoningConfig`
still works throughout the reasoning package without circular imports.
"""

from __future__ import annotations

from pydantic import BaseModel


class ReasoningConfig(BaseModel):
    """Structured reasoning engine configuration.

    When enabled, agents gain access to a reasoning graph that tracks
    claims, evidence, decisions, and their relationships — with full
    traceability for "why did we decide X?" queries.
    """

    enabled: bool = True
    model: str = ""  # empty → inherits from PersonaConfig.model.reasoning
    background_model: str = ""  # empty → inherits learning model (cheap local LLM)
    max_graph_nodes: int = 500
    auto_reason_threshold: str = "decision"  # "all" | "decision" | "never"
    persist_traces: bool = True
    max_evidence_per_claim: int = 20
    default_strategy: str = "weighted_evidence"
    trace_branch: str = "reasoning"

"""Reasoning engine — structured claim/evidence/decision graphs with traceability.

Imports are lazy to avoid circular dependency with axon.config → axon.agents.
"""

from __future__ import annotations


def __getattr__(name: str):
    """Lazy imports to break circular dependency chain."""
    if name == "ReasoningConfig":
        from axon.config import ReasoningConfig
        return ReasoningConfig
    if name == "ReasoningEngine":
        from axon.reasoning.engine import ReasoningEngine
        return ReasoningEngine
    if name == "ReasoningGraph":
        from axon.reasoning.graph import ReasoningGraph
        return ReasoningGraph
    if name in ("ReasoningNode", "ReasoningEdge", "DecisionTrace", "EvaluationResult", "NodeType", "EdgeType"):
        from axon.reasoning import models
        return getattr(models, name)
    if name == "REASONING_TOOLS":
        from axon.reasoning.tools import REASONING_TOOLS
        return REASONING_TOOLS
    if name == "ReasoningToolExecutor":
        from axon.reasoning.tools import ReasoningToolExecutor
        return ReasoningToolExecutor
    raise AttributeError(f"module 'axon.reasoning' has no attribute {name!r}")

"""Data models for the reasoning engine — claims, evidence, decisions, edges, traces."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """Types of nodes in the reasoning graph."""

    CLAIM = "claim"
    EVIDENCE = "evidence"
    DECISION = "decision"
    ASSUMPTION = "assumption"
    EUREKA = "eureka"  # first-principles insight that contradicts conventional wisdom


class EdgeType(str, Enum):
    """Types of relationships between reasoning nodes."""

    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    DEPENDS_ON = "depends_on"
    SUPERSEDES = "supersedes"


class ReasoningNode(BaseModel):
    """A node in the reasoning graph — a claim, piece of evidence, or decision."""

    id: str
    node_type: NodeType
    content: str
    confidence: float = 0.5
    source: str = ""  # vault path, conversation id, huddle id, or free text
    created_at: str = ""  # ISO timestamp
    tags: list[str] = []
    vault_path: str = ""  # where this node is persisted (if at all)


class ReasoningEdge(BaseModel):
    """A directed relationship between two reasoning nodes."""

    source_id: str
    target_id: str
    edge_type: EdgeType
    weight: float = 1.0
    reasoning: str = ""


class Alternative(BaseModel):
    """A considered option in a decision trace."""

    option: str
    score: float = 0.0
    reasoning: str = ""


class DecisionTrace(BaseModel):
    """A full record of a structured decision — question, evidence, conclusion."""

    id: str
    question: str
    strategy: str
    claims_considered: list[str] = []  # node IDs
    evidence_used: list[str] = []  # node IDs
    conclusion: str = ""
    confidence: float = 0.5
    alternatives: list[Alternative] = []
    created_at: str = ""
    agent_id: str = ""
    vault_path: str = ""


class EvaluationResult(BaseModel):
    """Result of evaluating a claim against evidence."""

    claim_id: str
    score: float = 0.5
    supporting_evidence: list[str] = []  # node IDs
    contradicting_evidence: list[str] = []  # node IDs
    reasoning: str = ""
    strategy: str = ""


class ContradictionPair(BaseModel):
    """Two nodes that contradict each other."""

    node_a_id: str
    node_b_id: str
    description: str = ""


# ── LLM response schemas (structured output the LLM is forced into) ──


class LLMEvaluationResponse(BaseModel):
    """Schema for LLM evaluation output."""

    score: float = Field(description="Confidence score 0.0-1.0")
    supporting: list[str] = Field(default=[], description="IDs of supporting evidence")
    contradicting: list[str] = Field(default=[], description="IDs of contradicting evidence")
    reasoning: str = Field(default="", description="Explanation of the evaluation")


class LLMDecisionResponse(BaseModel):
    """Schema for LLM decision output."""

    conclusion: str = Field(description="The chosen course of action")
    confidence: float = Field(description="Confidence score 0.0-1.0")
    alternatives: list[dict[str, Any]] = Field(
        default=[], description="List of {option, score, reasoning}"
    )
    reasoning: str = Field(default="", description="Explanation of the decision")
    claims: list[dict[str, Any]] = Field(
        default=[], description="Claims extracted: {content, confidence, type}"
    )


class LLMContradictionResponse(BaseModel):
    """Schema for LLM contradiction resolution output."""

    resolution: str = Field(description="The resolved position")
    confidence: float = Field(description="Confidence in the resolution")
    keep: str = Field(default="", description="Which node to keep: 'a', 'b', 'neither', or 'both'")
    reasoning: str = Field(default="", description="Explanation")


class LLMHuddleExtractionResponse(BaseModel):
    """Schema for extracting reasoning nodes from huddle transcripts."""

    claims: list[dict[str, Any]] = Field(
        default=[], description="Claims made: {content, confidence, source}"
    )
    evidence: list[dict[str, Any]] = Field(
        default=[], description="Evidence cited: {content, confidence, source}"
    )
    decisions: list[dict[str, Any]] = Field(
        default=[], description="Decisions reached: {question, conclusion, confidence}"
    )
    contradictions: list[dict[str, Any]] = Field(
        default=[], description="Contradictions found: {claim_a, claim_b, description}"
    )

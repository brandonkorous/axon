"""Reasoning strategies — prompt builders that shape how the LLM reasons.

Each strategy is a function that takes a question, evidence nodes, and
optional options, then returns a formatted prompt string. The LLM does
the actual reasoning; the strategy shapes the framing.
"""

from __future__ import annotations

from typing import Any, Callable

from axon.reasoning.models import ReasoningNode
from axon.reasoning.prompts import EVALUATE_CLAIM_PROMPT, MAKE_DECISION_PROMPT

StrategyFn = Callable[[str, list[ReasoningNode], list[str] | None], str]


def _format_evidence(nodes: list[ReasoningNode]) -> str:
    """Format evidence nodes into a readable block for prompts."""
    if not nodes:
        return "No evidence available."
    lines = []
    for node in nodes:
        conf_label = f"confidence: {node.confidence:.2f}"
        lines.append(f"- [{node.id}] ({node.node_type.value}, {conf_label}): {node.content}")
    return "\n".join(lines)


def _format_options(options: list[str] | None) -> str:
    """Format options into a numbered list."""
    if not options:
        return "No predefined options — generate the best options based on evidence."
    return "\n".join(f"{i+1}. {opt}" for i, opt in enumerate(options))


def build_weighted_evidence_prompt(
    question: str,
    evidence: list[ReasoningNode],
    options: list[str] | None = None,
) -> str:
    """Default strategy: weigh all evidence by confidence, score options."""
    prefix = (
        "Strategy: WEIGHTED EVIDENCE\n"
        "Weigh each piece of evidence by its confidence score. "
        "Higher-confidence evidence should carry more weight in your analysis. "
        "Low-confidence evidence (< 0.3) should be noted but not relied upon.\n\n"
    )
    return prefix + MAKE_DECISION_PROMPT.format(
        question=question,
        options=_format_options(options),
        evidence=_format_evidence(evidence),
    )


def build_adversarial_prompt(
    question: str,
    evidence: list[ReasoningNode],
    options: list[str] | None = None,
) -> str:
    """Devil's advocate: argue against the strongest position."""
    prefix = (
        "Strategy: ADVERSARIAL\n"
        "First, identify the strongest position based on the evidence. "
        "Then, argue AGAINST it as forcefully as possible. Find every weakness, "
        "assumption, and blind spot. Only after thoroughly attacking the leading "
        "option should you render your final judgment — which may or may not "
        "match the original strongest position.\n\n"
    )
    return prefix + MAKE_DECISION_PROMPT.format(
        question=question,
        options=_format_options(options),
        evidence=_format_evidence(evidence),
    )


def build_consensus_prompt(
    question: str,
    evidence: list[ReasoningNode],
    options: list[str] | None = None,
) -> str:
    """Consensus: find common ground across multiple positions."""
    prefix = (
        "Strategy: CONSENSUS\n"
        "The evidence comes from multiple sources that may disagree. "
        "Your job is to find the common ground — what do most sources agree on? "
        "Where they disagree, note the dissent but weight the majority position. "
        "Synthesize a conclusion that captures the shared truth.\n\n"
    )
    return prefix + MAKE_DECISION_PROMPT.format(
        question=question,
        options=_format_options(options),
        evidence=_format_evidence(evidence),
    )


def build_cost_benefit_prompt(
    question: str,
    evidence: list[ReasoningNode],
    options: list[str] | None = None,
) -> str:
    """Cost-benefit: structured upside/downside/probability for each option."""
    prefix = (
        "Strategy: COST-BENEFIT ANALYSIS\n"
        "For each option, analyze:\n"
        "1. Upside — what's the best case? How likely?\n"
        "2. Downside — what's the worst case? How likely?\n"
        "3. Expected value — probability-weighted outcome\n\n"
        "Score each option by expected value. The conclusion should pick "
        "the option with the highest expected value, accounting for risk tolerance.\n\n"
    )
    return prefix + MAKE_DECISION_PROMPT.format(
        question=question,
        options=_format_options(options),
        evidence=_format_evidence(evidence),
    )


def build_evaluation_prompt(
    claim: str,
    evidence: list[ReasoningNode],
) -> str:
    """Build an evaluation prompt for scoring a claim against evidence."""
    return EVALUATE_CLAIM_PROMPT.format(
        claim=claim,
        evidence=_format_evidence(evidence),
    )


def build_first_principles_prompt(
    question: str,
    evidence: list[ReasoningNode],
    options: list[str] | None = None,
) -> str:
    """First principles: three-layer epistemological analysis."""
    prefix = (
        "Strategy: FIRST PRINCIPLES (Three Layers of Knowledge)\n\n"
        "Analyze this question through three distinct layers:\n\n"
        "**Layer 1 — Tried and True:** What does conventional wisdom say? "
        "What are the standard patterns and established approaches? "
        "List them explicitly.\n\n"
        "**Layer 2 — New and Popular:** What are the current best practices? "
        "What's trending? What would a well-read practitioner recommend today? "
        "Note where Layer 2 updates or contradicts Layer 1.\n\n"
        "**Layer 3 — First Principles:** Forget Layers 1 and 2 entirely. "
        "If you were solving this problem for the first time with no prior art, "
        "no conventions, and no trends — just the raw constraints and goals — "
        "what would you do? Reason from fundamentals.\n\n"
        "**Eureka Check:** Does your Layer 3 conclusion contradict Layers 1 or 2? "
        "If yes, this is an EUREKA MOMENT — a first-principles insight that "
        "challenges conventional wisdom. Flag it prominently and explain why "
        "the conventional approach is wrong for THIS specific case.\n\n"
        "In your response JSON, include a `claims` entry with type 'eureka' "
        "for any Eureka Moments detected.\n\n"
    )
    return prefix + MAKE_DECISION_PROMPT.format(
        question=question,
        options=_format_options(options),
        evidence=_format_evidence(evidence),
    )


STRATEGIES: dict[str, StrategyFn] = {
    "weighted_evidence": build_weighted_evidence_prompt,
    "adversarial": build_adversarial_prompt,
    "consensus": build_consensus_prompt,
    "cost_benefit": build_cost_benefit_prompt,
    "first_principles": build_first_principles_prompt,
}

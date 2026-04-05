"""Reasoning tool definitions and executor for agent integration."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from axon.logging import get_logger

if TYPE_CHECKING:
    from axon.reasoning.engine import ReasoningEngine

logger = get_logger(__name__)


# ── Tool schemas (for LLM tool-use) ─────────────────────────────────

REASONING_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "reason_evaluate",
            "description": (
                "Evaluate a claim against evidence using structured reasoning. "
                "Returns a confidence score with full evidence chain. Use when you "
                "need to assess whether something is true, likely, or supported by evidence."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "claim": {
                        "type": "string",
                        "description": "The claim to evaluate (e.g., 'Usage-based pricing will increase revenue')",
                    },
                    "evidence_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Vault paths to evidence files (optional — auto-gathers if omitted)",
                    },
                    "strategy": {
                        "type": "string",
                        "enum": ["weighted_evidence", "adversarial", "consensus", "cost_benefit"],
                        "description": "Reasoning strategy to use (default: weighted_evidence)",
                    },
                },
                "required": ["claim"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reason_decide",
            "description": (
                "Make a structured decision with full trace. Gathers evidence, "
                "evaluates options, and records the decision with alternatives. "
                "Use for important decisions that need to be traceable and justified."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The decision question (e.g., 'Should we hire a marketing lead?')",
                    },
                    "options": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Options to consider (optional — generates options if omitted)",
                    },
                    "strategy": {
                        "type": "string",
                        "enum": ["weighted_evidence", "adversarial", "consensus", "cost_benefit"],
                        "description": "Reasoning strategy to use (default: weighted_evidence)",
                    },
                },
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reason_explain",
            "description": (
                "Explain why a decision was made. Traces back through the evidence "
                "and reasoning chain to produce a clear narrative."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What to explain (e.g., 'why did we choose usage-based pricing?')",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reason_contradictions",
            "description": (
                "Find contradictions in the reasoning graph. "
                "Optionally attempt to resolve them."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "resolve": {
                        "type": "boolean",
                        "description": "If true, attempt to resolve found contradictions",
                    },
                },
            },
        },
    },
]


# ── Tool executor ───────────────────────────────────────────────────

class ReasoningToolExecutor:
    """Executes reasoning tool calls from agent responses."""

    def __init__(self, engine: "ReasoningEngine"):
        self.engine = engine

    async def execute(self, tool_name: str, arguments: str) -> str:
        """Execute a reasoning tool call and return the result as a string."""
        try:
            args = json.loads(arguments)
        except json.JSONDecodeError:
            return f"Error: Invalid JSON arguments: {arguments}"

        handlers = {
            "reason_evaluate": self._evaluate,
            "reason_decide": self._decide,
            "reason_explain": self._explain,
            "reason_contradictions": self._contradictions,
        }

        handler = handlers.get(tool_name)
        if not handler:
            return f"Error: Unknown reasoning tool: {tool_name}"

        try:
            return await handler(args)
        except Exception as e:
            return f"Error in {tool_name}: {e}"

    async def _evaluate(self, args: dict) -> str:
        result = await self.engine.evaluate_claim(
            claim=args["claim"],
            evidence_paths=args.get("evidence_paths"),
            strategy=args.get("strategy", ""),
        )
        lines = [
            f"## Evaluation: {args['claim'][:80]}",
            f"**Score:** {result.score:.2f} / 1.0",
            f"**Strategy:** {result.strategy}",
            f"**Supporting evidence:** {len(result.supporting_evidence)} pieces",
            f"**Contradicting evidence:** {len(result.contradicting_evidence)} pieces",
            f"\n### Reasoning\n{result.reasoning}",
        ]
        return "\n".join(lines)

    async def _decide(self, args: dict) -> str:
        trace = await self.engine.make_decision(
            question=args["question"],
            options=args.get("options"),
            strategy=args.get("strategy", ""),
        )
        lines = [
            f"## Decision: {trace.question[:80]}",
            f"**Conclusion:** {trace.conclusion}",
            f"**Confidence:** {trace.confidence:.2f}",
            f"**Strategy:** {trace.strategy}",
            f"**Evidence considered:** {len(trace.evidence_used)} pieces",
        ]
        if trace.alternatives:
            lines.append("\n### Alternatives Considered")
            for alt in trace.alternatives:
                lines.append(f"- **{alt.option}** (score: {alt.score:.2f}): {alt.reasoning}")
        if trace.vault_path:
            lines.append(f"\n*Decision trace saved to: [[{trace.vault_path}]]*")
        return "\n".join(lines)

    async def _explain(self, args: dict) -> str:
        return await self.engine.explain_decision(args["query"])

    async def _contradictions(self, args: dict) -> str:
        pairs = self.engine.graph.find_contradictions()
        if not pairs:
            return "No contradictions found in the reasoning graph."

        lines = [f"## Found {len(pairs)} contradiction(s)\n"]
        for pair in pairs:
            node_a = self.engine.graph.get_node(pair.node_a_id)
            node_b = self.engine.graph.get_node(pair.node_b_id)
            a_content = node_a.content[:80] if node_a else pair.node_a_id
            b_content = node_b.content[:80] if node_b else pair.node_b_id
            lines.append(f"**{a_content}** vs **{b_content}**")
            if pair.description:
                lines.append(f"  {pair.description}")
            lines.append("")

        # Optionally resolve
        if args.get("resolve") and pairs:
            lines.append("### Resolution Attempts\n")
            for pair in pairs[:3]:  # cap at 3 resolutions per call
                resolution = await self.engine.resolve_contradiction(
                    pair.node_a_id, pair.node_b_id,
                )
                if resolution:
                    lines.append(f"- **Resolved:** {resolution.content[:100]} (conf: {resolution.confidence:.2f})")

        return "\n".join(lines)

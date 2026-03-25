"""Reasoning engine — orchestrates structured reasoning pipelines.

Sits between the vault (knowledge) and agents (action). Turns raw
knowledge into justified conclusions with full traceability.

Flow: trigger → gather → reason → record → act
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from axon.agents.provider import complete
from axon.reasoning.config import ReasoningConfig
from axon.reasoning.graph import ReasoningGraph
from axon.reasoning.models import (
    Alternative,
    DecisionTrace,
    EdgeType,
    EvaluationResult,
    NodeType,
    ReasoningEdge,
    ReasoningNode,
)
from axon.reasoning.prompts import (
    EXPLAIN_DECISION_PROMPT,
    EXTRACT_FROM_HUDDLE_PROMPT,
    GATHER_EVIDENCE_PROMPT,
    RESOLVE_CONTRADICTION_PROMPT,
)
from axon.reasoning.strategies import STRATEGIES, build_evaluation_prompt
from axon.vault.memory_prompts import parse_llm_json
from axon.vault.vault import VaultManager

if TYPE_CHECKING:
    from axon.usage import UsageTracker

logger = logging.getLogger(__name__)


class ReasoningEngine:
    """Orchestrates structured reasoning with graph persistence.

    Uses an expensive model for sync reasoning (agent waits for result)
    and a cheap background model for fire-and-forget operations.
    """

    def __init__(
        self,
        vault: VaultManager,
        config: ReasoningConfig,
        model: str,
        background_model: str = "",
        agent_id: str = "",
        usage_tracker: "UsageTracker | None" = None,
        org_id: str = "",
    ):
        self.vault = vault
        self.config = config
        self.model = model
        self.background_model = background_model or model
        self.agent_id = agent_id
        self._usage_tracker = usage_tracker
        self._org_id = org_id
        self.graph = ReasoningGraph(vault, config)

    # ── Core reasoning operations (sync — agent waits) ──────────

    async def evaluate_claim(
        self,
        claim: str,
        evidence_paths: list[str] | None = None,
        strategy: str = "",
    ) -> EvaluationResult:
        """Evaluate a claim against evidence. Returns structured result."""
        strategy = strategy or self.config.default_strategy

        # Gather evidence
        if evidence_paths:
            evidence_nodes = self._load_evidence_from_paths(evidence_paths)
        else:
            evidence_nodes = await self._gather_evidence(claim)

        # Build prompt and call LLM
        prompt = build_evaluation_prompt(claim, evidence_nodes)
        result = await self._call_llm(prompt, self.model)

        if not result:
            return EvaluationResult(claim_id="", score=0.5, strategy=strategy)

        # Create the claim node
        claim_node = ReasoningNode(
            id=str(uuid4())[:8],
            node_type=NodeType.CLAIM,
            content=claim,
            confidence=result.get("score", 0.5),
            source=f"evaluation:{strategy}",
        )
        self.graph.add_node(claim_node)

        # Link evidence
        for eid in result.get("supporting", []):
            self.graph.add_edge(ReasoningEdge(
                source_id=eid, target_id=claim_node.id,
                edge_type=EdgeType.SUPPORTS, reasoning="evaluation",
            ))
        for eid in result.get("contradicting", []):
            self.graph.add_edge(ReasoningEdge(
                source_id=eid, target_id=claim_node.id,
                edge_type=EdgeType.CONTRADICTS, reasoning="evaluation",
            ))

        return EvaluationResult(
            claim_id=claim_node.id,
            score=result.get("score", 0.5),
            supporting_evidence=result.get("supporting", []),
            contradicting_evidence=result.get("contradicting", []),
            reasoning=result.get("reasoning", ""),
            strategy=strategy,
        )

    async def make_decision(
        self,
        question: str,
        options: list[str] | None = None,
        strategy: str = "",
        gather_evidence: bool = True,
    ) -> DecisionTrace:
        """Make a structured decision with full trace."""
        strategy = strategy or self.config.default_strategy

        # Gather evidence
        evidence_nodes: list[ReasoningNode] = []
        if gather_evidence:
            evidence_nodes = await self._gather_evidence(question)

        # Build strategy prompt
        strategy_fn = STRATEGIES.get(strategy, STRATEGIES["weighted_evidence"])
        prompt = strategy_fn(question, evidence_nodes, options)
        result = await self._call_llm(prompt, self.model)

        if not result:
            return DecisionTrace(
                id=str(uuid4())[:8], question=question,
                strategy=strategy, agent_id=self.agent_id,
            )

        # Create decision node
        decision_node = ReasoningNode(
            id=str(uuid4())[:8],
            node_type=NodeType.DECISION,
            content=result.get("conclusion", ""),
            confidence=result.get("confidence", 0.5),
            source=f"decision:{strategy}",
        )
        self.graph.add_node(decision_node)

        # Link evidence to decision
        evidence_ids = [n.id for n in evidence_nodes]
        for eid in evidence_ids:
            self.graph.add_edge(ReasoningEdge(
                source_id=eid, target_id=decision_node.id,
                edge_type=EdgeType.SUPPORTS, reasoning="gathered for decision",
            ))

        # Extract any new claims from the LLM response
        for claim_data in result.get("claims", []):
            claim_node = ReasoningNode(
                id=str(uuid4())[:8],
                node_type=NodeType(claim_data.get("type", "claim")),
                content=claim_data.get("content", ""),
                confidence=claim_data.get("confidence", 0.5),
                source=f"derived:decision:{decision_node.id}",
            )
            self.graph.add_node(claim_node)

        # Build alternatives
        alternatives = [
            Alternative(
                option=alt.get("option", ""),
                score=alt.get("score", 0.0),
                reasoning=alt.get("reasoning", ""),
            )
            for alt in result.get("alternatives", [])
        ]

        # Build and persist the trace
        trace = DecisionTrace(
            id=str(uuid4())[:8],
            question=question,
            strategy=strategy,
            claims_considered=[n.id for n in evidence_nodes if n.node_type == NodeType.CLAIM],
            evidence_used=evidence_ids,
            conclusion=result.get("conclusion", ""),
            confidence=result.get("confidence", 0.5),
            alternatives=alternatives,
            agent_id=self.agent_id,
        )
        self.graph.add_trace(trace)

        return trace

    async def resolve_contradiction(
        self,
        node_id_a: str,
        node_id_b: str,
    ) -> ReasoningNode | None:
        """Resolve a contradiction between two nodes."""
        node_a = self.graph.get_node(node_id_a)
        node_b = self.graph.get_node(node_id_b)
        if not node_a or not node_b:
            logger.warning("Cannot resolve — missing node(s): %s, %s", node_id_a, node_id_b)
            return None

        # Gather context for resolution
        context_parts = []
        for node in [node_a, node_b]:
            supporting = self.graph.get_supporting(node.id)
            if supporting:
                context_parts.append(
                    f"Evidence supporting '{node.content[:50]}': "
                    + "; ".join(s.content[:80] for s in supporting)
                )

        prompt = RESOLVE_CONTRADICTION_PROMPT.format(
            node_a=f"[{node_a.id}] {node_a.content} (confidence: {node_a.confidence:.2f})",
            node_b=f"[{node_b.id}] {node_b.content} (confidence: {node_b.confidence:.2f})",
            context="\n".join(context_parts) if context_parts else "No additional context.",
        )
        result = await self._call_llm(prompt, self.model)
        if not result:
            return None

        # Create resolution node
        resolution = ReasoningNode(
            id=str(uuid4())[:8],
            node_type=NodeType.CLAIM,
            content=result.get("resolution", ""),
            confidence=result.get("confidence", 0.5),
            source=f"resolution:{node_id_a}+{node_id_b}",
        )
        self.graph.add_node(resolution)

        # Supersede the loser(s)
        keep = result.get("keep", "both")
        if keep in ("a", "neither"):
            self.graph.add_edge(ReasoningEdge(
                source_id=resolution.id, target_id=node_id_b,
                edge_type=EdgeType.SUPERSEDES, reasoning=result.get("reasoning", ""),
            ))
        if keep in ("b", "neither"):
            self.graph.add_edge(ReasoningEdge(
                source_id=resolution.id, target_id=node_id_a,
                edge_type=EdgeType.SUPERSEDES, reasoning=result.get("reasoning", ""),
            ))

        return resolution

    async def explain_decision(self, query: str) -> str:
        """Explain a decision by searching traces and building a narrative."""
        # Search for relevant traces
        traces = self.graph.get_recent_traces(limit=20)
        matching = [
            t for t in traces
            if query.lower() in t.question.lower() or query.lower() in t.conclusion.lower()
        ]

        if not matching:
            # Fallback: search the graph directly
            nodes = self.graph.search(query)
            if nodes:
                return self.graph.explain(nodes[0].id)
            return f"No decisions found matching: {query}"

        trace = matching[0]
        evidence_chain = []
        for eid in trace.evidence_used:
            node = self.graph.get_node(eid)
            if node:
                evidence_chain.append(
                    f"- [{node.id}] ({node.node_type.value}, "
                    f"conf: {node.confidence:.2f}): {node.content}"
                )

        prompt = EXPLAIN_DECISION_PROMPT.format(
            decision=(
                f"Question: {trace.question}\n"
                f"Conclusion: {trace.conclusion}\n"
                f"Strategy: {trace.strategy}\n"
                f"Confidence: {trace.confidence:.2f}"
            ),
            evidence_chain="\n".join(evidence_chain) if evidence_chain else "No evidence chain recorded.",
        )
        result = await self._call_llm(prompt, self.model, parse_json=False)
        return result if isinstance(result, str) else str(result)

    # ── Background operations (fire-and-forget, cheap model) ────

    async def background_evaluate(
        self,
        claim: str,
        evidence_paths: list[str],
    ) -> None:
        """Fire-and-forget evaluation using the cheap model."""
        try:
            evidence_nodes = self._load_evidence_from_paths(evidence_paths)
            prompt = build_evaluation_prompt(claim, evidence_nodes)
            result = await self._call_llm(prompt, self.background_model)
            if result:
                node = ReasoningNode(
                    id=str(uuid4())[:8],
                    node_type=NodeType.CLAIM,
                    content=claim,
                    confidence=result.get("score", 0.5),
                    source="background_evaluation",
                )
                self.graph.add_node(node)
        except Exception as e:
            logger.debug("Background evaluation failed (non-critical): %s", e)

    async def ingest_huddle_conclusion(
        self,
        transcript: str,
        topic: str,
    ) -> None:
        """Extract reasoning nodes from a huddle transcript (fire-and-forget)."""
        try:
            prompt = EXTRACT_FROM_HUDDLE_PROMPT.format(
                topic=topic,
                transcript=transcript[:6000],  # cap transcript size
            )
            result = await self._call_llm(prompt, self.background_model)
            if not result:
                return

            # Add extracted claims
            for claim_data in result.get("claims", []):
                node = ReasoningNode(
                    id=str(uuid4())[:8],
                    node_type=NodeType.CLAIM,
                    content=claim_data.get("content", ""),
                    confidence=claim_data.get("confidence", 0.5),
                    source=f"huddle:{claim_data.get('source', 'unknown')}",
                    tags=["huddle"],
                )
                self.graph.add_node(node)

            # Add extracted evidence
            for ev_data in result.get("evidence", []):
                node = ReasoningNode(
                    id=str(uuid4())[:8],
                    node_type=NodeType.EVIDENCE,
                    content=ev_data.get("content", ""),
                    confidence=ev_data.get("confidence", 0.5),
                    source=f"huddle:{ev_data.get('source', 'unknown')}",
                    tags=["huddle"],
                )
                self.graph.add_node(node)

            # Add extracted decisions as traces
            for dec_data in result.get("decisions", []):
                trace = DecisionTrace(
                    id=str(uuid4())[:8],
                    question=dec_data.get("question", ""),
                    strategy="consensus",
                    conclusion=dec_data.get("conclusion", ""),
                    confidence=dec_data.get("confidence", 0.5),
                    agent_id="huddle",
                )
                self.graph.add_trace(trace)

            # Record contradictions as edges
            for contra in result.get("contradictions", []):
                # Find matching nodes by content
                nodes_a = self.graph.search(contra.get("claim_a", ""))
                nodes_b = self.graph.search(contra.get("claim_b", ""))
                if nodes_a and nodes_b:
                    self.graph.add_edge(ReasoningEdge(
                        source_id=nodes_a[0].id,
                        target_id=nodes_b[0].id,
                        edge_type=EdgeType.CONTRADICTS,
                        reasoning=contra.get("description", ""),
                    ))

            logger.debug(
                "Ingested huddle: %d claims, %d evidence, %d decisions",
                len(result.get("claims", [])),
                len(result.get("evidence", [])),
                len(result.get("decisions", [])),
            )
        except Exception as e:
            logger.debug("Huddle ingestion failed (non-critical): %s", e)

    # ── Internal helpers ────────────────────────────────────────────

    async def _gather_evidence(self, question: str) -> list[ReasoningNode]:
        """Search the vault and graph for evidence relevant to a question."""
        nodes: list[ReasoningNode] = []

        # 1. Search the reasoning graph for existing relevant nodes
        graph_results = self.graph.search(question)
        nodes.extend(graph_results[:10])

        # 2. Search the vault for relevant files
        vault_results = self.vault.search(question)
        for vr in vault_results[:5]:
            path = vr.get("path", "")
            content = vr.get("snippet", vr.get("title", ""))
            if not content:
                continue
            # Create evidence nodes from vault search results
            node = ReasoningNode(
                id=str(uuid4())[:8],
                node_type=NodeType.EVIDENCE,
                content=content[:500],
                confidence=0.6,  # vault entries start at moderate confidence
                source=f"vault:{path}",
            )
            self.graph.add_node(node)
            nodes.append(node)

        return nodes

    def _load_evidence_from_paths(self, paths: list[str]) -> list[ReasoningNode]:
        """Load evidence from specific vault paths."""
        nodes: list[ReasoningNode] = []
        for path in paths:
            try:
                metadata, body = self.vault.read_file(path)
                content = f"{metadata.get('name', '')}: {body[:300]}"
                confidence = float(metadata.get("confidence", 0.6))
                node = ReasoningNode(
                    id=str(uuid4())[:8],
                    node_type=NodeType.EVIDENCE,
                    content=content,
                    confidence=confidence,
                    source=f"vault:{path}",
                )
                self.graph.add_node(node)
                nodes.append(node)
            except Exception as e:
                logger.warning("Failed to load evidence from %s: %s", path, e)
        return nodes

    async def _call_llm(
        self,
        prompt: str,
        model: str,
        parse_json: bool = True,
    ) -> dict[str, Any] | str | None:
        """Call the LLM and parse the response."""
        try:
            response = await complete(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2048,
                temperature=0.3,
            )

            if self._usage_tracker:
                usage = response.get("usage")
                if usage:
                    try:
                        self._usage_tracker.record(
                            model=model,
                            prompt_tokens=usage.get("prompt_tokens", 0),
                            completion_tokens=usage.get("completion_tokens", 0),
                            total_tokens=usage.get("total_tokens", 0),
                            cost=usage.get("cost", 0.0),
                            agent_id=self.agent_id,
                            org_id=self._org_id,
                            call_type="completion",
                            caller="reasoning_engine",
                        )
                    except Exception:
                        pass

            content = response.get("content", "")
            if not parse_json:
                return content
            return parse_llm_json(content)

        except Exception as e:
            logger.warning("Reasoning LLM call failed: %s", e)
            return None

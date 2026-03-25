"""Reasoning graph — CRUD, persistence, and query over claims/evidence/decisions."""

from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from axon.reasoning.config import ReasoningConfig
from axon.reasoning.models import (
    ContradictionPair,
    DecisionTrace,
    EdgeType,
    NodeType,
    ReasoningEdge,
    ReasoningNode,
)
from axon.vault.vault import VaultManager

logger = logging.getLogger(__name__)

INDEX_PATH = "reasoning/graph-index.md"


class ReasoningGraph:
    """In-memory reasoning graph backed by vault persistence.

    The graph index (nodes + edges as JSON) lives in a single vault file
    for fast load. Individual decision traces get their own vault files
    for discoverability and wikilink integration.
    """

    def __init__(self, vault: VaultManager, config: ReasoningConfig):
        self.vault = vault
        self.config = config
        self._nodes: dict[str, ReasoningNode] = {}
        self._edges: list[ReasoningEdge] = []
        self._traces: dict[str, DecisionTrace] = {}
        self._loaded = False
        self._lock = asyncio.Lock()

        # Adjacency indexes for fast lookup
        self._outgoing: dict[str, list[ReasoningEdge]] = defaultdict(list)
        self._incoming: dict[str, list[ReasoningEdge]] = defaultdict(list)

    def _ensure_loaded(self) -> None:
        """Lazy-load from vault on first access."""
        if not self._loaded:
            self._load_from_vault()
            self._loaded = True

    # ── CRUD ────────────────────────────────────────────────────────

    def add_node(self, node: ReasoningNode) -> str:
        """Add a node to the graph. Returns the node ID."""
        self._ensure_loaded()
        if not node.id:
            node.id = str(uuid4())[:8]
        if not node.created_at:
            node.created_at = datetime.now(timezone.utc).isoformat()

        # Cap graph size
        if len(self._nodes) >= self.config.max_graph_nodes:
            self._prune_lowest_confidence()

        self._nodes[node.id] = node
        self._save_index()
        return node.id

    def add_edge(self, edge: ReasoningEdge) -> None:
        """Add a directed edge between two nodes."""
        self._ensure_loaded()
        if edge.source_id not in self._nodes or edge.target_id not in self._nodes:
            logger.warning("Edge references missing node: %s → %s", edge.source_id, edge.target_id)
            return
        self._edges.append(edge)
        self._outgoing[edge.source_id].append(edge)
        self._incoming[edge.target_id].append(edge)
        self._save_index()

    def get_node(self, node_id: str) -> ReasoningNode | None:
        """Get a node by ID."""
        self._ensure_loaded()
        return self._nodes.get(node_id)

    def remove_node(self, node_id: str) -> None:
        """Remove a node and all its edges."""
        self._ensure_loaded()
        self._nodes.pop(node_id, None)
        self._edges = [e for e in self._edges if e.source_id != node_id and e.target_id != node_id]
        self._rebuild_indexes()
        self._save_index()

    def add_trace(self, trace: DecisionTrace) -> str:
        """Add a decision trace and persist it as a vault file."""
        self._ensure_loaded()
        if not trace.id:
            trace.id = str(uuid4())[:8]
        if not trace.created_at:
            trace.created_at = datetime.now(timezone.utc).isoformat()
        self._traces[trace.id] = trace

        if self.config.persist_traces:
            self._persist_trace(trace)

        self._save_index()
        return trace.id

    # ── Query ───────────────────────────────────────────────────────

    def get_supporting(self, node_id: str) -> list[ReasoningNode]:
        """Get all nodes that support the given node."""
        self._ensure_loaded()
        return [
            self._nodes[e.source_id]
            for e in self._incoming.get(node_id, [])
            if e.edge_type == EdgeType.SUPPORTS and e.source_id in self._nodes
        ]

    def get_contradicting(self, node_id: str) -> list[ReasoningNode]:
        """Get all nodes that contradict the given node."""
        self._ensure_loaded()
        return [
            self._nodes[e.source_id]
            for e in self._incoming.get(node_id, [])
            if e.edge_type == EdgeType.CONTRADICTS and e.source_id in self._nodes
        ]

    def get_dependencies(self, node_id: str) -> list[ReasoningNode]:
        """Get all nodes this node depends on."""
        self._ensure_loaded()
        return [
            self._nodes[e.target_id]
            for e in self._outgoing.get(node_id, [])
            if e.edge_type == EdgeType.DEPENDS_ON and e.target_id in self._nodes
        ]

    def get_trace(self, trace_id: str) -> DecisionTrace | None:
        """Get a decision trace by ID."""
        self._ensure_loaded()
        return self._traces.get(trace_id)

    def find_contradictions(self) -> list[ContradictionPair]:
        """Find all pairs of contradicting nodes in the graph."""
        self._ensure_loaded()
        pairs: list[ContradictionPair] = []
        seen: set[tuple[str, str]] = set()
        for edge in self._edges:
            if edge.edge_type != EdgeType.CONTRADICTS:
                continue
            pair_key = tuple(sorted([edge.source_id, edge.target_id]))
            if pair_key in seen:
                continue
            seen.add(pair_key)
            pairs.append(ContradictionPair(
                node_a_id=edge.source_id,
                node_b_id=edge.target_id,
                description=edge.reasoning,
            ))
        return pairs

    def search(self, query: str) -> list[ReasoningNode]:
        """Simple text search across node content."""
        self._ensure_loaded()
        query_lower = query.lower()
        results = []
        for node in self._nodes.values():
            if query_lower in node.content.lower():
                results.append(node)
        return sorted(results, key=lambda n: n.confidence, reverse=True)

    def explain(self, node_id: str, depth: int = 3) -> str:
        """BFS through edges to produce a markdown explanation of why a node exists."""
        self._ensure_loaded()
        root = self._nodes.get(node_id)
        if not root:
            return f"Node {node_id} not found."

        lines = [f"## {root.node_type.value.title()}: {root.content}"]
        lines.append(f"Confidence: {root.confidence:.2f}\n")

        visited: set[str] = {node_id}
        queue: list[tuple[str, int]] = [(node_id, 0)]

        while queue:
            current_id, level = queue.pop(0)
            if level >= depth:
                continue

            indent = "  " * (level + 1)
            for edge in self._incoming.get(current_id, []):
                source = self._nodes.get(edge.source_id)
                if not source or edge.source_id in visited:
                    continue
                visited.add(edge.source_id)
                icon = _edge_icon(edge.edge_type)
                lines.append(
                    f"{indent}{icon} **{edge.edge_type.value}** "
                    f"({source.node_type.value}): {source.content} "
                    f"[conf: {source.confidence:.2f}]"
                )
                queue.append((edge.source_id, level + 1))

        return "\n".join(lines)

    def get_all_nodes(self) -> list[ReasoningNode]:
        """Return all nodes in the graph."""
        self._ensure_loaded()
        return list(self._nodes.values())

    def get_recent_traces(self, limit: int = 10) -> list[DecisionTrace]:
        """Return the most recent decision traces."""
        self._ensure_loaded()
        traces = sorted(
            self._traces.values(),
            key=lambda t: t.created_at,
            reverse=True,
        )
        return traces[:limit]

    # ── Persistence ─────────────────────────────────────────────────

    def _load_from_vault(self) -> None:
        """Load graph index from vault."""
        try:
            raw = self.vault.read_file_raw(INDEX_PATH)
        except (FileNotFoundError, Exception):
            logger.debug("No existing reasoning graph — starting fresh")
            return

        # Extract JSON from the body (after frontmatter)
        body = _extract_body(raw)
        if not body:
            return

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            logger.warning("Failed to parse reasoning graph index JSON")
            return

        for nd in data.get("nodes", []):
            node = ReasoningNode(**nd)
            self._nodes[node.id] = node

        for ed in data.get("edges", []):
            edge = ReasoningEdge(**ed)
            self._edges.append(edge)

        for td in data.get("traces", []):
            trace = DecisionTrace(**td)
            self._traces[trace.id] = trace

        self._rebuild_indexes()
        logger.debug(
            "Loaded reasoning graph: %d nodes, %d edges, %d traces",
            len(self._nodes), len(self._edges), len(self._traces),
        )

    def _save_index(self) -> None:
        """Persist graph index to vault as a single JSON-in-markdown file."""
        data = {
            "nodes": [n.model_dump() for n in self._nodes.values()],
            "edges": [e.model_dump() for e in self._edges],
            "traces": [t.model_dump() for t in self._traces.values()],
        }
        metadata: dict[str, Any] = {
            "name": "Reasoning Graph Index",
            "type": "reasoning-graph",
            "node_count": len(self._nodes),
            "edge_count": len(self._edges),
            "trace_count": len(self._traces),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        body = json.dumps(data, indent=2)
        self.vault.write_file(INDEX_PATH, metadata, body)

    def _persist_trace(self, trace: DecisionTrace) -> None:
        """Write a decision trace as its own vault file for discoverability."""
        date_str = trace.created_at[:10] if trace.created_at else "unknown"
        slug = trace.question[:50].lower().replace(" ", "-")
        slug = "".join(c for c in slug if c.isalnum() or c == "-")
        path = f"reasoning/traces/{date_str}-{slug}.md"

        metadata: dict[str, Any] = {
            "name": trace.question[:100],
            "type": "decision-trace",
            "strategy": trace.strategy,
            "confidence": trace.confidence,
            "agent_id": trace.agent_id,
            "date": date_str,
            "status": "active",
        }

        # Build readable body
        lines = [f"## Question\n{trace.question}\n"]

        if trace.evidence_used:
            lines.append("## Evidence Considered")
            for eid in trace.evidence_used:
                node = self._nodes.get(eid)
                content = node.content[:100] if node else eid
                lines.append(f"- {content}")
            lines.append("")

        lines.append(f"## Conclusion\n{trace.conclusion}\n")

        if trace.alternatives:
            lines.append("## Alternatives")
            for alt in trace.alternatives:
                lines.append(f"- **{alt.option}** (score: {alt.score:.2f}): {alt.reasoning}")
            lines.append("")

        body = "\n".join(lines)
        trace.vault_path = path
        self.vault.write_file(path, metadata, body)

    def _rebuild_indexes(self) -> None:
        """Rebuild adjacency indexes from edge list."""
        self._outgoing = defaultdict(list)
        self._incoming = defaultdict(list)
        for edge in self._edges:
            self._outgoing[edge.source_id].append(edge)
            self._incoming[edge.target_id].append(edge)

    def _prune_lowest_confidence(self) -> None:
        """Remove the lowest-confidence non-decision node to make room."""
        candidates = [
            n for n in self._nodes.values()
            if n.node_type != NodeType.DECISION
        ]
        if not candidates:
            return
        weakest = min(candidates, key=lambda n: n.confidence)
        logger.debug("Pruning node %s (confidence %.2f) to stay under limit", weakest.id, weakest.confidence)
        self.remove_node(weakest.id)


def _edge_icon(edge_type: EdgeType) -> str:
    """Visual icon for edge type in explanations."""
    return {
        EdgeType.SUPPORTS: "+",
        EdgeType.CONTRADICTS: "x",
        EdgeType.DEPENDS_ON: "^",
        EdgeType.SUPERSEDES: ">",
    }.get(edge_type, "-")


def _extract_body(raw: str) -> str:
    """Extract body content after YAML frontmatter."""
    if not raw.startswith("---"):
        return raw
    end = raw.find("---", 3)
    if end == -1:
        return raw
    return raw[end + 3:].strip()

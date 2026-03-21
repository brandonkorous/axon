"""Memory navigator — retrieves relevant vault context for agent conversations.

MVP: Deterministic search using vault structure, keyword matching, and graph signals.
The vault's own structure (branches, indexes, wikilinks) IS the index.

Future: Optional AI navigator that uses a cheap LLM to traverse the graph when
deterministic search has low confidence.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from axon.vault.frontmatter import parse_frontmatter
from axon.vault.graph import VaultGraph
from axon.vault.wikilinks import extract_wikilinks


@dataclass
class RetrievedContext:
    """Context retrieved from the vault for a query."""

    files: list[dict[str, Any]]  # [{path, title, content, relevance_score}]
    total_tokens: int  # Estimated token count
    query: str


class MemoryNavigator:
    """Navigates the vault's semantic graph to find relevant context.

    Strategy:
    1. Tokenize query into keywords
    2. Score each vault file by keyword hits in: title, description, content, tags
    3. Boost files that are heavily linked (hub nodes are likely important)
    4. Boost files linked from high-scoring files (follow the graph)
    5. Return top files within token budget
    """

    def __init__(self, vault_path: str | Path, root_file: str = "second-brain.md"):
        self.vault_path = Path(vault_path)
        self.root_file = root_file
        self._graph: VaultGraph | None = None

    @property
    def graph(self) -> VaultGraph:
        if self._graph is None:
            self._graph = VaultGraph.build(self.vault_path)
        return self._graph

    def rebuild(self) -> None:
        self._graph = None

    async def retrieve(self, query: str, token_budget: int = 4000) -> str:
        """Retrieve relevant vault context for a query.

        Returns formatted markdown string with the most relevant vault content,
        fitted within the token budget.
        """
        result = self._search_and_rank(query, token_budget)
        return self._format_context(result)

    def _search_and_rank(self, query: str, token_budget: int) -> RetrievedContext:
        """Score, rank, and select vault files for a query."""
        keywords = self._tokenize(query)
        if not keywords:
            # No meaningful keywords — return root context
            root_content = self._read_file(self.root_file)
            return RetrievedContext(
                files=[{
                    "path": self.root_file,
                    "title": "Root",
                    "content": root_content,
                    "relevance_score": 1.0,
                }],
                total_tokens=len(root_content) // 4,
                query=query,
            )

        # Score all files
        scores: dict[str, float] = {}
        file_contents: dict[str, str] = {}

        for md_file in self.vault_path.rglob("*.md"):
            if md_file.name.startswith("."):
                continue
            rel_path = str(md_file.relative_to(self.vault_path)).replace("\\", "/")
            try:
                content = md_file.read_text(encoding="utf-8")
            except Exception:
                continue

            file_contents[rel_path] = content
            score = self._score_file(rel_path, content, keywords)
            if score > 0:
                scores[rel_path] = score

        # Boost scores based on graph signals
        self._apply_graph_boost(scores)

        # Always include root with a baseline score
        if self.root_file not in scores:
            scores[self.root_file] = 0.1

        # Sort by score, select within budget
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        selected: list[dict[str, Any]] = []
        tokens_used = 0

        for path, score in ranked:
            content = file_contents.get(path, self._read_file(path))
            estimated_tokens = len(content) // 4

            if tokens_used + estimated_tokens > token_budget:
                # Try to include a truncated version
                remaining = token_budget - tokens_used
                if remaining > 200:  # Worth including if >200 tokens
                    content = content[: remaining * 4]
                    estimated_tokens = remaining
                else:
                    continue

            selected.append({
                "path": path,
                "title": self._get_title(path, content),
                "content": content,
                "relevance_score": score,
            })
            tokens_used += estimated_tokens

            if tokens_used >= token_budget:
                break

        return RetrievedContext(files=selected, total_tokens=tokens_used, query=query)

    def _score_file(self, path: str, content: str, keywords: list[str]) -> float:
        """Score a file's relevance to a set of keywords."""
        score = 0.0
        content_lower = content.lower()
        path_lower = path.lower()

        # Parse frontmatter for structured scoring
        try:
            metadata, body = parse_frontmatter(content)
        except Exception:
            metadata, body = {}, content

        title = str(metadata.get("name", "")).lower()
        description = str(metadata.get("description", "")).lower()
        tags = str(metadata.get("tags", "")).lower()

        for keyword in keywords:
            kw = keyword.lower()
            # Title match (highest weight)
            if kw in title:
                score += 5.0
            # Description match
            if kw in description:
                score += 3.0
            # Path/filename match
            if kw in path_lower:
                score += 3.0
            # Tags match
            if kw in tags:
                score += 2.0
            # Body content match (lower weight, count occurrences)
            count = body.lower().count(kw)
            if count > 0:
                score += min(count * 0.5, 3.0)  # Cap body match contribution

        return score

    def _apply_graph_boost(self, scores: dict[str, float]) -> None:
        """Boost scores based on graph structure.

        - Hub nodes (many links) get a small boost
        - Files linked FROM high-scoring files get boosted (propagate relevance)
        """
        graph = self.graph

        # Hub boost: files with many connections are generally more important
        for path, score in list(scores.items()):
            node = graph.nodes.get(path)
            if node:
                hub_score = (node.link_count + node.backlink_count) * 0.1
                scores[path] = score + min(hub_score, 2.0)  # Cap hub boost

        # Propagation: if A scores high and links to B, boost B
        propagation: dict[str, float] = {}
        for path, score in scores.items():
            if score < 2.0:
                continue  # Only propagate from reasonably relevant files
            for neighbor in graph.get_neighbors(path):
                if neighbor not in scores or scores[neighbor] < score * 0.3:
                    propagation[neighbor] = max(
                        propagation.get(neighbor, 0),
                        score * 0.3,  # 30% of parent's score
                    )

        for path, boost in propagation.items():
            scores[path] = scores.get(path, 0) + boost

    def _tokenize(self, query: str) -> list[str]:
        """Extract meaningful keywords from a query."""
        # Remove common stop words
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "shall", "can", "need", "dare", "ought",
            "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
            "as", "into", "through", "during", "before", "after", "above", "below",
            "between", "out", "off", "over", "under", "again", "further", "then",
            "once", "here", "there", "when", "where", "why", "how", "all", "each",
            "every", "both", "few", "more", "most", "other", "some", "such", "no",
            "nor", "not", "only", "own", "same", "so", "than", "too", "very",
            "just", "about", "what", "which", "who", "whom", "this", "that",
            "these", "those", "i", "me", "my", "we", "our", "you", "your",
            "he", "him", "his", "she", "her", "it", "its", "they", "them", "their",
            "and", "but", "or", "if", "while", "because", "until", "although",
        }
        words = re.findall(r"[a-zA-Z0-9]+", query.lower())
        return [w for w in words if w not in stop_words and len(w) > 1]

    def _get_title(self, path: str, content: str) -> str:
        """Extract title from frontmatter or filename."""
        try:
            metadata, _ = parse_frontmatter(content)
            return metadata.get("name", Path(path).stem)
        except Exception:
            return Path(path).stem

    def _read_file(self, relative_path: str) -> str:
        """Read a file's content."""
        full_path = self.vault_path / relative_path
        if full_path.exists():
            return full_path.read_text(encoding="utf-8")
        return ""

    def _format_context(self, result: RetrievedContext) -> str:
        """Format retrieved context as a markdown string for the LLM."""
        if not result.files:
            return "*No relevant vault context found.*"

        sections: list[str] = []
        for f in result.files:
            header = f"### {f['title']} (`{f['path']}`)"
            sections.append(f"{header}\n{f['content']}")

        return "\n\n---\n\n".join(sections)

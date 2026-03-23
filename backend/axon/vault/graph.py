"""Vault graph builder — builds the wikilink adjacency graph for navigation and visualization."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from axon.vault.wikilinks import WikiLink, extract_wikilinks, resolve_wikilink


@dataclass
class GraphNode:
    """A node in the vault graph (one markdown file)."""

    path: str  # Relative path from vault root
    name: str  # Filename without extension
    branch: str  # Top-level directory (e.g., "decisions", "contacts")
    title: str  # From frontmatter name field, or filename
    description: str  # From frontmatter description field
    link_count: int = 0  # Number of outgoing links
    backlink_count: int = 0  # Number of incoming links
    tags: list[str] = field(default_factory=list)


@dataclass
class GraphEdge:
    """An edge in the vault graph (one wikilink)."""

    source: str  # Source file path
    target: str  # Target file path
    context: str  # Surrounding text (semantic signal)
    line_number: int


@dataclass
class VaultGraph:
    """The complete wikilink graph for a vault."""

    nodes: dict[str, GraphNode]  # path -> node
    edges: list[GraphEdge]
    adjacency: dict[str, list[str]]  # path -> [linked paths]
    backlinks: dict[str, list[str]]  # path -> [paths that link here]

    @classmethod
    def build(cls, vault_root: str | Path) -> VaultGraph:
        """Build the complete graph by scanning all markdown files in the vault."""
        root = Path(vault_root)
        nodes: dict[str, GraphNode] = {}
        edges: list[GraphEdge] = []
        adjacency: dict[str, list[str]] = {}
        backlinks: dict[str, list[str]] = {}

        # First pass: discover all files and build nodes
        for md_file in root.rglob("*.md"):
            if md_file.name.startswith("."):
                continue

            rel_path = str(md_file.relative_to(root)).replace("\\", "/")
            parts = rel_path.split("/")
            branch = parts[0] if len(parts) > 1 else ""
            name = md_file.stem

            # Parse frontmatter for metadata
            title = name
            description = ""
            tags: list[str] = []
            try:
                content = md_file.read_text(encoding="utf-8")
                if content.startswith("---"):
                    import yaml

                    end = content.index("---", 3)
                    fm = yaml.safe_load(content[3:end])
                    if isinstance(fm, dict):
                        title = fm.get("name", name)
                        description = fm.get("description", "")
                        raw_tags = fm.get("tags", "")
                        if isinstance(raw_tags, str):
                            tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
                        elif isinstance(raw_tags, list):
                            tags = raw_tags
            except Exception:
                pass

            nodes[rel_path] = GraphNode(
                path=rel_path,
                name=name,
                branch=branch,
                title=title,
                description=description,
                tags=tags,
            )
            adjacency[rel_path] = []
            backlinks[rel_path] = []

        # Second pass: extract wikilinks and build edges
        for rel_path, node in nodes.items():
            md_file = root / rel_path
            try:
                content = md_file.read_text(encoding="utf-8")
            except Exception:
                continue

            links = extract_wikilinks(content)
            for link in links:
                resolved = resolve_wikilink(link.target, root, md_file)
                if resolved and resolved.exists():
                    target_path = str(resolved.relative_to(root)).replace("\\", "/")
                    if target_path in nodes:
                        edge = GraphEdge(
                            source=rel_path,
                            target=target_path,
                            context=link.context,
                            line_number=link.line_number,
                        )
                        edges.append(edge)
                        adjacency[rel_path].append(target_path)
                        backlinks.setdefault(target_path, []).append(rel_path)

            node.link_count = len(adjacency.get(rel_path, []))

        # Compute backlink counts
        for path, bl in backlinks.items():
            if path in nodes:
                nodes[path].backlink_count = len(bl)

        return cls(nodes=nodes, edges=edges, adjacency=adjacency, backlinks=backlinks)

    def get_neighbors(self, path: str) -> list[str]:
        """Get all files linked from a given file."""
        return self.adjacency.get(path, [])

    def get_backlinks(self, path: str) -> list[str]:
        """Get all files that link to a given file."""
        return self.backlinks.get(path, [])

    def get_most_connected(self, n: int = 10) -> list[GraphNode]:
        """Get the N most connected nodes (by total link + backlink count)."""
        scored = [
            (node, node.link_count + node.backlink_count)
            for node in self.nodes.values()
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [node for node, _ in scored[:n]]

    def get_neighborhood(self, path: str, depth: int = 2) -> dict:
        """BFS from a node, return subgraph within `depth` hops."""
        if path not in self.nodes:
            return {"nodes": [], "edges": []}

        visited: set[str] = set()
        queue = [(path, 0)]
        visited.add(path)

        while queue:
            current, d = queue.pop(0)
            if d >= depth:
                continue
            for neighbor in self.get_neighbors(current) + self.get_backlinks(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, d + 1))

        sub_nodes = [self.nodes[p] for p in visited if p in self.nodes]
        sub_edges = [e for e in self.edges if e.source in visited and e.target in visited]

        return {
            "nodes": [
                {
                    "id": n.path,
                    "name": n.name,
                    "branch": n.branch,
                    "title": n.title,
                    "description": n.description,
                    "linkCount": n.link_count,
                    "backlinkCount": n.backlink_count,
                    "tags": n.tags,
                }
                for n in sub_nodes
            ],
            "edges": [
                {"source": e.source, "target": e.target, "context": e.context}
                for e in sub_edges
            ],
        }

    def get_stats(self) -> dict:
        """Return graph statistics."""
        branch_counts: dict[str, int] = {}
        for node in self.nodes.values():
            branch_counts[node.branch] = branch_counts.get(node.branch, 0) + 1

        top_connected = self.get_most_connected(5)

        return {
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "branches": branch_counts,
            "top_connected": [
                {"path": n.path, "title": n.title, "connections": n.link_count + n.backlink_count}
                for n in top_connected
            ],
        }

    def to_json(self) -> dict:
        """Serialize graph for the frontend memory browser."""
        return {
            "nodes": [
                {
                    "id": node.path,
                    "name": node.name,
                    "branch": node.branch,
                    "title": node.title,
                    "description": node.description,
                    "linkCount": node.link_count,
                    "backlinkCount": node.backlink_count,
                    "tags": node.tags,
                }
                for node in self.nodes.values()
            ],
            "edges": [
                {
                    "source": edge.source,
                    "target": edge.target,
                    "context": edge.context,
                }
                for edge in self.edges
            ],
        }

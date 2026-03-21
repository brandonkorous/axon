"""VaultManager — the core interface for reading, writing, and searching Obsidian vaults."""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from typing import Any

from axon.vault.frontmatter import (
    parse_frontmatter,
    read_file_with_frontmatter,
    write_file_with_frontmatter,
)
from axon.vault.graph import VaultGraph
from axon.vault.wikilinks import add_wikilink, extract_wikilinks, resolve_wikilink


class VaultManager:
    """Interface to an Obsidian vault on the filesystem.

    Handles reading, writing, searching, and linking of markdown files
    with YAML frontmatter and [[wikilinks]].
    """

    def __init__(self, vault_path: str, root_file: str = "second-brain.md"):
        self.vault_path = Path(vault_path)
        self.root_file = root_file
        self._graph: VaultGraph | None = None

    @property
    def root_path(self) -> Path:
        return self.vault_path / self.root_file

    @property
    def graph(self) -> VaultGraph:
        """Lazy-loaded vault graph. Call rebuild_graph() to refresh."""
        if self._graph is None:
            self._graph = VaultGraph.build(self.vault_path)
        return self._graph

    def rebuild_graph(self) -> VaultGraph:
        """Rebuild the wikilink graph from disk."""
        self._graph = VaultGraph.build(self.vault_path)
        return self._graph

    # ── Read operations ──────────────────────────────────────────────

    def read_root(self) -> str:
        """Read the root orientation file."""
        if not self.root_path.exists():
            return f"# Vault\n\nNo root file found at {self.root_file}"
        return self.root_path.read_text(encoding="utf-8")

    def read_file(self, relative_path: str) -> tuple[dict[str, Any], str]:
        """Read a file, return (frontmatter_dict, body_string).

        Raises FileNotFoundError if the file doesn't exist.
        """
        full_path = self.vault_path / relative_path
        if not full_path.exists():
            raise FileNotFoundError(f"Vault file not found: {relative_path}")
        self._check_path_access(full_path)
        return read_file_with_frontmatter(str(full_path))

    def read_file_raw(self, relative_path: str) -> str:
        """Read a file's raw content (frontmatter + body)."""
        full_path = self.vault_path / relative_path
        if not full_path.exists():
            raise FileNotFoundError(f"Vault file not found: {relative_path}")
        self._check_path_access(full_path)
        return full_path.read_text(encoding="utf-8")

    # ── Write operations ─────────────────────────────────────────────

    def write_file(
        self,
        relative_path: str,
        metadata: dict[str, Any],
        body: str,
    ) -> str:
        """Write a file with YAML frontmatter. Creates parent directories if needed.

        Returns the relative path of the written file.
        """
        full_path = self.vault_path / relative_path
        self._check_path_access(full_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        write_file_with_frontmatter(str(full_path), metadata, body)
        self._invalidate_graph()
        return relative_path

    def create_file(
        self,
        branch: str,
        name: str,
        metadata: dict[str, Any],
        body: str,
        update_index: bool = True,
    ) -> str:
        """Create a new file in a branch, optionally updating the branch index.

        Returns the relative path of the created file.
        """
        relative_path = f"{branch}/{name}.md" if not name.endswith(".md") else f"{branch}/{name}"
        self.write_file(relative_path, metadata, body)

        if update_index:
            self._update_branch_index(
                branch,
                name.removesuffix(".md"),
                metadata.get("description", metadata.get("name", name)),
            )

        return relative_path

    # ── Search operations ────────────────────────────────────────────

    def search(self, query: str, max_results: int = 20) -> list[dict[str, Any]]:
        """Full-text search across vault files.

        Returns list of {path, title, snippet} dicts.
        """
        results: list[dict[str, Any]] = []
        query_lower = query.lower()

        for md_file in self.vault_path.rglob("*.md"):
            if md_file.name.startswith("."):
                continue
            try:
                content = md_file.read_text(encoding="utf-8")
            except Exception:
                continue

            if query_lower in content.lower():
                rel_path = str(md_file.relative_to(self.vault_path)).replace("\\", "/")
                metadata, body = parse_frontmatter(content)

                # Extract snippet around first match
                idx = content.lower().index(query_lower)
                start = max(0, idx - 100)
                end = min(len(content), idx + len(query) + 100)
                snippet = content[start:end].strip()

                results.append({
                    "path": rel_path,
                    "title": metadata.get("name", md_file.stem),
                    "snippet": snippet,
                })

                if len(results) >= max_results:
                    break

        return results

    def list_branch(self, branch: str) -> list[dict[str, Any]]:
        """List all files in a branch directory.

        Returns list of {path, name, title, description} dicts.
        """
        branch_dir = self.vault_path / branch
        if not branch_dir.exists():
            return []

        files: list[dict[str, Any]] = []
        for md_file in sorted(branch_dir.glob("*.md")):
            rel_path = str(md_file.relative_to(self.vault_path)).replace("\\", "/")
            try:
                metadata, _ = read_file_with_frontmatter(str(md_file))
            except Exception:
                metadata = {}

            files.append({
                "path": rel_path,
                "name": md_file.stem,
                "title": metadata.get("name", md_file.stem),
                "description": metadata.get("description", ""),
            })

        return files

    # ── Link operations ──────────────────────────────────────────────

    def add_link(self, from_path: str, to_path: str, section: str | None = None) -> None:
        """Add a [[wikilink]] from one file to another."""
        full_from = self.vault_path / from_path
        if not full_from.exists():
            raise FileNotFoundError(f"Source file not found: {from_path}")

        # Determine the wikilink target (use shortest unique reference)
        to_stem = Path(to_path).stem
        content = full_from.read_text(encoding="utf-8")
        updated = add_wikilink(content, to_stem, section)
        full_from.write_text(updated, encoding="utf-8")
        self._invalidate_graph()

    def get_backlinks(self, relative_path: str) -> list[str]:
        """Find all files that link to the given file."""
        return self.graph.get_backlinks(relative_path)

    def get_links(self, relative_path: str) -> list[str]:
        """Get all files that this file links to."""
        return self.graph.get_neighbors(relative_path)

    # ── Context building (for memory navigator) ──────────────────────

    def get_context_window(self, max_tokens: int = 2000) -> str:
        """Read root + recent/important files, fit within token budget.

        This is a simple heuristic for the MVP. The MemoryNavigator
        replaces this with intelligent graph traversal.
        """
        content = self.read_root()
        # Rough token estimate: ~4 chars per token
        if len(content) // 4 > max_tokens:
            content = content[: max_tokens * 4]
        return content

    # ── Internal helpers ─────────────────────────────────────────────

    def _update_branch_index(self, branch: str, entry_name: str, description: str) -> None:
        """Add an entry to a branch's index file."""
        # Find the index file (conventions: branch-index.md, branch-log.md, or branch.md)
        index_candidates = [
            f"{branch}/{branch}-index.md",
            f"{branch}/{branch}-log.md",
            f"{branch}/{branch}.md",
        ]

        index_path = None
        for candidate in index_candidates:
            if (self.vault_path / candidate).exists():
                index_path = candidate
                break

        if not index_path:
            # Create a default index
            index_path = f"{branch}/{branch}-index.md"
            self.write_file(
                index_path,
                {"name": f"{branch.title()} Index", "description": f"Index of {branch} entries"},
                f"# {branch.title()}\n\n",
            )

        full_index = self.vault_path / index_path
        content = full_index.read_text(encoding="utf-8")
        link_line = f"- [[{entry_name}]] — {description}"

        if f"[[{entry_name}]]" not in content:
            content = f"{content.rstrip()}\n{link_line}\n"
            full_index.write_text(content, encoding="utf-8")

    def _check_path_access(self, full_path: Path) -> None:
        """Ensure the path is within the vault directory (prevent directory traversal)."""
        try:
            full_path.resolve().relative_to(self.vault_path.resolve())
        except ValueError:
            raise PermissionError(f"Path is outside vault: {full_path}")

    def _invalidate_graph(self) -> None:
        """Mark the graph as stale so it gets rebuilt on next access."""
        self._graph = None

"""Append-only audit logger — traces every tool call to the shared vault."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from axon.vault.frontmatter import write_file_with_frontmatter


# Branch name used for audit logs inside the shared vault
AUDIT_BRANCH = "audit"


class AuditLogger:
    """Writes append-only audit entries to shared/audit/{date}/{timestamp}-{action}.md.

    The audit branch is protected — only this logger can write to it.
    """

    def __init__(self, vault_path: str | Path):
        self.vault_path = Path(vault_path)
        self.audit_dir = self.vault_path / AUDIT_BRANCH

    def log(
        self,
        agent_id: str,
        action: str,
        tool: str,
        conversation_id: str = "",
        org_id: str = "",
        context: str = "",
        arguments: str = "",
        result_summary: str = "",
    ) -> str:
        """Write an audit entry. Returns the relative path of the entry."""
        ts = datetime.utcnow()
        date_str = ts.strftime("%Y-%m-%d")
        ts_str = ts.strftime("%Y%m%d%H%M%S%f")[:18]  # trim microseconds to 4 digits

        # Slugify the action for the filename
        action_slug = action.lower().replace(" ", "-").replace("_", "-")[:30]
        filename = f"{ts_str}-{action_slug}.md"

        day_dir = self.audit_dir / date_str
        day_dir.mkdir(parents=True, exist_ok=True)

        metadata: dict[str, Any] = {
            "timestamp": ts.isoformat() + "Z",
            "agent_id": agent_id,
            "action": action,
            "tool": tool,
            "conversation_id": conversation_id,
            "org_id": org_id,
            "type": "audit",
        }

        body_parts = []
        if context:
            body_parts.append(f"## Context\n{context}")
        if arguments:
            # Truncate very long arguments
            args_display = arguments[:2000]
            if len(arguments) > 2000:
                args_display += "\n... (truncated)"
            body_parts.append(f"## Arguments\n```json\n{args_display}\n```")
        if result_summary:
            result_display = result_summary[:1000]
            if len(result_summary) > 1000:
                result_display += "\n... (truncated)"
            body_parts.append(f"## Result\n{result_display}")

        body = "\n\n".join(body_parts) if body_parts else ""

        file_path = day_dir / filename
        write_file_with_frontmatter(str(file_path), metadata, body)

        return f"{AUDIT_BRANCH}/{date_str}/{filename}"

    def list_entries(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        agent_id: str | None = None,
        action: str | None = None,
        tool: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List audit entries with optional filters. Returns newest first."""
        from axon.vault.frontmatter import read_file_with_frontmatter

        entries: list[dict[str, Any]] = []

        if not self.audit_dir.exists():
            return []

        # Iterate date directories in reverse (newest first)
        date_dirs = sorted(self.audit_dir.iterdir(), reverse=True)
        for day_dir in date_dirs:
            if not day_dir.is_dir():
                continue

            day_name = day_dir.name
            # Apply date filters
            if date_from and day_name < date_from:
                continue
            if date_to and day_name > date_to:
                continue

            for md_file in sorted(day_dir.glob("*.md"), reverse=True):
                try:
                    metadata, body = read_file_with_frontmatter(str(md_file))
                except Exception:
                    continue

                # Apply filters
                if agent_id and metadata.get("agent_id") != agent_id:
                    continue
                if action and metadata.get("action") != action:
                    continue
                if tool and metadata.get("tool") != tool:
                    continue

                rel_path = f"{AUDIT_BRANCH}/{day_name}/{md_file.name}"
                entries.append({**metadata, "path": rel_path, "body": body})

        # Paginate
        return entries[offset : offset + limit]

    def count_entries(self) -> int:
        """Quick count of total audit entries."""
        if not self.audit_dir.exists():
            return 0
        count = 0
        for day_dir in self.audit_dir.iterdir():
            if day_dir.is_dir():
                count += len(list(day_dir.glob("*.md")))
        return count


def is_audit_branch(relative_path: str) -> bool:
    """Check if a relative path is within the audit branch."""
    clean = relative_path.replace("\\", "/").strip("/")
    return clean.startswith(f"{AUDIT_BRANCH}/") or clean == AUDIT_BRANCH

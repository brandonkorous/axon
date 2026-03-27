"""Contact lookup — search the shared vault contacts directory."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from axon.vault.vault import VaultManager


async def lookup_contact(vault: "VaultManager", query: str) -> str:
    """Search contacts directory in shared vault and return formatted results."""
    query = query.lower().strip()
    if not query:
        return "Error: 'query' is required."

    contacts_dir = Path(vault.vault_path) / "contacts"
    if not contacts_dir.exists():
        return "No contacts directory found. Ask the user to add contacts."

    matches = []
    for md_file in contacts_dir.glob("*.md"):
        if md_file.name.endswith("-index.md"):
            continue
        try:
            meta, body = vault.read_file(f"contacts/{md_file.name}")
            searchable = " ".join(str(v).lower() for v in meta.values()) + " " + body.lower()
            if query in searchable:
                matches.append(_format_contact(meta, body))
        except Exception:
            continue

    if not matches:
        return f"No contacts found matching '{query}'."
    return f"Found {len(matches)} contact(s):\n\n" + "\n---\n".join(matches)


def _format_contact(meta: dict, body: str) -> str:
    """Format a contact for display."""
    lines = []
    if meta.get("name"):
        lines.append(f"**Name:** {meta['name']}")
    if meta.get("email"):
        lines.append(f"**Email:** {meta['email']}")
    if meta.get("discord_id"):
        lines.append(f"**Discord:** {meta['discord_id']}")
    if meta.get("phone"):
        lines.append(f"**Phone:** {meta['phone']}")
    if meta.get("role"):
        lines.append(f"**Role:** {meta['role']}")
    if meta.get("company"):
        lines.append(f"**Company:** {meta['company']}")
    if body.strip():
        lines.append(f"**Notes:** {body.strip()[:200]}")
    return "\n".join(lines)

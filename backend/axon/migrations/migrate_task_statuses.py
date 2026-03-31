"""Migrate task statuses to simplified v2 values."""

from __future__ import annotations

import argparse
import glob
from datetime import datetime, timezone

from axon.vault.frontmatter import read_file_with_frontmatter, write_file_with_frontmatter

STATUS_MAP: dict[str, str] = {
    "planned": "pending",
    "awaiting_approval": "done",
    "approved": "done",
    "declined": "blocked",
    "executing": "in_progress",
    "failed": "blocked",
    "closed": "accepted",
    "send failed": "blocked",
    "send_failed": "blocked",
}

UNCHANGED = {"pending", "in_progress", "done", "blocked", "accepted"}


def migrate_tasks(orgs_dir: str, *, apply: bool = False) -> None:
    pattern = f"{orgs_dir}/*/vaults/shared/tasks/*.md"
    files = sorted(glob.glob(pattern, recursive=False))

    if not files:
        print(f"No task files found matching: {pattern}")
        return

    migrated, skipped = 0, 0

    for path in files:
        meta, body = read_file_with_frontmatter(path)
        old_status = meta.get("status", "")

        if old_status not in STATUS_MAP:
            skipped += 1
            continue

        new_status = STATUS_MAP[old_status]
        meta["status"] = new_status

        responses = meta.get("responses", []) or []
        responses.append({
            "from": "system",
            "content": f"Status migrated from '{old_status}' to '{new_status}' during v2 migration",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "migration",
        })
        meta["responses"] = responses

        label = "Migrated" if apply else "Would migrate"
        print(f"  {label}: {path}  [{old_status} -> {new_status}]")

        if apply:
            write_file_with_frontmatter(path, meta, body)

        migrated += 1

    mode = "APPLIED" if apply else "DRY RUN"
    print(f"\n[{mode}] {migrated} migrated, {skipped} unchanged, {len(files)} total")
    if not apply and migrated:
        print("Re-run with --apply to write changes.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate task statuses to v2")
    parser.add_argument(
        "orgs_dir", nargs="?", default="orgs",
        help="Path to the orgs directory (default: orgs)",
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Actually write changes (default is dry-run)",
    )
    args = parser.parse_args()
    migrate_tasks(args.orgs_dir, apply=args.apply)


if __name__ == "__main__":
    main()

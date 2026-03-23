"""Issue management routes — list, create, update, comment on issues."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import axon.registry as registry

router = APIRouter()
org_router = APIRouter()


class IssueCreate(BaseModel):
    title: str
    description: str = ""
    assignee: str = ""
    priority: str = "p2"
    labels: list[str] = []
    parent_issue: str = ""


class IssueUpdate(BaseModel):
    status: str | None = None
    assignee: str | None = None
    priority: str | None = None


class IssueCommentCreate(BaseModel):
    content: str
    author: str = "user"


# ── Shared helpers ────────────────────────────────────────────────────


def _get_shared_vault(org_id: str):
    org = registry.get_org(org_id)
    if not org:
        raise HTTPException(404, f"Organization not found: {org_id}")
    if not org.shared_vault:
        raise HTTPException(404, f"No shared vault for org: {org_id}")
    return org.shared_vault


def _parse_issues(vault) -> list[dict[str, Any]]:
    """Read all issue files from the shared vault."""
    issues_dir = Path(vault.vault_path) / "issues"
    if not issues_dir.exists():
        return []

    issues = []
    for md_file in sorted(issues_dir.glob("*.md"), reverse=True):
        if md_file.name.endswith("-index.md"):
            continue
        try:
            metadata, body = vault.read_file(f"issues/{md_file.name}")
            metadata["path"] = f"issues/{md_file.name}"
            metadata["body"] = body

            # Count comments
            issue_dir = issues_dir / md_file.name.removesuffix(".md") / "comments"
            metadata["comment_count"] = len(list(issue_dir.glob("*.md"))) if issue_dir.exists() else 0

            issues.append(metadata)
        except Exception:
            continue
    return issues


def _list_issues(
    org_id: str,
    status: str | None,
    assignee: str | None,
    priority: str | None,
    label: str | None,
):
    vault = _get_shared_vault(org_id)
    issues = _parse_issues(vault)

    if status:
        issues = [i for i in issues if i.get("status") == status]
    if assignee:
        issues = [i for i in issues if i.get("assignee") == assignee]
    if priority:
        issues = [i for i in issues if i.get("priority") == priority]
    if label:
        def has_label(issue):
            labels = issue.get("labels", [])
            if isinstance(labels, str):
                labels = [l.strip() for l in labels.split(",")]
            return label in labels
        issues = [i for i in issues if has_label(i)]

    return issues


def _get_issue(org_id: str, issue_path: str):
    vault = _get_shared_vault(org_id)
    try:
        metadata, body = vault.read_file(issue_path)
    except FileNotFoundError:
        raise HTTPException(404, f"Issue not found: {issue_path}")

    # Load comments
    issue_dir = Path(vault.vault_path) / issue_path.removesuffix(".md") / "comments"
    comments = []
    if issue_dir.exists():
        for comment_file in sorted(issue_dir.glob("*.md")):
            try:
                c_meta, c_body = vault.read_file(
                    str(Path(issue_path.removesuffix(".md")) / "comments" / comment_file.name)
                )
                comments.append({**c_meta, "body": c_body})
            except Exception:
                continue

    return {**metadata, "path": issue_path, "body": body, "comments": comments}


def _create_issue(org_id: str, data: IssueCreate):
    from axon.agents.shared_tools import SharedVaultToolExecutor, _slugify

    vault = _get_shared_vault(org_id)

    # Get next ID
    counter_path = Path(vault.vault_path) / "issues" / ".next_id"
    counter_path.parent.mkdir(parents=True, exist_ok=True)
    if counter_path.exists():
        issue_id = int(counter_path.read_text().strip())
    else:
        issue_id = 1
    counter_path.write_text(str(issue_id + 1), encoding="utf-8")

    slug = _slugify(data.title)
    path = f"issues/{issue_id}-{slug}.md"

    metadata = {
        "name": data.title,
        "type": "issue",
        "id": issue_id,
        "assignee": data.assignee,
        "status": "open",
        "priority": data.priority,
        "labels": data.labels,
        "parent_issue": data.parent_issue,
        "created_by": "user",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }

    content = f"# #{issue_id}: {data.title}\n\n{data.description}"
    vault.write_file(path, metadata, content)
    vault._update_branch_index("issues", f"{issue_id}-{slug}", data.title)

    return {**metadata, "path": path, "body": content, "comments": []}


def _update_issue(org_id: str, issue_path: str, data: IssueUpdate):
    vault = _get_shared_vault(org_id)
    try:
        metadata, body = vault.read_file(issue_path)
    except FileNotFoundError:
        raise HTTPException(404, f"Issue not found: {issue_path}")

    if data.status is not None:
        metadata["status"] = data.status
    if data.assignee is not None:
        metadata["assignee"] = data.assignee
    if data.priority is not None:
        metadata["priority"] = data.priority

    metadata["updated_at"] = datetime.utcnow().isoformat() + "Z"
    vault.write_file(issue_path, metadata, body)

    return {**metadata, "path": issue_path, "body": body}


def _add_comment(org_id: str, issue_path: str, data: IssueCommentCreate):
    vault = _get_shared_vault(org_id)

    # Verify issue exists
    try:
        vault.read_file(issue_path)
    except FileNotFoundError:
        raise HTTPException(404, f"Issue not found: {issue_path}")

    ts = datetime.utcnow()
    ts_str = ts.strftime("%Y%m%d%H%M%S")
    issue_dir = issue_path.removesuffix(".md")
    comment_path = f"{issue_dir}/comments/{ts_str}.md"

    metadata = {
        "author": data.author,
        "type": "comment",
        "created_at": ts.isoformat() + "Z",
    }

    vault.write_file(comment_path, metadata, data.content)
    return {**metadata, "body": data.content, "path": comment_path}


# ── Org-scoped routes ─────────────────────────────────────────────────


@org_router.get("")
async def list_issues_org(
    org_id: str,
    status: str | None = None,
    assignee: str | None = None,
    priority: str | None = None,
    label: str | None = None,
):
    return _list_issues(org_id, status, assignee, priority, label)


@org_router.post("")
async def create_issue_org(org_id: str, data: IssueCreate):
    return _create_issue(org_id, data)


# Comments route MUST come before the catch-all {issue_path:path} routes
@org_router.post("/{issue_id}/comments")
async def add_comment_org(org_id: str, issue_id: str, data: IssueCommentCreate):
    vault = _get_shared_vault(org_id)
    issues_dir = Path(vault.vault_path) / "issues"
    matches = list(issues_dir.glob(f"{issue_id}-*.md"))
    if not matches:
        raise HTTPException(404, f"Issue #{issue_id} not found")
    issue_path = f"issues/{matches[0].name}"
    return _add_comment(org_id, issue_path, data)


@org_router.get("/{issue_path:path}")
async def get_issue_org(org_id: str, issue_path: str):
    if not issue_path.startswith("issues/"):
        issue_path = f"issues/{issue_path}"
    return _get_issue(org_id, issue_path)


@org_router.put("/{issue_path:path}")
async def update_issue_org(org_id: str, issue_path: str, data: IssueUpdate):
    if not issue_path.startswith("issues/"):
        issue_path = f"issues/{issue_path}"
    return _update_issue(org_id, issue_path, data)


# ── Legacy routes ─────────────────────────────────────────────────────


@router.get("")
async def list_issues_legacy(
    status: str | None = None,
    assignee: str | None = None,
    priority: str | None = None,
    label: str | None = None,
):
    return _list_issues(registry.default_org_id, status, assignee, priority, label)


@router.post("")
async def create_issue_legacy(data: IssueCreate):
    return _create_issue(registry.default_org_id, data)


@router.post("/{issue_id}/comments")
async def add_comment_legacy(issue_id: str, data: IssueCommentCreate):
    vault = _get_shared_vault(registry.default_org_id)
    issues_dir = Path(vault.vault_path) / "issues"
    matches = list(issues_dir.glob(f"{issue_id}-*.md"))
    if not matches:
        raise HTTPException(404, f"Issue #{issue_id} not found")
    issue_path = f"issues/{matches[0].name}"
    return _add_comment(registry.default_org_id, issue_path, data)


@router.get("/{issue_path:path}")
async def get_issue_legacy(issue_path: str):
    if not issue_path.startswith("issues/"):
        issue_path = f"issues/{issue_path}"
    return _get_issue(registry.default_org_id, issue_path)


@router.put("/{issue_path:path}")
async def update_issue_legacy(issue_path: str, data: IssueUpdate):
    if not issue_path.startswith("issues/"):
        issue_path = f"issues/{issue_path}"
    return _update_issue(registry.default_org_id, issue_path, data)

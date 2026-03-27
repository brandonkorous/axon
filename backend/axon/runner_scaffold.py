"""Scaffold a self-contained runner directory for a worker agent."""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path

from axon.worker_types import WorkerType

logger = logging.getLogger(__name__)

# Template lives alongside this module
_TEMPLATE_DIR = Path(__file__).parent / "runner_template"

# Host service lives in the axon package root
_HOST_SERVICE = Path(__file__).parent / "runner_host.js"

# Files copied for every runner
_COMMON_FILES = ("runner.js", "base_bridge.js")

# Bridge files per worker type
_BRIDGE_FILES: dict[str, tuple[str, ...]] = {
    WorkerType.CODE: ("code_bridge.js", "claude_bridge.js", "claude_util.js"),
    WorkerType.DOCUMENTS: ("documents_bridge.js", "doc_renderers.js", "claude_util.js"),
    WorkerType.EMAIL: ("email_bridge.js", "claude_util.js"),
    WorkerType.IMAGES: ("images_bridge.js", "claude_util.js"),
    WorkerType.BROWSER: ("browser_bridge.js", "claude_util.js"),
    WorkerType.SHELL: ("shell_bridge.js",),
}


def scaffold_runner(
    runners_dir: Path,
    agent_id: str,
    axon_url: str,
    org_id: str,
    codebase_path: str,
    worker_type: str = WorkerType.CODE,
    type_config: dict | None = None,
    sandbox: dict | None = None,
) -> Path:
    """Create a self-contained runner app for a worker agent.

    Copies template files into ``runners_dir / agent_id`` and writes
    a config.json with the provided values. Also ensures the host
    runner service and start scripts exist in the orgs root.

    Returns the path to the created runner directory.
    """
    runner_dir = runners_dir / agent_id
    if runner_dir.exists():
        raise FileExistsError(f"Runner directory already exists: {runner_dir}")

    runner_dir.mkdir(parents=True)

    # Copy common + bridge-specific files
    copy_files = list(_COMMON_FILES) + list(_BRIDGE_FILES.get(worker_type, _BRIDGE_FILES[WorkerType.CODE]))
    for filename in copy_files:
        src = _TEMPLATE_DIR / filename
        if src.exists():
            shutil.copy2(src, runner_dir / filename)

    # Write config.json
    config = {
        "axon_url": axon_url,
        "org_id": org_id,
        "agent_id": agent_id,
        "codebase": codebase_path,
        "worker_type": worker_type,
        **({"type_config": type_config} if type_config else {}),
        **({"sandbox": sandbox} if sandbox else {}),
    }
    config_path = runner_dir / "config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
        f.write("\n")

    # Write package.json for workers that need npm dependencies
    if worker_type == WorkerType.DOCUMENTS:
        pkg = {"private": True, "dependencies": {"pdfkit": "^0.16", "docx": "^9"}}
        pkg_path = runner_dir / "package.json"
        with open(pkg_path, "w", encoding="utf-8") as f:
            json.dump(pkg, f, indent=2)
            f.write("\n")

    # Ensure host runner service exists in the orgs root
    orgs_root = runners_dir.parent.parent  # runners_dir = orgs/{org}/runners
    scaffold_runner_host(orgs_root)

    logger.info("Runner scaffolded: %s", runner_dir)
    return runner_dir


def scaffold_runner_host(orgs_root: Path) -> None:
    """Ensure runner_host.js and start scripts exist in the orgs root.

    Safe to call multiple times — always updates runner_host.js
    (in case of upgrades) but preserves existing start scripts.
    """
    host_dest = orgs_root / "runner_host.js"

    # Always update runner_host.js (in case of upgrades)
    if _HOST_SERVICE.exists():
        shutil.copy2(_HOST_SERVICE, host_dest)

    # Windows start script
    cmd_path = orgs_root / "start-runners.cmd"
    if not cmd_path.exists():
        cmd_path.write_text(
            '@echo off\n'
            'title Axon Runner Host\n'
            'echo Starting Axon Runner Host...\n'
            'echo Watching: %~dp0\n'
            'echo.\n'
            'node "%~dp0runner_host.js" "%~dp0."\n'
            'pause\n',
            encoding="utf-8",
        )

    # Unix start script (Mac / Linux)
    sh_path = orgs_root / "start-runners.sh"
    if not sh_path.exists():
        sh_path.write_text(
            '#!/bin/bash\n'
            'DIR="$(cd "$(dirname "$0")" && pwd)"\n'
            'echo "Starting Axon Runner Host..."\n'
            'echo "Watching: $DIR"\n'
            'node "$DIR/runner_host.js" "$DIR"\n',
            encoding="utf-8",
        )
        try:
            sh_path.chmod(0o755)
        except OSError:
            pass  # Windows doesn't support chmod

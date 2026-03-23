"""Bridge to Claude Code CLI — plan generation and execution."""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import tempfile

logger = logging.getLogger(__name__)


def _claude_cmd() -> str:
    """Resolve the Claude CLI command for the current platform."""
    # On Windows, .cmd/.bat wrappers need shell=True with subprocess_exec,
    # so we resolve to the full path instead.
    cmd = shutil.which("claude")
    if cmd:
        return cmd
    raise FileNotFoundError(
        "Claude CLI not found. Install it with: npm install -g @anthropic-ai/claude-code"
    )


async def _run_claude(codebase: str, prompt: str, extra_args: list[str] | None = None) -> tuple[bytes, bytes, int]:
    """Run Claude Code CLI with the given prompt.

    Writes the prompt to a temp file and pipes it via stdin to avoid
    Windows cmd.exe mangling newlines in command-line arguments.
    """
    prompt_file = None
    try:
        # Write prompt to temp file — avoids cmd.exe arg length/newline issues
        fd, prompt_file = tempfile.mkstemp(suffix=".txt", prefix="axon-prompt-")
        os.write(fd, prompt.encode("utf-8"))
        os.close(fd)

        args = [_claude_cmd(), "--print"]
        if extra_args:
            args.extend(extra_args)

        logger.debug("Claude args: %s, prompt file: %s (%d bytes)",
                      args, prompt_file, len(prompt))

        # Pipe prompt via stdin (reading from the temp file)
        with open(prompt_file, "rb") as f:
            proc = await asyncio.create_subprocess_exec(
                *args,
                cwd=codebase,
                stdin=f,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

        return stdout, stderr, proc.returncode
    finally:
        if prompt_file and os.path.exists(prompt_file):
            os.unlink(prompt_file)


async def generate_plan(codebase: str, task_description: str) -> str:
    """Run Claude Code in plan-only mode. Returns the plan text."""
    prompt = (
        "You are acting as an Enterprise Architect. "
        "Create a detailed implementation plan for the following task. "
        "Do NOT execute any changes — only output the plan.\n\n"
        f"Task: {task_description}"
    )

    logger.info("Generating plan for: %s", task_description[:80])
    stdout, stderr, returncode = await _run_claude(codebase, prompt)

    if returncode != 0:
        error = stderr.decode().strip()
        logger.error("Claude Code plan failed: %s", error)
        raise RuntimeError(f"Claude Code plan failed: {error}")

    plan = stdout.decode().strip()
    logger.info("Plan generated (%d chars)", len(plan))
    return plan


async def execute_plan(codebase: str, plan: str) -> dict:
    """Run Claude Code to execute an approved plan. Returns result dict."""
    prompt = (
        "Execute the following approved implementation plan exactly as specified. "
        "Make all the code changes described.\n\n"
        f"Plan:\n{plan}"
    )

    logger.info("Executing approved plan (%d chars)", len(plan))
    stdout, stderr, returncode = await _run_claude(
        codebase, prompt, extra_args=["--dangerously-skip-permissions"],
    )

    # Capture git diff for the result
    diff_proc = await asyncio.create_subprocess_exec(
        "git", "diff", "--stat",
        cwd=codebase,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    diff_out, _ = await diff_proc.communicate()

    return {
        "success": returncode == 0,
        "output": stdout.decode().strip(),
        "diff": diff_out.decode().strip(),
        "error": stderr.decode().strip() if returncode != 0 else None,
    }

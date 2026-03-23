"""Axon Worker Runner — self-contained, zero-dependency agent runner.

Reads configuration from config.json in the same directory.
Controlled via state.json written by the Axon backend process manager.
"""

import asyncio
import json
import logging
import os
import sys
import urllib.request
import urllib.error

from claude_bridge import generate_plan, execute_plan

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("runner")

POLL_INTERVAL = 15  # seconds
RUNNER_DIR = os.path.dirname(os.path.abspath(__file__))


# ── HTTP helpers (stdlib, no external deps) ───────────────────────

def _http_get(url: str) -> dict:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def _http_post(url: str, data: dict) -> tuple[int, dict]:
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()}


# ── Config & state ────────────────────────────────────────────────

def _load_config() -> dict:
    config_path = os.path.join(RUNNER_DIR, "config.json")
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def _read_state() -> str:
    """Read desired state from state.json. Returns 'running' if missing."""
    state_path = os.path.join(RUNNER_DIR, "state.json")
    try:
        with open(state_path, encoding="utf-8") as f:
            return json.load(f).get("state", "running")
    except (FileNotFoundError, json.JSONDecodeError):
        return "running"


def _write_pid():
    pid_path = os.path.join(RUNNER_DIR, "runner.pid")
    with open(pid_path, "w") as f:
        f.write(str(os.getpid()))


def _remove_pid():
    pid_path = os.path.join(RUNNER_DIR, "runner.pid")
    try:
        os.unlink(pid_path)
    except FileNotFoundError:
        pass


# ── Runner ────────────────────────────────────────────────────────

class Runner:
    def __init__(self, config: dict):
        agent_id = config["agent_id"]
        base_url = config["axon_url"].rstrip("/")
        org_id = config["org_id"]
        self.base = f"{base_url}/api/orgs/{org_id}/external/{agent_id}"
        self.codebase = config["codebase"]
        self._busy = False

    async def run(self):
        logger.info("Runner started — polling %s every %ds", self.base, POLL_INTERVAL)
        logger.info("Codebase: %s", self.codebase)

        while True:
            state = _read_state()
            if state == "stop":
                logger.info("Stop signal received — shutting down")
                break
            if state == "paused":
                await asyncio.sleep(POLL_INTERVAL)
                continue

            try:
                await self._tick()
            except urllib.error.URLError:
                logger.warning("Cannot reach Axon — retrying in %ds", POLL_INTERVAL)
            except Exception:
                logger.exception("Unexpected error in tick")

            await asyncio.sleep(POLL_INTERVAL)

    async def _tick(self):
        data = await asyncio.to_thread(_http_get, f"{self.base}/tasks")

        for task in data.get("tasks", []):
            status = task.get("status")
            path = task.get("path")
            if not path:
                continue
            if status == "pending":
                await self._handle_pending(task)
            elif status == "approved":
                await self._handle_approved(task)

    async def _handle_pending(self, task: dict):
        if self._busy:
            return
        self._busy = True
        try:
            path = task["path"]
            name = task.get("name", path)
            body = task.get("body", "")
            logger.info("New task: %s", name)

            try:
                plan = await generate_plan(self.codebase, f"{name}\n\n{body}")
            except Exception as e:
                logger.error("Plan generation failed: %s", e)
                await self._submit_result(path, False, str(e), error=str(e))
                return

            logger.info("Submitting plan for approval: %s", path)
            status_code, resp = await asyncio.to_thread(
                _http_post,
                f"{self.base}/tasks/{path}/plan",
                {"plan": plan, "files_affected": []},
            )
            if status_code == 200:
                logger.info("Plan submitted — awaiting user approval")
            else:
                logger.error("Plan submission failed: %s", resp)
        finally:
            self._busy = False

    async def _handle_approved(self, task: dict):
        if self._busy:
            return
        self._busy = True
        try:
            path = task["path"]
            plan = task.get("plan_content", "")
            name = task.get("name", path)

            if not plan:
                logger.warning("Approved task has no plan content: %s", path)
                return

            logger.info("Executing approved plan: %s", name)
            try:
                result = await execute_plan(self.codebase, plan)
            except Exception as e:
                logger.exception("Execution failed")
                await self._submit_result(path, False, str(e), error=str(e))
                return

            await self._submit_result(
                path, result["success"], result["output"][:2000],
                diff=result.get("diff", ""), error=result.get("error"),
            )
            status = "done" if result["success"] else "failed"
            logger.info("Task %s: %s", status, name)
        finally:
            self._busy = False

    async def _submit_result(
        self, path: str, success: bool, summary: str,
        diff: str = "", error: str | None = None,
    ):
        status_code, resp = await asyncio.to_thread(
            _http_post,
            f"{self.base}/tasks/{path}/result",
            {"success": success, "summary": summary, "diff": diff, "error": error},
        )
        if status_code != 200:
            logger.error("Result submission failed: %s", resp)


def main():
    config = _load_config()
    _write_pid()
    runner = Runner(config)
    try:
        asyncio.run(runner.run())
    except KeyboardInterrupt:
        logger.info("Shutting down")
    finally:
        _remove_pid()


if __name__ == "__main__":
    main()

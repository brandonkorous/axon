"""EA Runner — host-side bridge between Axon and Claude Code.

Usage:
    python -m runner \
        --axon-url http://localhost:8000 \
        --org employment-networks \
        --agent enterprise_architect \
        --codebase G:/code/splits.network
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

import httpx

from runner.claude_bridge import execute_plan, generate_plan

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

POLL_INTERVAL = 15  # seconds


class EARunner:
    def __init__(self, axon_url: str, org_id: str, agent_id: str, codebase: str):
        self.base = f"{axon_url.rstrip('/')}/api/orgs/{org_id}/external/{agent_id}"
        self.codebase = codebase
        self.agent_id = agent_id
        self._lock = asyncio.Lock()  # One task at a time
        self._client = httpx.AsyncClient(timeout=300)

    async def run(self):
        logger.info("EA Runner started — polling %s every %ds", self.base, POLL_INTERVAL)
        logger.info("Codebase: %s", self.codebase)

        while True:
            try:
                await self._tick()
            except httpx.ConnectError:
                logger.warning("Cannot reach Axon — retrying in %ds", POLL_INTERVAL)
            except Exception:
                logger.exception("Unexpected error in tick")
            await asyncio.sleep(POLL_INTERVAL)

    async def _tick(self):
        resp = await self._client.get(f"{self.base}/tasks")
        resp.raise_for_status()
        data = resp.json()

        # Process shared vault tasks (these have the approval flow)
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
        if self._lock.locked():
            return  # Already working on something

        async with self._lock:
            path = task["path"]
            name = task.get("name", path)
            body = task.get("body", "")
            logger.info("New task: %s", name)

            try:
                plan = await generate_plan(self.codebase, f"{name}\n\n{body}")
            except RuntimeError as e:
                logger.error("Plan generation failed: %s", e)
                await self._submit_result(path, False, str(e), error=str(e))
                return

            # Submit plan for approval
            logger.info("Submitting plan for approval: %s", path)
            resp = await self._client.post(
                f"{self.base}/tasks/{path}/plan",
                json={"plan": plan, "files_affected": []},
            )
            if resp.status_code == 200:
                logger.info("Plan submitted — awaiting user approval")
            else:
                logger.error("Plan submission failed: %s", resp.text)

    async def _handle_approved(self, task: dict):
        if self._lock.locked():
            return

        async with self._lock:
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
                path,
                result["success"],
                result["output"][:2000],
                diff=result.get("diff", ""),
                error=result.get("error"),
            )
            status = "done" if result["success"] else "failed"
            logger.info("Task %s: %s", status, name)

    async def _submit_result(self, path: str, success: bool, summary: str,
                             diff: str = "", error: str | None = None):
        resp = await self._client.post(
            f"{self.base}/tasks/{path}/result",
            json={
                "success": success,
                "summary": summary,
                "diff": diff,
                "error": error,
            },
        )
        if resp.status_code != 200:
            logger.error("Result submission failed: %s", resp.text)

    async def close(self):
        await self._client.aclose()


def main():
    parser = argparse.ArgumentParser(description="Axon EA Runner — host-side coding agent")
    parser.add_argument("--axon-url", default="http://localhost:8000", help="Axon backend URL")
    parser.add_argument("--org", required=True, help="Organization ID")
    parser.add_argument("--agent", default="enterprise_architect", help="Agent ID")
    parser.add_argument("--codebase", required=True, help="Path to the codebase")
    args = parser.parse_args()

    runner = EARunner(args.axon_url, args.org, args.agent, args.codebase)

    try:
        asyncio.run(runner.run())
    except KeyboardInterrupt:
        logger.info("Shutting down")
        asyncio.run(runner.close())


if __name__ == "__main__":
    main()

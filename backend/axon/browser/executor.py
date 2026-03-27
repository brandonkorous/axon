"""BrowserToolExecutor — handles browser_* tool calls for agents."""

from __future__ import annotations

import json
import logging

from axon.browser.config import BrowserConfig
from axon.browser.manager import browser_manager

logger = logging.getLogger(__name__)


class BrowserToolExecutor:
    """Routes browser tool calls to the appropriate Playwright actions."""

    def __init__(self, config: BrowserConfig | None = None) -> None:
        self._config = config or BrowserConfig()

    async def execute(self, tool_name: str, arguments: str, agent_id: str = "") -> str:
        """Execute a browser tool call."""
        if not browser_manager.available:
            return json.dumps({
                "error": "Browser tools unavailable. Install playwright: pip install playwright && playwright install chromium",
            })

        args = json.loads(arguments) if arguments else {}

        try:
            session = await browser_manager.get_session(agent_id, self._config)
        except RuntimeError as e:
            return json.dumps({"error": str(e)})

        if tool_name == "browser_navigate":
            return await session.navigate(args["url"], args.get("wait_for", ""))
        elif tool_name == "browser_extract":
            return await session.extract(args["selector"])
        elif tool_name == "browser_screenshot":
            return await session.screenshot(args.get("full_page", False))
        elif tool_name == "browser_click":
            return await session.click(args["selector"])
        elif tool_name == "browser_fill":
            return await session.fill(args["selector"], args["value"])
        else:
            return json.dumps({"error": f"Unknown browser tool: {tool_name}"})

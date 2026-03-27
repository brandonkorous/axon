"""BrowserManager — Playwright lifecycle and session pool for agents."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
from typing import Any

from axon.browser.config import BrowserConfig
from axon.browser.extractor import extract_page_content

logger = logging.getLogger(__name__)


class BrowserSession:
    """A single browser session (page) for an agent."""

    def __init__(self, page: Any, config: BrowserConfig) -> None:
        self._page = page
        self._config = config

    @property
    def page(self) -> Any:
        return self._page

    async def navigate(self, url: str, wait_for: str = "") -> str:
        """Navigate to URL and return extracted content."""
        if not _is_allowed(url, self._config):
            return json.dumps({"error": f"Domain blocked: {url}"})

        try:
            await self._page.goto(url, timeout=self._config.timeout_seconds * 1000)
            if wait_for:
                await self._page.wait_for_selector(wait_for, timeout=10000)
            else:
                await self._page.wait_for_load_state("domcontentloaded")

            html = await self._page.content()
            content = extract_page_content(html, self._config.max_content_length)
            title = await self._page.title()

            return json.dumps({
                "title": title,
                "url": self._page.url,
                "content": content,
            })
        except Exception as e:
            return json.dumps({"error": f"Navigation failed: {e}"})

    async def extract(self, selector: str) -> str:
        """Extract text content matching a CSS selector."""
        try:
            elements = await self._page.query_selector_all(selector)
            texts = []
            for el in elements:
                text = await el.text_content()
                if text and text.strip():
                    texts.append(text.strip())
            return json.dumps({"selector": selector, "results": texts, "count": len(texts)})
        except Exception as e:
            return json.dumps({"error": f"Extraction failed: {e}"})

    async def screenshot(self, full_page: bool = False) -> str:
        """Take a screenshot and return as base64."""
        try:
            data = await self._page.screenshot(full_page=full_page)
            b64 = base64.b64encode(data).decode("utf-8")
            return json.dumps({"screenshot": b64, "format": "png"})
        except Exception as e:
            return json.dumps({"error": f"Screenshot failed: {e}"})

    async def click(self, selector: str) -> str:
        """Click an element."""
        try:
            await self._page.click(selector, timeout=10000)
            await self._page.wait_for_load_state("domcontentloaded")
            return json.dumps({"status": "clicked", "selector": selector, "url": self._page.url})
        except Exception as e:
            return json.dumps({"error": f"Click failed: {e}"})

    async def fill(self, selector: str, value: str) -> str:
        """Fill a form field."""
        try:
            await self._page.fill(selector, value, timeout=10000)
            return json.dumps({"status": "filled", "selector": selector})
        except Exception as e:
            return json.dumps({"error": f"Fill failed: {e}"})

    async def close(self) -> None:
        try:
            await self._page.close()
        except Exception:
            pass


class BrowserManager:
    """Manages Playwright browser instances and agent sessions."""

    def __init__(self) -> None:
        self._browser: Any | None = None
        self._sessions: dict[str, BrowserSession] = {}  # agent_id → session
        self._available: bool | None = None

    async def _ensure_browser(self) -> Any:
        """Lazy-init the Playwright browser."""
        if self._browser is not None:
            return self._browser

        try:
            from playwright.async_api import async_playwright
            pw = await async_playwright().start()
            self._browser = await pw.chromium.launch(headless=True)
            self._available = True
            logger.info("Playwright browser started")
            return self._browser
        except Exception as e:
            self._available = False
            logger.warning("Playwright not available: %s", e)
            raise RuntimeError("Playwright is not available") from e

    @property
    def available(self) -> bool:
        if self._available is None:
            try:
                import playwright  # noqa: F401
                self._available = True
            except ImportError:
                self._available = False
        return self._available or False

    async def get_session(self, agent_id: str, config: BrowserConfig) -> BrowserSession:
        """Get or create a browser session for an agent."""
        if agent_id in self._sessions:
            return self._sessions[agent_id]

        if len(self._sessions) >= config.max_sessions:
            # Close oldest session
            oldest_key = next(iter(self._sessions))
            await self._sessions[oldest_key].close()
            del self._sessions[oldest_key]

        browser = await self._ensure_browser()
        page = await browser.new_page()
        session = BrowserSession(page, config)
        self._sessions[agent_id] = session
        return session

    async def close_session(self, agent_id: str) -> None:
        session = self._sessions.pop(agent_id, None)
        if session:
            await session.close()

    async def shutdown(self) -> None:
        for session in self._sessions.values():
            await session.close()
        self._sessions.clear()
        if self._browser:
            await self._browser.close()
            self._browser = None


def _is_allowed(url: str, config: BrowserConfig) -> bool:
    """Check if a URL is allowed by the browser config."""
    from urllib.parse import urlparse
    domain = urlparse(url).hostname or ""

    for blocked in config.block_domains:
        if blocked in domain:
            return False

    if config.allow_domains == ["*"]:
        return True

    return any(allowed in domain for allowed in config.allow_domains)


# Singleton
browser_manager = BrowserManager()

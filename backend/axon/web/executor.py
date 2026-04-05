"""WebToolExecutor — handles web_* tool calls from agents."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import httpx

from axon.logging import get_logger

if TYPE_CHECKING:
    from axon.web.config import WebConfig

logger = get_logger(__name__)

# Content extraction — trafilatura is optional, falls back to basic extraction
try:
    from trafilatura import extract as trafilatura_extract
    HAS_TRAFILATURA = True
except ImportError:
    HAS_TRAFILATURA = False


class WebToolExecutor:
    """Executes web tool calls — search and fetch.

    Supports SearXNG (self-hosted, free) and Brave Search API as providers.
    Optionally synthesizes fetched content via a local LLM to reduce token cost.
    """

    def __init__(self, config: "WebConfig"):
        self.config = config
        self._synthesizer = None

        if config.synthesize_locally:
            from axon.web.synthesizer import WebSynthesizer
            self._synthesizer = WebSynthesizer(
                model=config.synthesis_model,
            )

    async def execute(self, tool_name: str, arguments: str) -> str:
        """Execute a web tool call and return the result."""
        try:
            args = json.loads(arguments)
        except json.JSONDecodeError:
            return f"Error: Invalid JSON arguments: {arguments}"

        handlers = {
            "web_search": self._search,
            "web_fetch": self._fetch,
        }

        handler = handlers.get(tool_name)
        if not handler:
            return f"Error: Unknown web tool: {tool_name}"

        try:
            return await handler(args)
        except Exception as e:
            logger.exception("Web tool error: %s", tool_name)
            return f"Error executing {tool_name}: {e}"

    async def _search(self, args: dict) -> str:
        """Search the web via configured provider."""
        query = args.get("query", "").strip()
        if not query:
            return "Error: 'query' is required."

        max_results = args.get("max_results", self.config.max_results)

        if self.config.search_provider == "brave":
            return await self._search_brave(query, max_results)
        return await self._search_searxng(query, max_results)

    async def _search_searxng(self, query: str, max_results: int) -> str:
        """Search via self-hosted SearXNG instance."""
        url = f"{self.config.searxng_url}/search"
        params = {
            "q": query,
            "format": "json",
            "engines": "google,duckduckgo,bing",
            "max_results": max_results,
        }

        async with httpx.AsyncClient(timeout=self.config.fetch_timeout) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        results = data.get("results", [])[:max_results]
        if not results:
            return f"No results found for: {query}"

        return self._format_search_results(results)

    async def _search_brave(self, query: str, max_results: int) -> str:
        """Search via Brave Search API."""
        if not self.config.brave_api_key:
            return "Error: Brave Search API key not configured."

        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.config.brave_api_key,
        }
        params = {"q": query, "count": max_results}

        async with httpx.AsyncClient(timeout=self.config.fetch_timeout) as client:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()

        web_results = data.get("web", {}).get("results", [])[:max_results]
        if not web_results:
            return f"No results found for: {query}"

        # Normalize to same format as SearXNG
        results = [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("description", ""),
            }
            for r in web_results
        ]
        return self._format_search_results(results)

    @staticmethod
    def _format_search_results(results: list[dict]) -> str:
        """Format search results for LLM consumption."""
        lines = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "Untitled")
            url = r.get("url", "")
            snippet = r.get("content", "")[:200]
            lines.append(f"**{i}. {title}**\n   URL: {url}\n   {snippet}")
        return "\n\n".join(lines)

    async def _fetch(self, args: dict) -> str:
        """Fetch and extract text content from a URL."""
        url = args.get("url", "").strip()
        if not url:
            return "Error: 'url' is required."

        async with httpx.AsyncClient(
            timeout=self.config.fetch_timeout,
            follow_redirects=True,
            headers={"User-Agent": "Axon/1.0 (AI Assistant)"},
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text

        # Extract main content from HTML
        content = self._extract_content(html, url)
        if not content:
            return f"Could not extract readable content from: {url}"

        # Truncate to configured max length
        if len(content) > self.config.max_content_length:
            content = content[: self.config.max_content_length] + "\n\n[Content truncated]"

        # Optionally synthesize via local LLM
        if self._synthesizer:
            original_query = args.get("_query", "")
            if original_query:
                content = await self._synthesizer.synthesize(
                    content, original_query,
                )

        return f"**Source:** {url}\n\n{content}"

    @staticmethod
    def _extract_content(html: str, url: str) -> str:
        """Extract readable text from HTML."""
        if HAS_TRAFILATURA:
            result = trafilatura_extract(html, url=url, include_links=False)
            if result:
                return result

        # Basic fallback — strip HTML tags
        import re
        # Remove script/style blocks
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", text)
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

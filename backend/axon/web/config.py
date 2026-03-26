"""Per-agent web access configuration."""

from __future__ import annotations

from pydantic import BaseModel


class WebConfig(BaseModel):
    """Per-agent web access toggle.

    When enabled, the agent gains access to WEB_TOOLS (web_search, web_fetch).
    Search provider and synthesis settings are configured here.
    """

    enabled: bool = False
    search_provider: str = "searxng"  # searxng | brave
    searxng_url: str = "http://searxng:8080"  # Docker service URL
    brave_api_key: str = ""  # Only needed if search_provider == "brave"
    max_results: int = 5
    fetch_timeout: int = 10  # seconds
    max_content_length: int = 4000  # chars — truncate fetched pages
    synthesize_locally: bool = True  # Use Ollama to summarize fetched content
    synthesis_model: str = "ollama/llama3:8b"  # Local model for synthesis

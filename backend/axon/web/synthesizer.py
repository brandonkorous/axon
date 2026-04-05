"""WebSynthesizer — uses a local LLM to summarize fetched web content."""

from __future__ import annotations

from axon.logging import get_logger

logger = get_logger(__name__)

SYNTHESIS_PROMPT = (
    "You are a content extraction assistant. Extract the key facts and information "
    "relevant to the user's query from the web page content below. Be concise and "
    "factual — return only the useful information, not filler or navigation text.\n\n"
    "## User's Query\n{query}\n\n"
    "## Web Page Content\n{content}\n\n"
    "## Extracted Information"
)


class WebSynthesizer:
    """Summarizes fetched web content via a local LLM (e.g. Ollama).

    This reduces the token cost of injecting raw web content into the
    cloud LLM's context window. A ~5000 char page becomes a ~500 token digest.
    """

    def __init__(self, model: str = "ollama/llama3:8b"):
        self.model = model

    async def synthesize(self, content: str, query: str) -> str:
        """Synthesize web content into a concise, query-relevant digest.

        Falls back to raw content (truncated) if the local model is unavailable.
        """
        from axon.agents.provider import complete

        prompt = SYNTHESIS_PROMPT.format(query=query, content=content[:6000])

        try:
            result = await complete(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=0.3,
            )
            synthesized = result.get("content", "").strip()
            if synthesized:
                return synthesized
        except Exception as e:
            logger.warning("Web synthesis failed (falling back to raw): %s", e)

        # Fallback — return raw content
        return content

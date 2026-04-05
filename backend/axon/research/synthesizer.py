"""Multi-document synthesizer — compress and aggregate sources via local LLM.

Uses a cheap local model (Ollama) to reduce raw source content before
the agent's primary model does the final analysis. This saves significant
token cost on the expensive cloud model while preserving quality.

Flow: raw source (4000 chars) → local LLM digest (500 chars) → agent LLM
"""

from __future__ import annotations

from typing import Any

from axon.logging import get_logger

logger = get_logger(__name__)

# Prompt for compressing a single source
SOURCE_DIGEST_PROMPT = (
    "You are a research assistant. Extract the key facts, data points, and insights "
    "from the following source that are relevant to the research topic. Be thorough "
    "but concise — capture everything important in roughly 500 words.\n\n"
    "## Research Topic\n{topic}\n\n"
    "## Source: {title}\n{content}\n\n"
    "## Key Findings"
)

# Prompt for synthesizing multiple digested sources
MULTI_SOURCE_PROMPT = (
    "You are a research synthesizer. Combine the following source digests into a "
    "coherent analysis. Identify common themes, contradictions, and key insights. "
    "Organize by theme, not by source.\n\n"
    "## Research Topic\n{topic}\n\n"
    "## Source Digests\n{digests}\n\n"
    "## Synthesized Analysis"
)

DEFAULT_MODEL = "ollama/llama3:8b"


async def digest_source(
    content: str,
    title: str,
    topic: str,
    model: str = DEFAULT_MODEL,
) -> str:
    """Compress a single source using a local LLM.

    Takes ~4000 chars of raw content, returns ~500 chars of key findings.
    Falls back to truncated raw content if the local model is unavailable.
    """
    from axon.agents.provider import complete

    prompt = SOURCE_DIGEST_PROMPT.format(
        topic=topic,
        title=title,
        content=content[:6000],
    )

    try:
        result = await complete(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.2,
        )
        digest = result.get("content", "").strip()
        if digest:
            logger.debug("Digested source '%s': %d→%d chars", title, len(content), len(digest))
            return digest
    except Exception as e:
        logger.warning("Source digest failed for '%s' (falling back to raw): %s", title, e)

    # Fallback — return truncated raw content
    return content[:1500] if len(content) > 1500 else content


async def synthesize_sources(
    sources: list[dict[str, Any]],
    topic: str,
    model: str = DEFAULT_MODEL,
) -> str:
    """Aggregate multiple source digests into a coherent synthesis.

    If local model is available: digest each source, then synthesize.
    If not: return structured raw content for the agent's LLM.
    """
    if not sources:
        return "No sources available for synthesis."

    # First pass: digest each source individually
    digests = []
    for s in sources:
        digest = await digest_source(
            content=s.get("content", ""),
            title=s.get("title", "Untitled"),
            topic=topic,
            model=model,
        )
        url = s.get("url", "")
        ref = f" ({url})" if url else ""
        digests.append(f"### {s.get('title', 'Untitled')}{ref}\n{digest}")

    digests_text = "\n\n".join(digests)

    # Second pass: synthesize all digests together
    from axon.agents.provider import complete

    prompt = MULTI_SOURCE_PROMPT.format(
        topic=topic,
        digests=digests_text,
    )

    try:
        result = await complete(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.3,
        )
        synthesis = result.get("content", "").strip()
        if synthesis:
            logger.info("Synthesized %d sources for '%s'", len(sources), topic)
            return synthesis
    except Exception as e:
        logger.warning("Multi-source synthesis failed (returning digests): %s", e)

    # Fallback — return the individual digests
    return digests_text


def deduplicate_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove duplicate sources based on URL or title similarity."""
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    unique: list[dict[str, Any]] = []

    for source in sources:
        url = source.get("url", "").strip().rstrip("/")
        title = source.get("title", "").strip().lower()

        if url and url in seen_urls:
            continue
        if title and title in seen_titles:
            continue

        if url:
            seen_urls.add(url)
        if title:
            seen_titles.add(title)
        unique.append(source)

    removed = len(sources) - len(unique)
    if removed:
        logger.debug("Deduplicated %d sources, %d removed", len(sources), removed)

    return unique

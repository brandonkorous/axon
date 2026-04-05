"""MediaToolExecutor — handles media_* tool calls for agents.

Uses a two-tier LLM strategy for transcripts:
- Local model (Ollama): compresses 10K+ char transcripts to ~1500 chars
- Agent model (Claude/GPT): does the final analysis and summarization

A 60-minute YouTube transcript can be 50K+ tokens. Without local
compression, that blows through the agent's context window and costs
a fortune. The local model extracts key points first.
"""

from __future__ import annotations

import json

from axon.logging import get_logger
from axon.media.config import MediaConfig

logger = get_logger(__name__)

TRANSCRIPT_DIGEST_PROMPT = (
    "You are a media content analyst. Extract the key points, insights, and "
    "notable statements from this transcript. Organize by topic, not chronologically. "
    "Be thorough but concise — capture everything important in roughly 1000 words.\n\n"
    "## Transcript\n{transcript}\n\n"
    "## Key Points and Insights"
)


class MediaToolExecutor:
    """Routes media tool calls to appropriate handlers."""

    def __init__(self, config: MediaConfig | None = None) -> None:
        self._config = config or MediaConfig()

    async def execute(self, tool_name: str, arguments: str) -> str:
        args = json.loads(arguments) if arguments else {}

        if tool_name == "media_youtube_transcript":
            return await self._youtube_transcript(args)
        elif tool_name == "media_summarize":
            return await self._summarize(args)
        else:
            return json.dumps({"error": f"Unknown media tool: {tool_name}"})

    async def _youtube_transcript(self, args: dict) -> str:
        from axon.media.youtube import fetch_transcript

        url = args["url"]
        language = args.get("language", "en")

        result = await fetch_transcript(
            url,
            max_length=self._config.max_transcript_length,
            languages=[language],
        )

        if "error" in result:
            return json.dumps(result)

        raw_transcript = result.get("transcript", "")

        # Compress transcript via local LLM if enabled and content is large
        if self._config.synthesize_locally and len(raw_transcript) > 2000:
            digest = await _digest_transcript(
                raw_transcript,
                model=self._config.synthesis_model,
            )
            if digest and digest != raw_transcript:
                result["transcript_digest"] = digest
                result["original_length"] = len(raw_transcript)
                result["digest_length"] = len(digest)
                # Replace raw transcript with digest to save agent tokens
                result["transcript"] = digest
                result["digested"] = True
                logger.info(
                    "Transcript compressed: %d→%d chars (%.0f%% reduction)",
                    len(raw_transcript), len(digest),
                    (1 - len(digest) / len(raw_transcript)) * 100,
                )

        return json.dumps(result)

    async def _summarize(self, args: dict) -> str:
        """Summarize content using local LLM if available, else structure for agent."""
        content = args["content"]
        fmt = args.get("format", "brief")
        focus = args.get("focus", "")

        # Try local LLM summarization first
        if self._config.synthesize_locally and len(content) > 1000:
            summary = await _local_summarize(
                content=content,
                fmt=fmt,
                focus=focus,
                model=self._config.synthesis_model,
            )
            if summary:
                return json.dumps({
                    "summary": summary,
                    "format": fmt,
                    "locally_synthesized": True,
                    "original_length": len(content),
                })

        # Fallback — structure content for agent's LLM
        max_len = self._config.max_transcript_length
        if len(content) > max_len:
            content = content[:max_len] + "\n\n[Content truncated for summarization]"

        prompt_parts = [f"Content to summarize ({len(content)} chars):"]
        prompt_parts.append(content)

        if focus:
            prompt_parts.append(f"\nFocus area: {focus}")

        format_instructions = {
            "brief": "Provide a 2-3 sentence summary capturing the main points.",
            "detailed": "Provide a comprehensive summary with sections for main topics, key insights, and conclusions.",
            "bullet_points": "Provide a bullet-point summary with 5-10 key takeaways.",
        }

        return json.dumps({
            "content": "\n\n".join(prompt_parts),
            "format_instruction": format_instructions.get(fmt, format_instructions["brief"]),
            "word_target": self._config.summary_length,
            "locally_synthesized": False,
        })


async def _digest_transcript(transcript: str, model: str) -> str | None:
    """Compress a transcript using a local LLM."""
    from axon.agents.provider import complete

    prompt = TRANSCRIPT_DIGEST_PROMPT.format(transcript=transcript[:15000])

    try:
        result = await complete(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.2,
        )
        return result.get("content", "").strip() or None
    except Exception as e:
        logger.warning("Transcript digest failed (using raw): %s", e)
        return None


SUMMARIZE_PROMPT = (
    "Summarize the following content. {format_instruction}\n\n"
    "{focus_line}"
    "## Content\n{content}\n\n"
    "## Summary"
)


async def _local_summarize(
    content: str,
    fmt: str,
    focus: str,
    model: str,
) -> str | None:
    """Summarize content using a local LLM."""
    from axon.agents.provider import complete

    format_instructions = {
        "brief": "Provide a 2-3 sentence summary capturing the main points.",
        "detailed": "Provide a comprehensive summary organized by topic with key insights.",
        "bullet_points": "Provide a bullet-point summary with 5-10 key takeaways.",
    }

    prompt = SUMMARIZE_PROMPT.format(
        format_instruction=format_instructions.get(fmt, format_instructions["brief"]),
        focus_line=f"Focus on: {focus}\n\n" if focus else "",
        content=content[:10000],
    )

    try:
        result = await complete(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.3,
        )
        return result.get("content", "").strip() or None
    except Exception as e:
        logger.warning("Local summarization failed: %s", e)
        return None

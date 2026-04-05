"""YouTube transcript fetcher — extract captions from YouTube videos."""

from __future__ import annotations

import re
from typing import Any

from axon.logging import get_logger

logger = get_logger(__name__)


def extract_video_id(url: str) -> str | None:
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})",
        r"^([a-zA-Z0-9_-]{11})$",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


async def fetch_transcript(
    url: str,
    max_length: int = 10000,
    languages: list[str] | None = None,
) -> dict[str, Any]:
    """Fetch the transcript for a YouTube video.

    Requires the `youtube-transcript-api` package.
    Returns a dict with title, video_id, transcript text, and metadata.
    """
    video_id = extract_video_id(url)
    if not video_id:
        return {"error": f"Could not extract video ID from: {url}"}

    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        langs = languages or ["en"]
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=langs)

        # Combine transcript segments
        text_parts = []
        for entry in transcript_list:
            text_parts.append(entry["text"])

        full_text = " ".join(text_parts)

        # Truncate if needed
        if len(full_text) > max_length:
            full_text = full_text[:max_length] + "\n\n[Transcript truncated]"

        return {
            "video_id": video_id,
            "url": f"https://youtube.com/watch?v={video_id}",
            "transcript": full_text,
            "segment_count": len(transcript_list),
            "duration_seconds": int(transcript_list[-1]["start"] + transcript_list[-1]["duration"])
            if transcript_list
            else 0,
        }

    except ImportError:
        return {"error": "youtube-transcript-api not installed. Run: pip install youtube-transcript-api"}
    except Exception as e:
        logger.warning("Failed to fetch transcript for %s: %s", video_id, e)
        return {"error": f"Transcript unavailable: {e}"}

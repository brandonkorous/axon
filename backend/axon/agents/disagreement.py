"""Disagreement surfacing — detect and structure advisor disagreements.

After huddle advisors respond, an LLM analyzes their positions to identify
where they agree, where they disagree, and what the key tensions are.
This structured analysis is the highest-value signal from multi-advisor discussions.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

from axon.logging import get_logger

logger = get_logger(__name__)


class DisagreementDimension(BaseModel):
    """A single dimension of agreement/disagreement between advisors."""

    dimension: str  # e.g. "timeline", "budget", "approach"
    positions: dict[str, str]  # advisor_name -> their position
    agreement_score: float  # 0.0 = total disagreement, 1.0 = full alignment


class DisagreementReport(BaseModel):
    """Structured disagreement analysis from a huddle discussion."""

    topic: str
    dimensions: list[DisagreementDimension] = []
    overall_agreement: float = 0.5
    key_tensions: list[str] = []
    recommended_resolution: str = ""


def build_disagreement_prompt(
    user_message: str,
    advisor_responses: dict[str, str],
    advisor_names: dict[str, str],
) -> list[dict[str, str]]:
    """Build messages for the disagreement analysis LLM call."""
    advisor_summary = "\n\n".join(
        f"**{advisor_names.get(aid, aid)}:** {resp}"
        for aid, resp in advisor_responses.items()
    )

    return [
        {
            "role": "system",
            "content": (
                "You are a neutral analyst examining advisor perspectives from a group discussion. "
                "Your job is to identify dimensions of agreement and disagreement.\n\n"
                "Respond with ONLY a JSON object (no markdown, no explanation) in this exact format:\n"
                "{\n"
                '  "dimensions": [\n'
                '    {\n'
                '      "dimension": "name of the dimension (e.g. timeline, approach, risk)",\n'
                '      "positions": {"AdvisorName": "their position in 1 sentence"},\n'
                '      "agreement_score": 0.7\n'
                '    }\n'
                '  ],\n'
                '  "overall_agreement": 0.6,\n'
                '  "key_tensions": ["tension 1", "tension 2"],\n'
                '  "recommended_resolution": "one sentence recommendation"\n'
                "}\n\n"
                "Rules:\n"
                "- agreement_score: 0.0 = completely opposed, 1.0 = fully aligned\n"
                "- Identify 2-5 dimensions of comparison\n"
                "- key_tensions: the most important disagreements (1-3 items)\n"
                "- Be precise and factual — quote actual positions, don't interpret\n"
                "- If advisors largely agree, say so (high scores) — don't manufacture disagreement"
            ),
        },
        {
            "role": "user",
            "content": (
                f"**Topic:** {user_message}\n\n"
                f"**Advisor responses:**\n\n{advisor_summary}"
            ),
        },
    ]


def parse_disagreement_response(
    raw: str, topic: str,
) -> DisagreementReport | None:
    """Parse the LLM's JSON response into a DisagreementReport."""
    # Try to extract JSON from the response (handle markdown wrapping)
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.debug("Failed to parse disagreement JSON: %s", text[:300])
        return None

    try:
        return DisagreementReport(
            topic=topic,
            dimensions=[
                DisagreementDimension(**d) for d in data.get("dimensions", [])
            ],
            overall_agreement=data.get("overall_agreement", 0.5),
            key_tensions=data.get("key_tensions", []),
            recommended_resolution=data.get("recommended_resolution", ""),
        )
    except Exception as e:
        logger.debug("Failed to build DisagreementReport: %s", e)
        return None

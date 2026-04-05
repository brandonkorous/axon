"""Structured output schemas — typed, composable agent responses.

Agents produce JSON-structured outputs alongside natural language when a
skill or agent config defines an output schema.  The structured data is
extracted post-completion, validated, and emitted as a separate StreamChunk.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel

from axon.logging import get_logger

logger = get_logger(__name__)

# Regex to find fenced JSON blocks in markdown
JSON_BLOCK_RE = re.compile(
    r"```json\s*\n(.*?)\n\s*```",
    re.DOTALL,
)


class OutputField(BaseModel):
    """A single field in a structured output schema."""

    name: str
    type: str = "string"  # string | number | boolean | rating | list | markdown
    description: str = ""
    required: bool = False


class InputField(BaseModel):
    """A single input field for a skill."""

    name: str
    type: str = "string"
    description: str = ""
    required: bool = False


class OutputSchema(BaseModel):
    """A named output schema — defines expected structured output shape."""

    name: str
    version: str = "1.0"
    fields: list[OutputField] = []


class StructuredResult(BaseModel):
    """A validated structured output from an agent response."""

    schema_name: str
    schema_version: str = "1.0"
    data: dict[str, Any]
    agent_id: str
    timestamp: str = ""
    confidence: float = 0.5

    def model_post_init(self, __context: Any) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


def build_output_instructions(fields: list[OutputField]) -> str:
    """Build system prompt instructions for producing structured output.

    Appended to the skill methodology when output fields are defined.
    """
    if not fields:
        return ""

    field_lines = []
    for f in fields:
        req = " (required)" if f.required else ""
        field_lines.append(f'  - `{f.name}` ({f.type}{req}): {f.description}')

    return (
        "\n## Structured Output\n"
        "After your response, include a JSON block with structured data:\n\n"
        "```json\n"
        "{\n"
        + ",\n".join(f'  "{f.name}": ...' for f in fields)
        + "\n}\n"
        "```\n\n"
        "Field definitions:\n"
        + "\n".join(field_lines)
        + "\n\nThe JSON block should appear at the END of your response, "
        "after your natural language analysis.\n"
    )


def extract_structured_output(
    response: str,
    fields: list[OutputField] | None = None,
) -> dict[str, Any] | None:
    """Extract and validate structured JSON from an agent response.

    Looks for ```json ... ``` blocks in the response.  If fields are
    provided, validates that required fields are present.

    Returns the parsed dict or None if no valid JSON block found.
    """
    matches = JSON_BLOCK_RE.findall(response)
    if not matches:
        return None

    # Use the last JSON block (output schema should be at the end)
    raw = matches[-1].strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.debug("Failed to parse structured output JSON: %s", raw[:200])
        return None

    if not isinstance(data, dict):
        return None

    # Validate required fields
    if fields:
        for f in fields:
            if f.required and f.name not in data:
                logger.debug("Missing required field '%s' in structured output", f.name)
                return None

    return data

"""Prompt templates and shared utilities for the MemoryManager."""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def parse_llm_json(text: str) -> dict[str, Any] | None:
    """Extract and parse JSON from LLM response text."""
    logger.debug("Parsing LLM JSON response (%d chars): %.200s...", len(text), text)
    if "```json" in text:
        start = text.index("```json") + 7
        end = text.index("```", start)
        text = text[start:end].strip()
    elif "```" in text:
        start = text.index("```") + 3
        end = text.index("```", start)
        text = text[start:end].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        for i, c in enumerate(text):
            if c == "{":
                try:
                    return json.loads(text[i:])
                except json.JSONDecodeError:
                    continue
        logger.warning("Failed to parse JSON from LLM response")
        return None

RECALL_PLAN_PROMPT = """\
You are a memory manager for an AI agent. Given a user message and a summary \
of the agent's vault (knowledge base), decide what memories to retrieve.

## Vault Summary
{vault_summary}

## User Message
{user_message}

Respond with JSON only:
```json
{{
  "needs_context": true/false,
  "search_queries": ["query1", "query2"],
  "branches": ["decisions", "learnings"]
}}
```

If the message is a greeting, simple question, or doesn't need vault knowledge, \
set needs_context to false. Be selective — only retrieve when it genuinely helps."""

RECALL_RANK_PROMPT = """\
You are a memory manager. Given these candidate files from the agent's vault \
and the user's message, select and rank the most relevant files.

## User Message
{user_message}

## Candidate Files
{candidates}

Respond with JSON only — a ranked list of file paths (most relevant first):
```json
{{
  "ranked_paths": ["path/to/file1.md", "path/to/file2.md"],
  "reasoning": "brief explanation"
}}
```

Only include files that are genuinely relevant. Consider confidence levels — \
prefer high-confidence validated knowledge over low-confidence entries."""

PROCESS_TURN_PROMPT = """\
You are a memory manager for an AI agent. Analyze this conversation turn and \
decide if anything is worth saving to the agent's long-term memory vault.

## User Message
{user_message}

## Agent Response
{assistant_response}

## Vault Context Used
{vault_context}

Respond with JSON only:
```json
{{
  "worth_saving": true/false,
  "insights": [
    {{
      "insight": "what was learned",
      "confidence": 0.7,
      "tags": "tag1, tag2",
      "related_files": ["path/to/related.md"]
    }}
  ],
  "confidence_updates": [
    {{
      "path": "existing/file.md",
      "new_confidence": 0.85,
      "reason": "validated by this conversation"
    }}
  ],
  "contradictions": [
    {{
      "path": "existing/file.md",
      "contradiction": "what was contradicted"
    }}
  ]
}}
```

Be selective. The bar is: "would this change how the agent handles a future \
conversation?" Greetings, simple facts, and routine answers are NOT worth saving. \
Only extract genuine insights, patterns, corrections, or validated knowledge."""

CONSOLIDATION_REVIEW_PROMPT = """\
You are a memory consolidation engine. Review these learning entries from an \
AI agent's knowledge vault and identify opportunities to consolidate.

## Learning Entries
{entries}

For each entry you see: [path] name (confidence, age_days, tags)
> First 150 chars of the insight text

Analyze the batch and respond with JSON only:
```json
{{
  "merges": [
    {{
      "source_paths": ["learnings/file1.md", "learnings/file2.md"],
      "merged_insight": "A higher-level insight combining the sources",
      "merged_confidence": 0.8,
      "tags": "tag1, tag2"
    }}
  ],
  "archives": [
    {{
      "path": "learnings/file.md",
      "reason": "Low value — vague, unvalidated, superseded by other entries"
    }}
  ],
  "contradictions": [
    {{
      "path_a": "learnings/file1.md",
      "path_b": "learnings/file2.md",
      "description": "These entries make opposing claims about X"
    }}
  ]
}}
```

Rules:
- Only merge entries that genuinely say the same thing or combine into a clear \
higher-level pattern. Do not force merges.
- Only archive entries that are clearly low-value: vague, trivial, or fully \
superseded by a better entry in this batch.
- Flag contradictions only when two entries make genuinely incompatible claims.
- It is fine to return empty arrays if nothing needs action. Be conservative.
- The merged_confidence should reflect the combined evidence — typically higher \
than either source alone, but capped at 0.9."""

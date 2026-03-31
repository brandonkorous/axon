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
extract memories worth saving. Memories come in two types:

**Short-term**: Working context — what's being discussed, active problems, \
in-flight decisions, names/details mentioned. These help the agent maintain \
continuity across turns and sessions for the next 5-7 days.

**Long-term**: Validated insights — patterns, corrections, preferences, \
strategic knowledge. These persist indefinitely and shape future behavior.

CRITICAL: Each memory must be 200 characters or fewer. Think fragments, not \
documents. If a topic needs more, split it into multiple related memories that \
reference each other. Humans recall partial memories that assemble together — \
so should this agent.

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
  "short_term": [
    {{
      "memory": "up to 200 char fragment about working context",
      "tags": "tag1, tag2",
      "related_files": ["path/to/related.md"]
    }}
  ],
  "long_term": [
    {{
      "memory": "up to 200 char fragment about a validated insight",
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

## What to save

**Short-term** (save liberally): Active bugs being debugged, decisions in progress, \
user requests and their context, names/entities mentioned, current goals or tasks. \
If the user came back tomorrow and asked "where were we?" — this is the answer.

**Long-term** (save selectively): User preferences, validated patterns, corrections \
to prior advice, strategic decisions with reasoning, things that change how the \
agent should behave in future conversations.

**Skip entirely**: Greetings, small talk, routine confirmations, information already \
captured in existing vault context."""

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

ORPHAN_ADOPTION_PROMPT = """\
You are a memory organization engine. The following files in an AI agent's \
knowledge vault are **orphans** — they exist on disk but are not reachable \
from the vault's root node via any wikilink chain.

## Vault Structure
Root file: {root_file}
Existing branches (with index files):
{branches}

## Orphan Files
{orphans}

For each orphan, decide the best action:

1. **adopt** — Link it into an existing branch index. Choose the branch that \
best matches the file's content.
2. **link_root** — Link it directly from the root file (for top-level files \
like instructions or config that don't belong in a branch).
3. **archive** — The file is stale, empty, or redundant. Mark it archived.

Respond with JSON only:
```json
{{
  "adoptions": [
    {{
      "path": "branch/file.md",
      "action": "adopt",
      "target_branch": "learnings",
      "reason": "Contains an insight about X that belongs in learnings"
    }},
    {{
      "path": "instructions.md",
      "action": "link_root",
      "reason": "Agent identity doc should be linked from root"
    }},
    {{
      "path": "branch/stale-note.md",
      "action": "archive",
      "reason": "Empty file with no meaningful content"
    }}
  ]
}}
```

Rules:
- Every orphan must appear in the adoptions array.
- Prefer "adopt" for files clearly belonging to a branch.
- Use "link_root" sparingly — only for files that genuinely belong at the top level.
- Use "archive" only when the file has no useful content.
- Be conservative — when in doubt, adopt into the closest matching branch."""

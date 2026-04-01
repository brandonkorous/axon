"""Intent router — deterministic tool and pattern selection.

Classifies user messages into intents and returns only the relevant
tool groups and cognitive patterns. No LLM needed — pure keyword matching.

This replaces the "send everything every time" approach with targeted
selection, reducing token count by 50-70% on most messages.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class RoutingResult:
    """Result of intent classification."""

    intent: str
    tool_groups: list[str]
    pattern_names: list[str]
    confidence: float  # 0-1, how confident we are in this classification


# Tool group names — these map to the *_TOOLS lists in tools.py and shared_tools.py
TOOL_GROUP_ISSUES = "issues"
TOOL_GROUP_DELEGATION = "delegation"
TOOL_GROUP_REASONING = "reasoning"
TOOL_GROUP_KNOWLEDGE = "knowledge"
TOOL_GROUP_DISCOVERY = "discovery"
TOOL_GROUP_RECRUITMENT = "recruitment"
TOOL_GROUP_PERFORMANCE = "performance"
TOOL_GROUP_ACHIEVEMENT = "achievement"
TOOL_GROUP_COMMS = "comms"
TOOL_GROUP_WEB = "web"
TOOL_GROUP_RESEARCH = "research"
TOOL_GROUP_BROWSER = "browser"
TOOL_GROUP_MEDIA = "media"
TOOL_GROUP_PLUGINS = "plugins"

# Always included — minimal baseline
ALWAYS_INCLUDED: list[str] = []

# Intent definitions: keyword patterns -> tool groups + patterns
_INTENT_RULES: list[dict[str, Any]] = [
    {
        "name": "greeting",
        "patterns": [
            r"^(hey|hi|hello|sup|yo|good morning|good afternoon|good evening)\b",
            r"^what'?s up\b",
            r"^how are you\b",
        ],
        "tool_groups": [],
        "cognitive_patterns": [],
        "confidence": 0.9,
    },
    {
        "name": "bug_report",
        "patterns": [
            r"\b(bug|error|broken|failing|crash|issue|problem|stuck|not working)\b",
            r"\b(fix|debug|investigate|diagnose|reproduce)\b",
        ],
        "tool_groups": [TOOL_GROUP_ISSUES, TOOL_GROUP_DELEGATION],
        "cognitive_patterns": ["blast_radius", "state_diagnosis"],
        "confidence": 0.8,
    },
    {
        "name": "task_management",
        "patterns": [
            r"\b(task|assign|work on|status|progress|todo|backlog)\b",
            r"\b(update|mark|complete|block)\b.*\b(task|issue)\b",
        ],
        "tool_groups": [TOOL_GROUP_DELEGATION],
        "cognitive_patterns": ["state_diagnosis"],
        "confidence": 0.8,
    },
    {
        "name": "delegation",
        "patterns": [
            r"\b(delegate|forward|send to|route|hand off|assign to)\b",
            r"\b(can you ask|tell|check with)\b.*\b(agent|advisor|team)\b",
        ],
        "tool_groups": [TOOL_GROUP_DELEGATION, TOOL_GROUP_DISCOVERY],
        "cognitive_patterns": [],
        "confidence": 0.8,
    },
    {
        "name": "strategy",
        "patterns": [
            r"\b(strategy|decide|decision|should we|trade-?off|evaluate)\b",
            r"\b(option|approach|alternative|compare|weigh|pros? and cons?)\b",
            r"\b(pricing|revenue|growth|market|competitive)\b",
        ],
        "tool_groups": [TOOL_GROUP_REASONING, TOOL_GROUP_KNOWLEDGE],
        "cognitive_patterns": ["build_vs_buy", "reversibility", "essential_complexity"],
        "confidence": 0.7,
    },
    {
        "name": "architecture",
        "patterns": [
            r"\b(architect|infrastructure|scaling|performance|database|api|service)\b",
            r"\b(deploy|migration|schema|microservice|monolith|cache|queue)\b",
            r"\b(tech debt|refactor|rewrite|migrate)\b",
        ],
        "tool_groups": [TOOL_GROUP_REASONING, TOOL_GROUP_DELEGATION],
        "cognitive_patterns": [
            "blast_radius", "boring_technology", "essential_complexity",
            "make_change_easy", "technical_debt_quadrant",
        ],
        "confidence": 0.7,
    },
    {
        "name": "capability_discovery",
        "patterns": [
            r"\b(what tools|need tools|need more|missing|equipped|capabilities)\b",
            r"\b(can you (browse|access|inspect|view|open|scrape))\b",
            r"\b(do you have|don'?t have|lack|can'?t (do|access|generate|process))\b",
            r"\b(plugin|skill|sandbox|integration|discover|enable|request)\b.*\b(tool|capability|feature|access)\b",
            r"\b(discover|available|install|activate|unlock)\b.*\b(plugin|skill|sandbox|tool)\b",
        ],
        "tool_groups": [TOOL_GROUP_DISCOVERY],
        "cognitive_patterns": [],
        "confidence": 0.85,
    },
    {
        "name": "team_discovery",
        "patterns": [
            r"\b(who handles|find agent|team|colleague|expert|specialist)\b",
            r"\b(need someone|hire|recruit|new agent|request agent)\b",
        ],
        "tool_groups": [TOOL_GROUP_DISCOVERY, TOOL_GROUP_RECRUITMENT],
        "cognitive_patterns": ["conways_law", "glue_work"],
        "confidence": 0.8,
    },
    {
        "name": "knowledge_sharing",
        "patterns": [
            r"\b(share|document|publish|distribute|inform|update the team)\b",
            r"\b(knowledge|insight|finding|report|analysis)\b",
        ],
        "tool_groups": [TOOL_GROUP_KNOWLEDGE],
        "cognitive_patterns": ["systems_over_heroes"],
        "confidence": 0.7,
    },
    {
        "name": "communication",
        "patterns": [
            r"\b(email|slack|discord|send|message|notify|contact)\b",
            r"\b(reach out|get in touch|ping)\b",
        ],
        "tool_groups": [TOOL_GROUP_COMMS],
        "cognitive_patterns": [],
        "confidence": 0.8,
    },
    {
        "name": "research",
        "patterns": [
            r"\b(research|look up|search|find out|investigate|explore)\b",
            r"\b(what is|how does|compare|benchmark|evaluate)\b",
        ],
        "tool_groups": [TOOL_GROUP_WEB, TOOL_GROUP_RESEARCH, TOOL_GROUP_REASONING],
        "cognitive_patterns": ["build_vs_buy"],
        "confidence": 0.6,
    },
    {
        "name": "performance_review",
        "patterns": [
            r"\b(metrics|performance|retro|retrospective|kpi)\b",
            r"\b(how did|track|measure|report)\b.*\b(week|month|quarter)\b",
        ],
        "tool_groups": [TOOL_GROUP_PERFORMANCE],
        "cognitive_patterns": ["state_diagnosis"],
        "confidence": 0.8,
    },
    {
        "name": "achievement",
        "patterns": [
            r"\b(milestone|shipped|launched|achieved|accomplished|celebrate)\b",
        ],
        "tool_groups": [TOOL_GROUP_ACHIEVEMENT],
        "cognitive_patterns": [],
        "confidence": 0.7,
    },
    {
        "name": "shell_filesystem",
        "patterns": [
            r"\b(list files|list dir|directory|folder|file system|filesystem|workspace)\b",
            r"\b(shell|terminal|command|execute|exec|run|sandbox|container)\b",
            r"\b(read file|write file|create file|delete file|edit file)\b",
            r"\b(git|node|python|npm|pip|cargo|make)\b",
            r"\b(shell_exec|shell_list_dir|shell_read_file|shell_write_file)\b",
            r"\b(sandbox_exec|sandbox_list_dir|sandbox_read_file|sandbox_write_file)\b",
        ],
        "tool_groups": [TOOL_GROUP_PLUGINS],
        "cognitive_patterns": [],
        "confidence": 0.9,
    },
]


def classify_intent(message: str) -> RoutingResult:
    """Classify a user message and return relevant tool groups + patterns.

    Falls back to a general intent if no specific match is found.
    """
    message_lower = message.lower().strip()

    best_match: RoutingResult | None = None
    best_score = 0.0

    for rule in _INTENT_RULES:
        matches = 0
        for pattern in rule["patterns"]:
            if re.search(pattern, message_lower):
                matches += 1

        if matches > 0:
            # Score = number of matching patterns * base confidence
            score = matches * rule["confidence"]
            if score > best_score:
                best_score = score
                best_match = RoutingResult(
                    intent=rule["name"],
                    tool_groups=ALWAYS_INCLUDED + rule["tool_groups"],
                    pattern_names=rule["cognitive_patterns"],
                    confidence=min(rule["confidence"], 1.0),
                )

    if best_match:
        return best_match

    # Fallback: general intent with common tools
    return RoutingResult(
        intent="general",
        tool_groups=ALWAYS_INCLUDED + [
            TOOL_GROUP_ISSUES, TOOL_GROUP_DELEGATION,
        ],
        pattern_names=[],
        confidence=0.3,
    )

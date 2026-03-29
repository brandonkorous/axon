"""Decision classification — Mechanical / Taste / User Challenge taxonomy.

When agents auto-resolve in pipelines or huddles, each decision is
classified to determine whether it should be auto-resolved silently,
surfaced for review, or escalated to the user.
"""

from __future__ import annotations

import re
from enum import Enum


class DecisionClass(str, Enum):
    """How autonomous a decision can be."""

    MECHANICAL = "mechanical"  # auto-decide silently
    TASTE = "taste"  # auto-decide but surface for review
    USER_CHALLENGE = "user_challenge"  # NEVER auto-decide


# Patterns matched against the decision description (case-insensitive).
# First match wins — order from most specific to least.

_USER_CHALLENGE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\bshould we\b",
        r"\bshould I\b",
        r"\bbudget\b",
        r"\bscope\b.*\b(change|expand|reduce)\b",
        r"\bhir(e|ing)\b",
        r"\bfir(e|ing)\b",
        r"\bstrateg(y|ic)\b",
        r"\barchitectur(e|al)\b.*\b(change|rewrite|migration)\b",
        r"\bcommit(ment)?\b.*\b(long.?term|multi.?year|contract)\b",
        r"\bremov(e|ing)\b.*\b(feature|functionality|endpoint|api)\b",
        r"\bpivot\b",
        r"\bfundrais(e|ing)\b",
        r"\bpric(e|ing)\b.*\b(change|increase|decrease)\b",
        r"\bpartnership\b",
        r"\bacquisition\b",
        r"\bshut.?down\b",
        r"\bdeprecate\b",
    ]
]

_MECHANICAL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\bformat(ting)?\b",
        r"\bnam(e|ing)\b.*\b(convention|style)\b",
        r"\border(ing)?\b.*\b(import|sort)\b",
        r"\bimport\b.*\b(order(?:ing)?|sort(?:ing)?|clean(?:ing|up)?)\b",
        r"\bboilerplate\b",
        r"\bwhitespace\b",
        r"\bindent(ation)?\b",
        r"\blint(ing)?\b",
        r"\btype\s?(hint|annotation)\b",
        r"\bdead\s?code\b",
        r"\bunused\b.*\b(variable|import|function)\b",
        r"\bversion\s?bump\b",
        r"\bdefault\s?value\b",
    ]
]


def classify_decision(description: str) -> DecisionClass:
    """Classify a decision description into Mechanical/Taste/User Challenge.

    First checks for user-challenge signals (high-stakes, irreversible).
    Then checks for mechanical signals (rote, pattern-based).
    Everything else is a taste decision.
    """
    for pattern in _USER_CHALLENGE_PATTERNS:
        if pattern.search(description):
            return DecisionClass.USER_CHALLENGE

    for pattern in _MECHANICAL_PATTERNS:
        if pattern.search(description):
            return DecisionClass.MECHANICAL

    return DecisionClass.TASTE

"""Pydantic model for cognitive pattern metadata loaded from pattern.yaml."""

from __future__ import annotations

from pydantic import BaseModel


class CognitivePattern(BaseModel):
    """A named mental model / thinking framework for a role."""

    name: str  # unique identifier, snake_case
    display_name: str = ""  # human-readable, e.g. "One-Way / Two-Way Doors"
    attribution: str = ""  # e.g. "Jeff Bezos"
    roles: list[str] = []  # which roles this applies to: ceo, cto, coo, cmo, designer, engineer
    description: str = ""  # one-line description
    tags: list[str] = []

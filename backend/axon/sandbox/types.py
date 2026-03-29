"""Sandbox type definitions and resolution logic."""

from __future__ import annotations

from enum import Enum


class SandboxType(str, Enum):
    """Available sandbox image types, ordered by capability."""

    BASE = "base"
    BROWSER = "browser"
    CODE = "code"
    DATA = "data"
    ML = "ml"
    DOCUMENTS = "documents"
    MEDIA = "media"
    FULL = "full"


# Inheritance chain — each type extends its parent image
SANDBOX_PARENTS: dict[SandboxType, SandboxType | None] = {
    SandboxType.BASE: None,
    SandboxType.BROWSER: SandboxType.BASE,
    SandboxType.CODE: SandboxType.BASE,
    SandboxType.DATA: SandboxType.CODE,
    SandboxType.ML: SandboxType.DATA,
    SandboxType.DOCUMENTS: SandboxType.CODE,
    SandboxType.MEDIA: SandboxType.BASE,
    SandboxType.FULL: None,
}

# Static metadata for each sandbox type
SANDBOX_METADATA: dict[SandboxType, dict] = {
    SandboxType.BASE: {
        "description": "Minimal shell environment",
        "estimated_size_mb": 50,
        "tools": ["bash", "bun", "curl", "git", "jq"],
    },
    SandboxType.BROWSER: {
        "description": "Web automation with Playwright",
        "estimated_size_mb": 500,
        "tools": ["bun", "playwright", "chromium"],
    },
    SandboxType.CODE: {
        "description": "Node.js and Python development",
        "estimated_size_mb": 200,
        "tools": ["bun", "python", "uv"],
    },
    SandboxType.DATA: {
        "description": "Data science and analysis",
        "estimated_size_mb": 350,
        "tools": ["pandas", "numpy", "matplotlib", "scipy", "jupyter"],
    },
    SandboxType.ML: {
        "description": "Machine learning and inference",
        "estimated_size_mb": 800,
        "tools": ["pytorch", "scikit-learn", "transformers", "onnxruntime"],
    },
    SandboxType.DOCUMENTS: {
        "description": "Document generation and conversion",
        "estimated_size_mb": 500,
        "tools": ["pandoc", "latex", "wkhtmltopdf", "libreoffice"],
    },
    SandboxType.MEDIA: {
        "description": "Audio, video, and image processing",
        "estimated_size_mb": 180,
        "tools": ["ffmpeg", "imagemagick", "sharp"],
    },
    SandboxType.FULL: {
        "description": "All tools available",
        "estimated_size_mb": 1500,
        "tools": ["all"],
    },
}


def image_name(sandbox_type: SandboxType, registry: str = "") -> str:
    """Image name for a sandbox type, optionally prefixed with a registry.

    registry="" → "axon-sandbox-base:latest"  (local Docker)
    registry="ghcr.io/axon-ai" → "ghcr.io/axon-ai/axon-sandbox-base:latest"
    """
    base = f"axon-sandbox-{sandbox_type.value}:latest"
    if registry:
        return f"{registry.rstrip('/')}/{base}"
    return base


def get_ancestors(sandbox_type: SandboxType) -> list[SandboxType]:
    """Return the ancestor chain (root first) for a sandbox type."""
    ancestors: list[SandboxType] = []
    current = SANDBOX_PARENTS.get(sandbox_type)
    while current:
        ancestors.append(current)
        current = SANDBOX_PARENTS.get(current)
    return list(reversed(ancestors))


def is_ancestor(potential_ancestor: SandboxType, of: SandboxType) -> bool:
    """Check if *potential_ancestor* is the same as or an ancestor of *of*."""
    return potential_ancestor in get_ancestors(of) or potential_ancestor == of


def resolve_sandbox_type(required_types: list[str]) -> SandboxType:
    """Find the minimum sandbox type that satisfies all requirements."""
    if not required_types:
        return SandboxType.BASE

    types = [SandboxType(t) for t in required_types if t]
    if not types:
        return SandboxType.BASE

    if SandboxType.FULL in types:
        return SandboxType.FULL

    # Check if any single candidate covers all required types
    for candidate in types:
        if all(is_ancestor(other, candidate) or other == candidate for other in types):
            return candidate

    # No single type covers all — fall back to full
    return SandboxType.FULL

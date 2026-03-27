"""Artifact templates — markdown scaffolds for different deliverable types."""

from __future__ import annotations

from axon.research.config import ArtifactType


REPORT_TEMPLATE = """# {title}

## Executive Summary
{summary}

## Key Findings
{findings}

## Detailed Analysis
{analysis}

## Sources
{sources}

## Methodology
- Research depth: {depth}
- Sources consulted: {source_count}
- Date: {date}
"""

ANALYSIS_TEMPLATE = """# {title}

## Overview
{summary}

## Data Points
{findings}

## Analysis
{analysis}

## Implications
{implications}

## Sources
{sources}
"""

BRIEF_TEMPLATE = """# {title}

{summary}

## Key Points
{findings}

## Sources
{sources}
"""

COMPARISON_TEMPLATE = """# {title}

## Overview
{summary}

## Comparison Matrix
{findings}

## Analysis
{analysis}

## Recommendation
{recommendation}

## Sources
{sources}
"""

TEMPLATES: dict[ArtifactType, str] = {
    ArtifactType.REPORT: REPORT_TEMPLATE,
    ArtifactType.ANALYSIS: ANALYSIS_TEMPLATE,
    ArtifactType.BRIEF: BRIEF_TEMPLATE,
    ArtifactType.COMPARISON: COMPARISON_TEMPLATE,
}


def get_template(artifact_type: ArtifactType) -> str:
    """Get the markdown template for an artifact type."""
    return TEMPLATES.get(artifact_type, REPORT_TEMPLATE)

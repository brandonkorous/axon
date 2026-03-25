"""LLM prompt templates for the reasoning engine."""

from __future__ import annotations

EVALUATE_CLAIM_PROMPT = """\
You are a structured reasoning engine. Evaluate the following claim against \
the provided evidence. Score how well the evidence supports or contradicts it.

## Claim
{claim}

## Evidence
{evidence}

Respond with JSON only:
```json
{{
  "score": 0.75,
  "supporting": ["node_id_1"],
  "contradicting": ["node_id_2"],
  "reasoning": "Brief explanation of your evaluation"
}}
```

Rules:
- score: 0.0 = definitely false, 0.5 = uncertain, 1.0 = definitely true
- Only reference evidence IDs from the list above
- Be precise — distinguish between weak and strong evidence
- If evidence is thin or ambiguous, score closer to 0.5"""

MAKE_DECISION_PROMPT = """\
You are a structured reasoning engine. Make a decision on the following \
question using the provided evidence and options.

## Question
{question}

## Options
{options}

## Evidence
{evidence}

Respond with JSON only:
```json
{{
  "conclusion": "The chosen course of action",
  "confidence": 0.8,
  "alternatives": [
    {{"option": "Option A", "score": 0.8, "reasoning": "Why this scored highest"}},
    {{"option": "Option B", "score": 0.5, "reasoning": "Why this scored lower"}}
  ],
  "reasoning": "Overall explanation of why this decision was reached",
  "claims": [
    {{"content": "A claim that emerged from this analysis", "confidence": 0.7, "type": "claim"}}
  ]
}}
```

Rules:
- Score each option 0.0–1.0 based on evidence
- The conclusion MUST match the highest-scored option
- Extract any new claims or insights that emerged during analysis
- Be specific — vague conclusions are useless"""

RESOLVE_CONTRADICTION_PROMPT = """\
You are a structured reasoning engine. Two pieces of knowledge contradict \
each other. Resolve the contradiction.

## Node A
{node_a}

## Node B
{node_b}

## Additional Context
{context}

Respond with JSON only:
```json
{{
  "resolution": "The resolved position that accounts for both sides",
  "confidence": 0.7,
  "keep": "a",
  "reasoning": "Why this resolution is correct"
}}
```

Rules:
- keep: "a" (A is correct), "b" (B is correct), "both" (both partially true), "neither" (both wrong)
- The resolution should synthesize the truth, not just pick a winner
- If evidence is insufficient, say so and keep confidence low"""

EXPLAIN_DECISION_PROMPT = """\
You are a structured reasoning engine. Explain the following decision trace \
in clear, readable prose. Trace the reasoning chain from evidence to conclusion.

## Decision
{decision}

## Evidence Chain
{evidence_chain}

Write a clear explanation that a non-technical person could follow. \
Use bullet points for key evidence. End with the confidence level and \
any caveats or assumptions."""

EXTRACT_FROM_HUDDLE_PROMPT = """\
You are a structured reasoning engine. Extract claims, evidence, decisions, \
and contradictions from this multi-agent discussion transcript.

## Topic
{topic}

## Transcript
{transcript}

Respond with JSON only:
```json
{{
  "claims": [
    {{"content": "A claim made during discussion", "confidence": 0.7, "source": "agent_name"}}
  ],
  "evidence": [
    {{"content": "A fact or data point cited", "confidence": 0.8, "source": "agent_name"}}
  ],
  "decisions": [
    {{"question": "What was being decided", "conclusion": "What was concluded", "confidence": 0.75}}
  ],
  "contradictions": [
    {{"claim_a": "First position", "claim_b": "Opposing position", "description": "Nature of the conflict"}}
  ]
}}
```

Rules:
- Only extract substantive claims, not filler or agreements
- Confidence reflects how strongly the claim was argued and supported
- Source is the agent name who made the claim
- Contradictions should be genuine disagreements, not just different perspectives"""

GATHER_EVIDENCE_PROMPT = """\
You are a memory search planner. Given a question and a summary of available \
vault files, identify which files are most relevant as evidence.

## Question
{question}

## Available Files
{vault_summary}

Respond with JSON only:
```json
{{
  "relevant_paths": ["path/to/file1.md", "path/to/file2.md"],
  "reasoning": "Brief explanation of why these files are relevant"
}}
```

Only include files that contain evidence directly relevant to the question. \
Be selective — less is more."""

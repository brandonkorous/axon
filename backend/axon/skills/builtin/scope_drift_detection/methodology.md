# Scope Drift Detection Methodology

You are performing a structured scope alignment analysis. Your job is to compare stated intent against actual changes and identify drift in both directions — additions that weren't asked for, and requirements that weren't addressed.

## Phase 1: Extract Requirements

Parse the original request into discrete, testable requirements:

1. **Explicit requirements** — things directly stated ("add a login page", "fix the search bug")
2. **Implicit requirements** — things reasonably expected ("the login page needs error handling", "the fix shouldn't break other searches")
3. **Out-of-scope signals** — anything the request explicitly excludes or doesn't mention

Number each requirement. Be specific — "improve performance" is not testable; "reduce page load time" is.

## Phase 2: Catalog Changes

Enumerate every change made:

1. **Files modified** — what was touched and what was the nature of the change
2. **New files** — what was added that didn't exist before
3. **Removed files** — what was deleted
4. **Behavioral changes** — what works differently from the user's perspective

For each change, write a one-line summary of what it does.

## Phase 3: Alignment Mapping

Map each change to a requirement:

| Change | Maps to Requirement | Classification |
|--------|-------------------|----------------|
| [change description] | Req #N / None | aligned / creep / refactor / dependency |

Classifications:
- **aligned** — directly implements a stated requirement
- **creep** — goes beyond what was asked. Sub-classify:
  - *while-I-was-here*: touched a nearby file and "improved" something unrelated
  - *gold-plating*: added features, configurability, or abstractions not requested
  - *premature*: built for hypothetical future requirements
- **refactor** — restructured existing code beyond what the task required
- **dependency** — necessary supporting change to enable a requirement (acceptable drift)

## Phase 4: Gap Analysis

For each original requirement, check coverage:

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Req #1 | covered / partial / missing | [which change addresses it] |

A requirement is:
- **covered** — fully addressed by one or more changes
- **partial** — some aspects addressed, others not
- **missing** — not addressed at all in the changes

## Phase 5: Drift Assessment

Synthesize your findings:

1. **Scope creep items** — list every change classified as creep, with the sub-classification and an estimate of how much effort went to non-requested work
2. **Missing requirements** — list every requirement that is partial or missing
3. **Alignment score** (1-10):
   - **9-10**: Changes match requirements precisely. Minimal or no drift.
   - **7-8**: Minor drift — small additions or one partial requirement. Acceptable.
   - **5-6**: Moderate drift — several unrelated changes or a notable gap.
   - **3-4**: Significant drift — substantial scope creep or multiple missing requirements.
   - **1-2**: Severe drift — changes bear little resemblance to the original request.

4. **Recommendation**: Should the drift be accepted, reverted, or addressed?
   - Accepted: the additions are valuable and the gaps are minor
   - Reverted: the creep adds complexity without value
   - Addressed: missing requirements need to be implemented before this is complete

## Rules

- Be precise. "Some files were changed" is useless. Name the files.
- Don't penalize dependency changes — if adding a login page requires updating the router, that's not creep.
- DO penalize gold-plating — if the task was "add a login page" and the developer also added OAuth, password reset, and MFA, flag each as creep even if they're "good ideas."
- Partial credit is real. A requirement that's 80% done is partial, not missing.
- The alignment score should reflect BOTH directions of drift (creep and gaps).

# Strategic Scope Review Methodology

You are performing a strategic founder-mode scope analysis, evaluating a proposal through one of four distinct lenses to ensure the right amount of work is being done at the right time.

## Phase 1: Mode Identification

Select the review mode based on input. Each mode represents a fundamentally different strategic posture:

| Mode | Posture | Core Question |
|------|---------|---------------|
| **Expand** | Dream big | What 10x opportunities are we missing? |
| **Selective** | Cherry-pick | What adjacent wins can we grab without scope explosion? |
| **Hold** | Fortify | How do we make what we have bulletproof? |
| **Reduce** | Ship fast | What is the absolute minimum that delivers value? |

If the mode is ambiguous, default to **hold** — it is the safest strategic posture.

## Phase 2: Architecture Overview

Regardless of mode, produce a comprehensive architecture assessment:

1. **System map** — enumerate all components, services, and their relationships
2. **Dependency graph** — what depends on what. Identify critical path components (single points of failure)
3. **Data flow** — trace how data moves through the system, including:
   - Happy path (normal operation)
   - Shadow paths (nil values, empty responses, error states, timeout cascades)
4. **Integration points** — external services, APIs, databases, and their failure modes
5. **Current technical debt** — known shortcuts, TODOs, and deferred decisions

## Phase 3: Mode-Specific Analysis

### Expand Mode — Surface 10x Opportunities

For each opportunity identified:

1. **Describe it** — what is the opportunity and why is it transformative (not incremental)
2. **Estimate effort** — T-shirt size (S/M/L/XL) with rationale
3. **Explain upside** — what changes if this succeeds. Revenue? Users? Moat? Technical capability?
4. **Explain downside** — what is the cost of pursuing this and failing
5. **Dependencies** — what must be true for this to work
6. **Opt-in approval** — explicitly flag that this is an expansion. Do not include in scope without approval.

Generate at least 5 opportunities, ranked by impact-to-effort ratio. For each, clearly state:
- "This would add approximately X weeks of work"
- "The upside is Y"
- "I recommend including/excluding this because Z"

**Red flag**: If every opportunity is "nice to have" rather than transformative, the product may already be well-scoped. Say so.

### Selective Expansion — Cherry-Pick Adjacent Wins

Hold the baseline scope firm. Then evaluate adjacent opportunities individually:

1. **Identify adjacencies** — features or improvements that are close to existing work
2. **Justify each** — why this specific addition is worth the scope increase
3. **Quantify cost** — hours, not days. Be precise.
4. **Assess blast radius** — does this addition touch other parts of the codebase? How many files?
5. **Gate each addition** — present as individual yes/no decisions, not a bundle

Acceptance criteria for selective additions:
- Effort is under 2 days
- Touches fewer than 5 files
- Does not introduce new dependencies
- Has clear user-facing value (not just "cleaner code")
- Does not delay the core delivery date

### Hold Mode — Maximum Rigor

No new features. Focus entirely on hardening what exists:

1. **Error/rescue mapping** — trace every code path and document what happens on failure
   - What errors can occur at each step?
   - Are errors caught and handled gracefully?
   - Do error messages help the user take corrective action?
   - Are there silent failures (caught exceptions with no logging)?

2. **Security threat model** — for each entry point:
   - What can an attacker send?
   - What validation exists?
   - What is the blast radius of a successful attack?

3. **Test coverage mapping** — for each feature:
   - What is tested?
   - What is NOT tested but should be?
   - Are edge cases covered (empty input, max length, concurrent access)?

4. **Performance review** — identify:
   - N+1 query patterns
   - Unbounded loops or recursion
   - Missing caching opportunities
   - Memory allocation hotspots

5. **Observability gaps** — can you answer these in production:
   - What is the system doing right now?
   - What went wrong in the last hour?
   - Which users are affected by an issue?

6. **Deployment safety** — what happens when a deploy goes wrong:
   - Rollback procedure documented?
   - Database migrations reversible?
   - Feature flags in place for risky changes?

### Reduce Mode — Ship MVP

Identify and defer everything non-essential:

1. **Core value proposition** — what is the ONE thing this product must do well
2. **Feature triage** — classify every planned feature:

| Feature | Classification | Rationale |
|---------|---------------|-----------|
| {feature} | Ship / Defer / Cut | {why} |

Classifications:
- **Ship**: Without this, the product does not deliver its core value
- **Defer**: Valuable but not required for launch. Build after validation.
- **Cut**: Not aligned with core value. Remove from roadmap entirely.

3. **Dependency pruning** — remove libraries, services, and integrations not needed for Ship features
4. **Timeline compression** — with reduced scope, what is the new realistic ship date
5. **Risk of cutting** — for each deferred/cut item, what is the risk that users reject the product without it

**Hard rule**: If a feature does not directly serve the core value proposition, it is deferred by default. The burden of proof is on inclusion, not exclusion.

## Phase 4: Cross-Cutting Analysis

Regardless of mode, assess:

### Error & Rescue Mapping
For every code path:
- What is the expected input?
- What happens with unexpected input?
- Where does the error surface (user-facing, logs, silent)?
- Is the error message actionable?

### Security Threat Model
For every entry point:
- Authentication: is the caller verified?
- Authorization: is the caller allowed to do this?
- Input validation: is the input sanitized?
- Data exposure: does the response leak sensitive information?

### Data Flow Tracing
Trace data from input to storage to output:
- Where is data transformed?
- Where could data be lost or corrupted?
- Are there shadow paths where nil/empty values propagate silently?
- Is sensitive data encrypted at rest and in transit?

### Long-Term Trajectory
- Where does this architecture lead in 6 months? 2 years?
- What decisions made now will be expensive to reverse?
- Are there architectural cliffs (points where the current approach stops scaling)?

## Phase 5: Risk Assessment

Categorize all identified risks:

| Severity | Description |
|----------|-------------|
| Critical | Will cause production outage or data loss if not addressed |
| High | Significant user impact or security vulnerability |
| Medium | Degraded experience or maintainability concern |
| Low | Minor issue, address when convenient |

For each risk:
- **What**: Describe the risk precisely
- **Why**: Explain why this matters
- **How to fix**: Specific remediation steps with effort estimate

## Phase 6: Strategic Recommendation

Synthesize findings into a clear recommendation:

1. **Mode verdict** — is the chosen mode correct, or should the founder reconsider?
2. **Top 3 priorities** — what must happen first, regardless of mode
3. **Timeline estimate** — realistic delivery date given the mode and findings
4. **Decision log** — explicit list of decisions made and deferred

## Output Structure

```markdown
## Strategic Scope Review: {Proposal Name}

**Mode**: {Expand | Selective | Hold | Reduce}

### Architecture Overview
- **Components**: {system map}
- **Critical paths**: {single points of failure}
- **Data flow**: {primary and shadow paths}

### Mode-Specific Analysis
{Mode-dependent sections per Phase 3}

### Error & Rescue Mapping
| Code Path | Failure Mode | Current Handling | Recommendation |
|-----------|-------------|-----------------|----------------|
| {path} | {what fails} | {what happens} | {what should happen} |

### Security Threat Model
| Entry Point | Threat | Current Mitigation | Gap |
|-------------|--------|-------------------|-----|
| {endpoint} | {threat} | {mitigation} | {gap} |

### Risk Assessment
| Risk | Severity | Impact | Remediation |
|------|----------|--------|-------------|
| {risk} | {critical/high/medium/low} | {what happens} | {how to fix} |

### Recommendation
**Mode verdict**: {correct mode / suggest alternative}
**Top priorities**:
1. {priority with effort estimate}
2. {priority with effort estimate}
3. {priority with effort estimate}

**Timeline**: {realistic estimate}
**Key decisions**: {what was decided and what was deferred}
```

# Engineering Review Methodology

You are performing an engineering manager-mode review of a proposed change, locking architecture decisions and producing test plans before any implementation begins.

## Phase 1: Scope & Architecture Analysis

### Existing Code Audit

Before designing anything new, identify what already exists:

1. **Related code** — search the codebase for modules, functions, or patterns that solve related problems. Avoid rebuilding what exists.
2. **Reuse candidates** — list specific files and functions that could be extended rather than replaced
3. **Pattern inventory** — document the existing patterns (naming conventions, error handling style, data access patterns) that new code must follow

### Scope Challenge

Stress-test the scope:

- Is every feature in the proposal necessary for the stated goal?
- Can any feature be deferred without reducing core value?
- Are there implicit requirements not stated (auth, error handling, logging, migrations)?
- What is explicitly out of scope?

### Complexity Mapping

Map the change across the codebase:

| File/Module | Change Type | Complexity |
|-------------|-------------|------------|
| {file} | New / Modified / Deleted | Low / Medium / High |

**Over-engineering smell test**: If the proposal touches more than 8 files, challenge whether the design is too complex. Possible causes:
- Feature is too broad (split it)
- Abstraction is wrong (simpler design exists)
- Unnecessary indirection (remove layers)
- Mixing concerns (separate responsibilities)

### System Design Evaluation

1. **Component diagram** — ASCII diagram showing components and their interactions
2. **Dependency graph** — what depends on what. Identify circular dependencies.
3. **Interface contracts** — define the API surface between components (inputs, outputs, error types)
4. **State management** — where is state stored, how does it flow, what are the consistency requirements

Score the architecture:

| Score | Level | Description |
|-------|-------|-------------|
| 0 | Unacceptable | Fundamental design flaws. Circular dependencies, no clear boundaries. |
| 1 | Weak | Works but fragile. Tight coupling, difficult to test in isolation. |
| 2 | Adequate | Reasonable separation. Some coupling but manageable. |
| 3 | Good | Clean boundaries, testable components, clear data flow. |
| 4 | Excellent | Elegant design. Easy to extend, test, and reason about. |

## Phase 2: Code Quality & Testing

### Coverage Diagram

Produce ASCII diagrams tracing every code path and user flow:

```
User Action → API Endpoint → Validation → Business Logic → Database → Response
                                ↓                ↓
                           Error Path       Error Path
                                ↓                ↓
                          400 Response     500 Response + Log
```

For each branch in the diagram, specify:
- What triggers this path
- What the expected outcome is
- Whether a test exists for it

### Test Gap Analysis

Identify untested paths with specific file and line references:

| Gap | File | Lines | Risk | Priority |
|-----|------|-------|------|----------|
| {what is untested} | {file path} | {line range} | {what could go wrong} | {P0/P1/P2} |

### Test Type Classification

For each required test, classify:

- **Unit tests** — isolated function behavior, mocked dependencies
- **Integration tests** — component interactions, real database, real file system
- **E2E tests** — full user workflow from UI to database and back
- **LLM eval tests** — if AI-generated output is involved, specify evaluation criteria (not just "does it work" but measurable quality dimensions)
- **Regression tests** — specific scenarios that previously broke and must not break again

### Mandatory Test Scenarios

List exact test scenarios with:
- **Scenario name**: descriptive, specific
- **Setup**: preconditions and test data
- **Action**: what is being tested
- **Expected result**: precise outcome, not vague
- **Type**: unit / integration / E2E / eval

## Phase 3: Performance & Failure Analysis

### Performance Review

Check for common performance issues:

1. **N+1 queries** — loops that issue database queries per iteration instead of batching
2. **Memory allocation** — large objects created in loops, unbounded collections, missing pagination
3. **Caching strategy** — what is cached, what should be, cache invalidation approach
4. **Concurrency** — race conditions, deadlocks, thread safety of shared state
5. **Network calls** — sequential calls that could be parallel, missing timeouts, retry storms

### Production Failure Scenarios

For every new code path, document one realistic production failure:

| Code Path | Failure Scenario | User Impact | Detection | Recovery |
|-----------|-----------------|-------------|-----------|----------|
| {path} | {what goes wrong} | {what user sees} | {how we know} | {how to fix} |

Requirements for each scenario:
- Must be realistic (not "meteor hits data center")
- Must describe user-facing impact (not just technical symptoms)
- Must include detection mechanism (how do we know this happened)
- Must include recovery steps (not just "fix it")

### Error Handling Audit

Verify error handling is user-facing:
- No stack traces shown to users
- Error messages explain what happened and what to do next
- Graceful degradation where possible (partial results over total failure)
- Errors are logged with sufficient context for debugging

## Phase 4: Scope Verdict

Synthesize all findings into a verdict:

- **Go**: Architecture is sound, tests are planned, risks are manageable. Proceed with implementation.
- **Refine**: Core approach is correct but specific issues must be resolved first. List the required refinements.
- **Reject**: Fundamental problems with the approach. Propose an alternative or request a redesign.

For refine or reject verdicts, provide:
- Specific issues that must be addressed
- Suggested alternative approaches
- Effort estimate for the required changes

## Output Structure

```markdown
## Engineering Review: {Proposal Name}

### Scope Assessment
- **Files affected**: {count and list}
- **Complexity**: {over-engineering smell test result}
- **Existing code to reuse**: {list with file paths}
- **Out of scope**: {explicit exclusions}

### Architecture
- **Score**: {0-4}
- **Component diagram**: {ASCII}
- **Dependencies**: {graph with circular dependency check}
- **Interface contracts**: {API surfaces}

### Coverage Diagram
{ASCII flow diagram with all paths}

### Test Plan
| # | Scenario | Type | Priority | File |
|---|----------|------|----------|------|
| 1 | {scenario} | {unit/integration/E2E/eval} | {P0/P1/P2} | {target file} |

### Test Gaps
| Gap | File | Lines | Risk |
|-----|------|-------|------|
| {gap} | {path} | {lines} | {risk} |

### Performance Concerns
| Issue | Location | Severity | Fix |
|-------|----------|----------|-----|
| {issue} | {file/line} | {severity} | {remediation} |

### Failure Scenarios
| Code Path | Failure | User Impact | Detection | Recovery |
|-----------|---------|-------------|-----------|----------|
| {path} | {scenario} | {impact} | {how to detect} | {how to fix} |

### Verdict: {Go / Refine / Reject}
{Rationale and required actions}
```

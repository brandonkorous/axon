# Release Pipeline Methodology

You are performing a complete release pipeline process that takes code from development through testing, review, versioning, and PR creation with quality gates at every stage.

## Step 1: Pre-flight Checks

Verify the environment is ready for release:

1. **Git platform detection** — identify whether the repository uses GitHub, GitLab, Bitbucket, or another platform by checking remote URLs and CI config files
2. **Base branch identification** — determine the target branch (main, master, develop) from repository conventions or branch protection rules
3. **Working tree status** — verify clean working tree with no uncommitted changes, staged files, or untracked files that should be committed
4. **Branch freshness** — confirm the feature branch is up to date with the base branch; flag if behind by more than 5 commits

Pre-flight checklist:

| Check | Pass Criteria | Fail Action |
|-------|--------------|-------------|
| Clean working tree | No uncommitted changes | Abort — commit or stash first |
| Branch up to date | ≤5 commits behind base | Warn — merge base branch |
| Remote in sync | Local matches remote | Abort — push or pull first |
| Platform detected | Known git platform found | Warn — some automation unavailable |

If any abort-level check fails, stop the pipeline and report what needs to be fixed.

## Step 2: Merge and Test

1. **Merge base branch** into the feature branch to ensure all changes are tested against the latest code
2. **Run the full test suite** — detect the test runner (pytest, jest, vitest, cargo test, go test) from project configuration
3. **Fail fast** — if any test fails, stop the pipeline immediately and report:
   - Which tests failed
   - The failure output
   - Whether the failure is in new code or existing code broken by the merge

Test result classification:

| Result | Action |
|--------|--------|
| All pass | Continue to Step 3 |
| New test fails | Abort — fix before release |
| Existing test fails | Abort — merge conflict or regression |
| No tests found | Warn — continue with coverage audit flagging |

## Step 3: Coverage Audit

Identify test coverage for all new and modified code:

1. **Enumerate new code paths** — list every new function, method, class, endpoint, and conditional branch added or modified
2. **Map to existing tests** — for each code path, find tests that exercise it directly or indirectly
3. **Flag untested paths** — any code path without a corresponding test is flagged with severity:

| Severity | Criteria | Action |
|----------|----------|--------|
| Critical | Public API endpoint, data mutation, auth logic | Block release — test required |
| High | Business logic, state transitions, error handling | Strongly recommend test |
| Medium | Utility functions, formatting, display logic | Recommend test |
| Low | Configuration, constants, type definitions | Note for completeness |

4. **Generate test skeletons** — for each untested critical or high-severity path, produce a minimal test skeleton with:
   - Test function name following project conventions
   - Setup/teardown outline
   - Assertions that need to be filled in
   - Comments explaining what the test should verify

## Step 4: Pre-landing Review

Perform domain-specific safety checks:

### SQL Safety
- Flag any raw SQL in application code (should use parameterized queries)
- Review migration files for destructive operations (DROP, TRUNCATE, column removal)
- Check for missing rollback/down migrations
- Verify migration ordering is consistent

### Data Integrity
- Check for missing null checks on data that could be absent
- Flag writes without corresponding validation
- Identify missing foreign key constraints or orphan potential
- Review transaction boundaries — are multi-step operations atomic?

### API Compatibility
- Detect removed or renamed endpoints
- Flag changed response shapes without versioning
- Check for missing backward compatibility (old clients still work)
- Verify error response format consistency

### Design Review (for UI changes)
- Check for accessibility regressions (missing alt text, aria labels, focus management)
- Flag hardcoded colors or sizes (should use tokens)
- Verify responsive behavior is addressed
- Check loading and error states are handled

## Step 5: Adversarial Review

Scale the review depth by diff size:

### Small diffs (<50 lines): Skip
No adversarial review needed. Pre-landing review is sufficient.

### Medium diffs (50-200 lines): Quick Review
Single pass focusing on:
- Obvious bugs (off-by-one, null derefs, missing error handling)
- Security surface (user input handling, auth checks)
- Performance red flags (N+1 queries, missing indexes, unbounded loops)

### Large diffs (200+ lines): 4-Pass Deep Review

**Pass 1 — Correctness**
- Does the code do what it claims to do?
- Are edge cases handled (empty inputs, max values, concurrent access)?
- Are error paths tested and meaningful?
- Do types and contracts match across boundaries?

**Pass 2 — Security**
- Is user input validated and sanitized at every entry point?
- Are authentication and authorization checks in place?
- Is sensitive data (passwords, tokens, PII) handled correctly?
- Are there injection vectors (SQL, XSS, command injection)?
- Are secrets hardcoded anywhere?

**Pass 3 — Performance**
- Are there N+1 query patterns?
- Are large datasets paginated?
- Is there unnecessary serialization/deserialization?
- Are expensive operations cached where appropriate?
- Are there unbounded growth patterns (lists that grow forever, caches without eviction)?

**Pass 4 — Maintainability**
- Is the code self-documenting or does it need comments?
- Are naming conventions consistent with the codebase?
- Is there unnecessary complexity (abstraction for one use case)?
- Are there magic numbers or strings?
- Does the code follow existing patterns in the project?

Finding severity scale:

| Level | Meaning | Action |
|-------|---------|--------|
| 0 — None | No issues found in this pass | Continue |
| 1 — Nit | Style or preference, not a problem | Note for author |
| 2 — Suggestion | Improvement opportunity, not blocking | Recommend change |
| 3 — Concern | Potential issue that should be addressed | Request change |
| 4 — Blocker | Must be fixed before release | Block release |

## Step 6: Version Management

Determine the version bump:

1. **Auto-bump MICRO/PATCH** when:
   - All changes are bug fixes (fix: prefix)
   - Only documentation or test changes
   - Internal refactoring with no user-facing changes

2. **Ask user for MINOR** when:
   - New features are added (feat: prefix)
   - New API endpoints or UI components
   - New configuration options

3. **Ask user for MAJOR** when:
   - Breaking changes detected (BREAKING CHANGE in commits)
   - Removed API endpoints or features
   - Changed data formats or schemas

If a `version_type` input was provided, use it directly. Otherwise, follow the auto-detection rules above.

Update version in all relevant files:
- package.json, pyproject.toml, Cargo.toml, or equivalent
- Version constants in source code
- Lock files (regenerate, don't edit directly)

## Step 7: Changelog Generation

Generate a changelog from commit messages:

1. **Parse commits** between the last release tag and HEAD
2. **Group by conventional commit prefix**:
   - **Features** (feat:) — new capabilities
   - **Fixes** (fix:) — bug fixes
   - **Refactoring** (refactor:) — code improvements without behavior change
   - **Documentation** (docs:) — documentation changes
   - **Chores** (chore:) — maintenance, dependencies, tooling
3. **Breaking Changes** section — any commit with BREAKING CHANGE in the body gets a separate top-level section
4. **Format** each entry as: `- {scope}: {description} ({short hash})`
5. **Polish** — remove duplicate entries, fix capitalization inconsistencies, ensure descriptions are user-facing language (not developer jargon)

## Step 8: TODO Detection

Scan the codebase for TODO-related changes:

1. **Completed TODOs** — find TODO comments that are now addressed by the changes in this release
2. **Mark completed** — stamp with version and date: `// DONE(v1.2.3, 2024-01-15): original TODO text`
3. **New TODOs** — find any TODO comments introduced in this release; list them for awareness
4. **Stale TODOs** — flag TODOs older than 3 months that remain unaddressed

## Step 9: Commit Organization

Ensure commits are logically bisectable:

1. **Review commit history** — examine all commits in the branch
2. **Verify independence** — each commit should build and pass tests independently
3. **Recommend squash candidates** — identify fixup commits, WIP commits, or "oops" commits that should be squashed
4. **Recommend split candidates** — identify commits that change unrelated things and should be split
5. **Suggest reorder** — if commit order doesn't tell a logical story, suggest a better sequence

Commit quality criteria:

| Quality | Criteria |
|---------|----------|
| Good | Single purpose, builds alone, message explains why |
| Acceptable | Slightly broad but coherent, builds alone |
| Needs work | Multiple purposes, or doesn't build alone, or unclear message |

## Step 10: PR/MR Creation

Generate a comprehensive PR body:

1. **Summary** — 2-3 sentence description of what this release contains and why
2. **Changes** — bulleted list of significant changes (not every commit, grouped logically)
3. **Test coverage** — coverage audit summary showing what's tested and what's not
4. **Review findings** — any concerns or suggestions from the adversarial review
5. **Changelog** — the generated changelog from Step 7
6. **Completed TODOs** — list of TODOs resolved in this release
7. **Version** — the new version number and bump justification

## Quality Gates

The pipeline will not produce a final PR body unless:

| Gate | Requirement |
|------|-------------|
| Tests pass | All tests green after merge |
| No critical findings | No level-4 blockers from adversarial review |
| No critical coverage gaps | All critical-severity code paths have tests |
| Version determined | Version bump decided and applied |
| Verification evidence | Each gate has documented pass/fail evidence |

If any gate fails, the pipeline output includes the failure reason and what needs to be fixed before retrying.

## Output Structure

Produce a structured report with these sections:

1. **Pre-flight**: pass/fail for each check with details
2. **Test results**: suite name, pass count, fail count, skip count, duration
3. **Coverage audit**: table of new code paths with test status and severity
4. **Pre-landing findings**: categorized by domain (SQL, data, API, design)
5. **Adversarial findings**: categorized by pass (correctness, security, performance, maintainability) with severity levels
6. **Version**: old version → new version, bump type, justification
7. **Changelog**: formatted changelog ready to paste
8. **TODO status**: completed, new, and stale TODOs
9. **Commit quality**: assessment of each commit with recommendations
10. **PR body**: complete, ready-to-paste PR description
11. **Gate status**: pass/fail summary for all quality gates

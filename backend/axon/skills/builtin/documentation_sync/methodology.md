# Documentation Sync Methodology

You are performing a post-release documentation synchronization that cross-references code changes against all project documentation to detect staleness, apply factual corrections, and flag narrative changes for user review.

## Phase 1: Branch Safety

Before making any changes:

1. **Check current branch** — refuse to proceed if on the base branch (main, master, develop). Documentation sync must happen on a feature branch.
2. **Verify clean state** — no uncommitted changes that would be mixed with doc updates.

If on the base branch, stop immediately and instruct the user to create a feature branch first.

## Phase 2: Documentation Discovery

Locate all documentation files in the project:

1. **Root-level docs** — README.md, ARCHITECTURE.md, CONTRIBUTING.md, CLAUDE.md, CHANGELOG.md, LICENSE
2. **API documentation** — OpenAPI/Swagger specs, API reference files, endpoint documentation
3. **Inline documentation** — docstrings, JSDoc comments, type annotations with descriptions
4. **Configuration docs** — .env.example, docker-compose comments, deployment guides
5. **User guides** — docs/ directory, wiki content, tutorial files

If `docs_paths` input is provided, limit the scan to those paths. Otherwise, scan the full project.

Build a documentation inventory:

| File | Type | Last Modified | Sections |
|------|------|--------------|----------|
| README.md | Root | date | Setup, Usage, API, ... |
| ... | ... | ... | ... |

## Phase 3: Change Analysis

Parse the release changes to understand what documentation might be affected:

1. **File path changes** — renamed, moved, or deleted files that docs might reference
2. **CLI command changes** — modified command names, flags, or output formats
3. **API changes** — new, modified, or removed endpoints
4. **Feature changes** — new features added, features removed, behavior changes
5. **Configuration changes** — new env vars, changed defaults, removed options
6. **Dependency changes** — added or removed dependencies that affect setup instructions
7. **Structure changes** — directory reorganization, new modules, renamed components

## Phase 4: Cross-reference Audit

For each documentation file, check every factual claim against the current codebase:

### Auto-detectable Staleness

| Signal | Check Method |
|--------|-------------|
| File paths | Verify every referenced path exists in the codebase |
| CLI commands | Verify commands match current implementation |
| Version numbers | Compare against package.json, pyproject.toml, etc. |
| Feature counts | Count actual features and compare to documented numbers |
| Project structure trees | Generate current tree and diff against documented tree |
| Component/module lists | Enumerate actual components and compare |
| Import paths | Verify documented imports resolve correctly |
| Environment variables | Cross-check .env.example against documented vars |

### Cross-document Consistency

- Check that the same fact isn't stated differently in two documents
- Verify CHANGELOG entries match README feature claims
- Ensure CONTRIBUTING.md setup steps match README setup steps

## Phase 5: Auto-apply Corrections

Apply these factual corrections without user approval:

1. **File paths** — update paths that changed to their new locations
2. **Version numbers** — update to current version where version is stated as a fact
3. **CLI commands** — fix command syntax to match current implementation
4. **Feature counts** — update counts (e.g., "supports 5 formats" → "supports 7 formats")
5. **Project structure trees** — regenerate from current directory structure
6. **Component lists** — update to reflect current components
7. **Completed TODO items** — stamp with version and date: `DONE(vX.Y.Z, YYYY-MM-DD)`
8. **CHANGELOG voice polish** — fix wording, grammar, and consistency without changing content or meaning

For each auto-applied change, record:
- What was changed
- Old value → new value
- Which document and line
- Why it was changed (which code change triggered it)

## Phase 6: Prompt for User Decision

Flag these changes for user review — do NOT auto-apply:

### Requires Approval

| Change Type | Why User Decides |
|-------------|-----------------|
| Narrative or philosophy changes | Tone and framing are authorial choices |
| Security model updates | Security documentation must be deliberate |
| Large section rewrites | Scope too broad for auto-correction |
| Section removals | Removing docs is destructive |
| VERSION bump decisions | User controls release versioning |
| New TODO items in code | User should triage priority |
| Cross-document contradictions | User decides which version is correct |
| New feature documentation | User decides depth and framing |
| Architecture description changes | Structural narratives need human judgment |

For each flagged item, provide:
- **What**: the specific change needed
- **Why**: what code change makes this necessary
- **Suggestion**: a proposed edit the user can accept, modify, or reject
- **Impact**: what happens if this isn't updated (confusing instructions, broken setup, etc.)

## Phase 7: Coverage Gap Analysis

Identify documentation that should exist but doesn't:

1. **New features without docs** — features added in this release with no corresponding documentation
2. **New configuration without docs** — new env vars, config files, or options not documented anywhere
3. **New API endpoints without docs** — endpoints added without API reference entries
4. **Removed features still documented** — features removed but docs still describe them

For each gap:
- Describe what documentation is needed
- Suggest where it should live (which file, which section)
- Provide a draft if the information can be inferred from the code

## Rules

- Never regenerate CHANGELOG from scratch — only append, polish wording, or fix formatting
- Never auto-apply narrative changes — these require human judgment
- Require approval for all version bumps, even if the version is obviously wrong
- Always operate on a feature branch — refuse to modify docs on the base branch
- Preserve the author's voice — when polishing, match the existing tone and style
- When in doubt, flag for user review rather than auto-applying
- Track every change with before/after evidence — the user must be able to audit what was changed and why

## Output Structure

Produce a structured report with these sections:

1. **Branch check**: current branch name, safety status
2. **Documentation inventory**: table of all docs found with type and last modified date
3. **Auto-applied updates**: list of factual corrections made, with old → new values and justification
4. **User prompts**: list of changes requiring approval, with what/why/suggestion/impact for each
5. **Stale references**: list of documentation references that no longer match the codebase
6. **Coverage gaps**: list of missing documentation with suggestions for where and what to write
7. **Cross-document issues**: contradictions or inconsistencies found across multiple documents

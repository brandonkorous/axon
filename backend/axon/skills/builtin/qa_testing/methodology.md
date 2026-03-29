# QA Testing Methodology

You are performing a systematic quality assurance review, testing an application for functional correctness, visual consistency, and user experience issues.

## Step 1: Mode Selection

Select the testing mode based on input or context:

| Mode | Scope | Duration Target | Includes |
|------|-------|----------------|----------|
| Quick | Smoke test — homepage + top 5 navigation targets | ~30 seconds | Critical path only |
| Standard | Full systematic exploration with issue documentation | ~5 minutes | All visible pages and flows |
| Exhaustive | Includes cosmetic and low-severity issues | ~15 minutes | Every state, edge case, and minor defect |
| Regression | Compare against baseline to show fixed/broken | ~5 minutes | Baseline comparison, delta report |
| Diff-aware | Auto-focus on pages affected by code changes | ~3 minutes | Changed files mapped to affected pages |

If mode is not specified, default to **standard**.

## Step 2: Test Planning

### Quick Mode
1. Load homepage — verify render, no console errors, all assets load
2. Navigate to top 5 pages — verify each loads, no broken links
3. Test primary CTA (call to action) — verify it works
4. Check responsive layout at 3 breakpoints (mobile 375px, tablet 768px, desktop 1440px)
5. Check for JavaScript console errors

### Standard Mode
All quick mode tests, plus:
1. **Navigation audit** — every link in the navigation works and leads to the correct page
2. **Form testing** — submit with valid data, invalid data, and empty data
3. **Interactive elements** — buttons, dropdowns, modals, tooltips, accordions
4. **User workflows** — complete end-to-end flows (signup, login, CRUD operations, checkout)
5. **Error states** — trigger error conditions and verify user-facing messages
6. **Empty states** — verify behavior with no data
7. **Loading states** — verify skeleton/spinner behavior during async operations

### Exhaustive Mode
All standard mode tests, plus:
1. **Cosmetic review** — alignment, spacing, typography consistency
2. **Cross-browser** — test in multiple browser engines if possible
3. **Keyboard navigation** — tab through every interactive element
4. **Screen reader** — verify ARIA labels and announcement order
5. **Performance** — note slow pages (>3s load time)
6. **Copy review** — typos, grammar, inconsistent terminology
7. **Edge cases** — extremely long text, special characters, rapid clicking, back button behavior

### Regression Mode
1. Parse baseline results into a comparable format
2. Re-test every issue from the baseline
3. Classify each baseline issue as: **Fixed**, **Still broken**, or **Regressed** (was working, now broken)
4. Test for new issues not in baseline
5. Produce delta report

### Diff-Aware Mode
1. Identify changed files from the feature branch
2. Map changed files to affected pages/components
3. Focus testing on affected areas
4. Run quick mode on unaffected pages (sanity check)

## Step 3: What to Test

### Visual Layout & Responsiveness
- Elements align to the grid
- No horizontal scrollbar on any viewport width
- Images and media are responsive (not overflowing containers)
- Text is readable at all breakpoints
- Touch targets are at least 44x44px on mobile

### Interactive Elements
- **Buttons**: click, hover, focus, disabled states all work
- **Forms**: validation on submit, inline validation, error clearing on re-input
- **Navigation**: dropdowns open/close, mobile menu toggles, active state reflects current page
- **Modals/Dialogs**: open, close via X, close via overlay click, close via Escape key, focus trap
- **Tabs/Accordions**: switch content, keyboard accessible, ARIA states update

### Console Errors & Exceptions
- Zero console errors in normal usage
- No unhandled promise rejections
- No React key warnings or hydration mismatches
- No deprecated API warnings in production builds

### Broken Links & 404s
- Every `<a>` tag leads to a valid destination
- No images return 404
- No API calls return unexpected errors
- External links open in new tabs (if appropriate)

### User Workflows
Test complete end-to-end flows:
- **Authentication**: signup, login, logout, password reset, session expiry
- **CRUD**: create, read, update, delete for every entity type
- **Search**: query, filter, sort, paginate, empty results
- **Checkout** (if applicable): add to cart, update quantity, apply coupon, complete payment

### Framework-Specific Checks
- **Next.js**: hydration errors, missing `use client` directives, static/dynamic rendering issues
- **React**: key warnings, state update on unmounted component, infinite re-renders
- **Rails**: N+1 queries in development logs, CSRF token issues, flash message display
- **General**: mixed content warnings (HTTP on HTTPS), CORS errors, cookie issues

## Step 4: Bug Documentation

Every discovered issue must include:

| Field | Description |
|-------|-------------|
| ID | Sequential identifier (BUG-001) |
| Title | One-line summary |
| Severity | Critical / High / Medium / Low |
| Page/Component | Where the bug occurs |
| Reproducibility | Always / Sometimes / Rare |
| Steps | Numbered reproduction steps |
| Expected | What should happen |
| Actual | What actually happens |
| Screenshot | Visual evidence (if applicable) |
| Console output | Error messages (if applicable) |
| Source location | File and line number responsible |

### Severity Definitions

| Severity | Description | Examples |
|----------|-------------|---------|
| Critical | Core functionality broken, data loss, security issue | Login fails, data not saved, XSS vulnerability |
| High | Major feature broken, significant UX issue | Form submit silently fails, layout completely broken on mobile |
| Medium | Feature partially broken, workaround exists | Dropdown misaligned, validation message unclear |
| Low | Cosmetic, minor inconvenience | Slightly off spacing, minor typo, tooltip flicker |

## Step 5: Bug Fixing Workflow

When fixing discovered bugs:

1. **Locate** — find the responsible source code (file and line)
2. **Understand** — determine root cause, not just symptoms
3. **Fix minimally** — one issue per commit. Do not bundle fixes.
4. **Evidence** — capture before and after state (screenshots, console output)
5. **Regression test** — write or describe a test that prevents recurrence

### Fix Documentation

| Field | Description |
|-------|-------------|
| Bug ID | Which bug this fixes |
| File changed | Path to modified file |
| Root cause | Why the bug existed |
| Fix applied | What was changed |
| Before | State before fix |
| After | State after fix |
| Regression test | How to verify it stays fixed |

## Step 6: Health Score Calculation

Calculate a health score (0-100) across 8 weighted categories:

| Category | Weight | Scoring |
|----------|--------|---------|
| Core functionality | 25 | Deduct 25 per critical bug, 10 per high |
| Visual consistency | 15 | Deduct 5 per visual regression, 2 per minor inconsistency |
| Responsive design | 15 | Deduct 10 per broken breakpoint, 3 per minor issue |
| Forms & validation | 10 | Deduct 10 per broken form, 3 per validation gap |
| Navigation & links | 10 | Deduct 5 per broken link, 2 per navigation issue |
| Performance | 10 | Deduct 5 per page >3s load, 2 per page >2s load |
| Accessibility | 10 | Deduct 5 per keyboard trap, 3 per missing ARIA |
| Console cleanliness | 5 | Deduct 3 per error, 1 per warning |

Score starts at 100 and deductions are applied. Minimum score is 0.

| Score Range | Rating | Interpretation |
|-------------|--------|---------------|
| 90-100 | Excellent | Ship-ready with confidence |
| 75-89 | Good | Minor issues, safe to ship with known defects |
| 50-74 | Needs work | Significant issues that should be addressed |
| 25-49 | Poor | Major problems, not ready to ship |
| 0-24 | Critical | Fundamental issues, requires immediate attention |

## Output Structure

```markdown
## QA Report: {Subject}

**Mode**: {quick/standard/exhaustive/regression/diff-aware}
**Health Score**: {0-100} — {rating}
**Issues Found**: {count} ({critical}/{high}/{medium}/{low})

### Health Breakdown
| Category | Score | Issues |
|----------|-------|--------|
| Core functionality | {/25} | {summary} |
| Visual consistency | {/15} | {summary} |
| Responsive design | {/15} | {summary} |
| Forms & validation | {/10} | {summary} |
| Navigation & links | {/10} | {summary} |
| Performance | {/10} | {summary} |
| Accessibility | {/10} | {summary} |
| Console cleanliness | {/5} | {summary} |

### Issues

#### BUG-{NNN}: {Title}
- **Severity**: {level}
- **Page**: {location}
- **Steps**: {reproduction steps}
- **Expected**: {expected behavior}
- **Actual**: {actual behavior}
- **Source**: {file:line}

{Repeat for all issues}

### Fixes Applied
| Bug | File | Root Cause | Fix | Regression Test |
|-----|------|-----------|-----|-----------------|
| BUG-{NNN} | {file} | {cause} | {fix} | {test} |

### Baseline Comparison (regression mode only)
| Status | Count | Details |
|--------|-------|---------|
| Fixed | {n} | {list} |
| Still broken | {n} | {list} |
| New issues | {n} | {list} |
| Regressions | {n} | {list} |
```

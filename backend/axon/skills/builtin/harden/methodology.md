# Harden Methodology

You are performing a production-resilience audit to identify vulnerabilities that only surface outside the happy path — real users, real data, real failures.

---

## Step 1: Establish Scope

Identify the subject under review: a full interface, a single component, or a system flow. Determine which of the five hardening dimensions apply. If a `focus` parameter is provided, deep-dive on that dimension only; otherwise assess all five.

**Core philosophy:** "Designs that only work with perfect data aren't production-ready." Test against extremes, not just happy paths.

---

## Step 2: Text Overflow Management

Evaluate how the interface handles text that exceeds expected lengths.

### Checks

- **Truncation strategy**: Are long strings truncated with ellipsis? Is the full text accessible via tooltip or expansion?
- **Wrapping behavior**: Do multi-line strings wrap correctly without breaking layout?
- **Single long words**: Does a 60-character unbroken string (e.g., a German compound noun or URL) cause horizontal overflow?
- **Dynamic containers**: Do flex/grid containers accommodate variable text without collapsing or overflowing?
- **User-generated content**: Are display names, comments, and titles constrained? What happens with 500-character inputs?

### Scoring

| Rating | Criteria |
|--------|----------|
| Pass | All text containers handle overflow gracefully; truncation is consistent; full text is accessible |
| Partial | Most containers handle overflow but 1-2 edge cases break layout |
| Fail | Text overflow causes horizontal scrolling, layout breaking, or content hidden without access |

### Common Fixes

- Apply `overflow: hidden; text-overflow: ellipsis; white-space: nowrap` for single-line truncation
- Use `overflow-wrap: break-word` for user-generated content areas
- Set `max-width` or `min-width: 0` on flex children
- Add `title` attributes or expand-on-click for truncated content

---

## Step 3: Internationalization (i18n)

Evaluate readiness for multilingual and multi-locale deployment.

### Text Expansion

Translated text is longer than English. Plan for these expansion ratios:

| English Length | Expected Expansion |
|---------------|-------------------|
| 1-10 chars | 200-300% |
| 11-20 chars | 180-200% |
| 21-30 chars | 160-180% |
| 31-50 chars | 140-160% |
| 51-70 chars | 130-140% |
| 70+ chars | 130% |

### RTL Language Support

- Is `dir="rtl"` supported at the document or component level?
- Are layouts mirrored correctly (navigation, icons with directional meaning, progress bars)?
- Are CSS logical properties used (`margin-inline-start` vs `margin-left`)?

### Locale-Sensitive Formats

- **Dates**: Does the interface use locale-aware formatting (DD/MM/YYYY vs MM/DD/YYYY)?
- **Numbers**: Are decimal separators and thousands groupings locale-aware (1,234.56 vs 1.234,56)?
- **Currency**: Is currency symbol placement flexible (prefix vs suffix)?
- **Pluralization**: Does copy handle plural rules beyond simple singular/plural (zero, one, two, few, many, other)?

### Scoring

| Rating | Criteria |
|--------|----------|
| Pass | Layouts accommodate 40% text expansion; logical properties used; locale formats supported |
| Partial | Some expansion tolerance but tight layouts break; RTL not considered; hardcoded formats |
| Fail | Fixed-width containers; no RTL support; hardcoded date/number formats |

---

## Step 4: Error Resilience

Evaluate how the interface responds to failures at every layer.

### Network Failures

- What does the user see when the API is unreachable? Is there a retry mechanism?
- Are failed requests retried with exponential backoff?
- Is there an offline indicator or graceful degradation?

### API Errors

- Are 4xx errors (validation, auth, not found) presented with actionable messages?
- Are 5xx errors caught and shown as "temporary issue, retry later" rather than stack traces?
- Are error responses parsed and displayed contextually (inline vs toast vs full-page)?

### Permission Denied

- Does the UI handle 403 gracefully? Are unauthorized actions hidden or disabled with explanation?
- Is there a clear path to request access or understand why access is denied?

### Timeouts

- Are long-running requests bounded by a timeout?
- Is there feedback during long waits (spinner, progress, cancel option)?
- Does the interface recover gracefully from timeout without corrupted state?

### Scoring

| Rating | Criteria |
|--------|----------|
| Pass | All failure modes produce user-friendly feedback; retry mechanisms exist; state remains consistent |
| Partial | Common errors handled but edge failures show raw errors or blank screens |
| Fail | Errors produce white screens, console errors, or silent failures; no retry or recovery |

---

## Step 5: Edge Cases

Evaluate behavior at the boundaries of expected usage.

### Empty States

- Do lists, tables, and dashboards have meaningful empty states?
- Do empty states explain value and provide a clear action ("No projects yet. Create your first project")?
- Are empty states distinct from loading states and error states?

### Loading States

- Are skeleton screens or shimmer effects used instead of spinners for content areas?
- Is loading state shown within 200ms of request initiation?
- Are partial results displayed as they arrive (progressive loading)?

### Large Datasets

- What happens with 1,000+ items in a list or table? Is pagination or virtualization implemented?
- Do charts and visualizations handle 10,000+ data points without freezing?
- Are search and filter operations performant at scale?

### Concurrent Edits

- Is there conflict detection when two users edit the same resource?
- Are stale data warnings shown when underlying data changes?
- Is optimistic UI used with proper rollback on conflict?

### Stale Data

- Are timestamps shown to indicate data freshness?
- Is there a refresh mechanism (manual or automatic)?
- Do cached views indicate when they were last updated?

### Scoring

| Rating | Criteria |
|--------|----------|
| Pass | Empty, loading, and error states are distinct and helpful; large datasets handled; concurrency addressed |
| Partial | Basic empty states exist but loading/error states conflated; no large dataset strategy |
| Fail | No empty states; loading spinners only; tables crash with large data; no concurrency handling |

---

## Step 6: Input Protection

Evaluate defenses against malicious or malformed input.

### XSS (Cross-Site Scripting)

- Is user-generated content sanitized before rendering?
- Are template engines auto-escaping HTML by default?
- Is `dangerouslySetInnerHTML` or equivalent used? If so, is input sanitized with a library like DOMPurify?

### SQL Injection

- Are all database queries parameterized?
- Are ORMs used consistently, or are there raw query escape hatches?

### File Upload Validation

- Are file types validated on both client and server?
- Are file sizes bounded with clear limits shown to the user?
- Are uploaded filenames sanitized to prevent path traversal?

### Rate Limiting

- Are form submissions rate-limited to prevent spam?
- Are API endpoints protected against brute-force attempts?
- Is there CAPTCHA or equivalent for public-facing forms?

### Scoring

| Rating | Criteria |
|--------|----------|
| Pass | Input sanitized; queries parameterized; uploads validated; rate limiting in place |
| Partial | Some sanitization but gaps exist; file uploads partially validated; no rate limiting |
| Fail | Raw user input rendered; SQL injection possible; no upload validation; no rate limiting |

---

## Step 7: Dimension Summary Scoring

Rate each dimension as Pass (1), Partial (0.5), or Fail (0).

| Dimension | Score | Key Findings |
|-----------|-------|-------------|
| Text Overflow | 0 / 0.5 / 1 | ... |
| Internationalization | 0 / 0.5 / 1 | ... |
| Error Resilience | 0 / 0.5 / 1 | ... |
| Edge Cases | 0 / 0.5 / 1 | ... |
| Input Protection | 0 / 0.5 / 1 | ... |
| **Total** | **X / 5** | |

**Coverage bands:**

| Score | Rating |
|-------|--------|
| 5 | Production-hardened — robust across all dimensions |
| 4 | Strong — one dimension needs attention |
| 3 | Moderate — multiple gaps to address before production |
| 2 | Weak — significant vulnerabilities in most dimensions |
| 0-1 | Critical — not production-ready |

---

## Output Structure

1. **Scope**: What was assessed and which dimensions were evaluated.
2. **Vulnerabilities**: Each finding includes dimension, what was found, why it matters, and severity (P0-P3).
3. **Dimension Scorecard**: Table with per-dimension pass/partial/fail and key findings.
4. **Coverage Score**: Total dimensions passing (0-5) with rating band.
5. **Hardening Plan**: Prioritized list of fixes, grouped by dimension, each with what/why/how-to-fix.
6. **Quick Wins**: 2-3 highest-impact, lowest-effort fixes to implement first.

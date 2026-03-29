# Canary Monitoring Methodology

You are performing post-deploy canary monitoring, watching production for a defined window after deployment to catch regressions before they affect all users.

## Step 1: Pre-Deploy Baseline Capture

Before deployment, capture the current state as a baseline:

### Visual Baseline
For each monitored page:
- Full-page screenshot at desktop viewport (1440px)
- Full-page screenshot at mobile viewport (375px)
- Key component screenshots (navigation, hero, footer, forms)

### Performance Baseline
For each monitored page:
- Page load time (TTFB, FCP, LCP, Full Load)
- Total resource count and transfer size
- JavaScript error count (should be zero)

### Error Baseline
- Current console errors across all pages (document existing errors to distinguish from new ones)
- Current broken links or 404s
- Current API error rates

## Step 2: Page Discovery

Determine which pages to monitor:

### Auto-Discovery
1. Parse sitemap.xml for all public pages
2. Crawl navigation to find linked pages
3. Identify critical pages from application routes

### Prioritization
If too many pages for the monitoring window, prioritize:

| Priority | Page Type | Rationale |
|----------|-----------|-----------|
| P0 | Homepage | First impression, highest traffic |
| P0 | Login/signup | Authentication is critical |
| P0 | Checkout/payment | Revenue-generating |
| P1 | Dashboard/main app | Core user experience |
| P1 | API health endpoint | Backend availability |
| P2 | Settings/profile | Important but lower traffic |
| P2 | Documentation | Used but less critical |
| P3 | Marketing pages | Lower priority during deploy |

### Custom Page List
Accept user-provided page list and merge with auto-discovered critical pages.

## Step 3: Monitoring Loop

### Timing
- Default monitoring window: 10 minutes
- Check interval: every 60 seconds
- Total checks: ~10 per page

### Each Check Cycle

For each monitored page, perform:

1. **Load test** — navigate to page, record load time
2. **Visual capture** — take screenshot for comparison
3. **Console scan** — collect all console errors and warnings
4. **Network scan** — check for failed requests (4xx, 5xx)
5. **Content verification** — verify key elements are present (navigation, main content, footer)

### Transient Tolerance

To avoid false positives from temporary hiccups (deploy in progress, cache warming, CDN propagation):

**Rule: Only alert on issues that persist in 2 or more consecutive checks.**

| Check 1 | Check 2 | Action |
|---------|---------|--------|
| Error | No error | Transient — do not alert |
| Error | Error | Persistent — alert |
| No error | Error | Watch — check again next cycle |
| Slow | Slow | Persistent degradation — alert |
| Slow | Normal | Transient — do not alert |

Record transient issues in the log but do not escalate them to alerts.

## Step 4: Alert Classification

### Severity Levels

| Severity | Condition | Example |
|----------|-----------|---------|
| CRITICAL | Page load failure or timeout (entire page broken) | 500 error, blank page, DNS failure |
| HIGH | New console errors absent from baseline | TypeError, unhandled rejection, module not found |
| MEDIUM | Performance regression (2x+ slower than baseline) | LCP went from 1.5s to 3.5s |
| LOW | Broken links or 404s for non-critical resources | Missing image, broken stylesheet |

### Alert Format

Each alert includes:

| Field | Description |
|-------|-------------|
| Severity | CRITICAL / HIGH / MEDIUM / LOW |
| Page | Which page is affected |
| Issue | What was detected |
| Baseline | What the baseline value was |
| Current | What the current value is |
| First seen | Which check cycle first detected it |
| Persistent | How many consecutive checks show this issue |
| Evidence | Screenshot, console output, or network log |

## Step 5: Visual Regression Detection

Compare current screenshots against pre-deploy baseline:

### Comparison Method
1. **Pixel diff** — overlay current on baseline, highlight changed pixels
2. **Structural diff** — compare DOM structure for added/removed/moved elements
3. **Content diff** — compare text content for unexpected changes

### Visual Change Classification

| Classification | Description | Alert Level |
|---------------|-------------|-------------|
| Layout break | Elements significantly repositioned or overlapping | CRITICAL |
| Missing content | Visible content from baseline is absent | HIGH |
| Style regression | Colors, fonts, or spacing changed unexpectedly | MEDIUM |
| Content update | Text content changed (may be intentional) | LOW / Ignore |
| Animation diff | Dynamic content differs between captures | Ignore |

### Ignore Zones
Exclude dynamic content areas from visual comparison:
- Timestamps and dates
- User-specific content (avatars, names)
- Ad slots or third-party widgets
- Random/rotating content (testimonials, hero images)

## Step 6: Error Tracking

### New Error Detection
Compare console errors against baseline:

1. **Classify each error**:
   - **New**: Not present in baseline → alert
   - **Existing**: Present in baseline → ignore (already known)
   - **Resolved**: In baseline but no longer present → positive signal

2. **Error details**:
   - Error message and stack trace
   - Frequency (how many times per check)
   - Page(s) affected
   - Browser/viewport where it occurs

### Error Pattern Detection
- **Cascade**: One error causing downstream errors
- **Intermittent**: Error appears and disappears across checks
- **Progressive**: Error frequency increasing over monitoring window

## Step 7: Performance Tracking

### Metric Comparison
For each page and metric, compare against baseline:

| Metric | Baseline | Current | Delta | Status |
|--------|----------|---------|-------|--------|
| TTFB | {ms} | {ms} | {+/-ms} | {OK/Degraded/Critical} |
| FCP | {ms} | {ms} | {+/-ms} | {OK/Degraded/Critical} |
| LCP | {ms} | {ms} | {+/-ms} | {OK/Degraded/Critical} |
| Total requests | {n} | {n} | {+/-n} | {OK/Degraded/Critical} |
| Transfer size | {KB} | {KB} | {+/-KB} | {OK/Degraded/Critical} |

### Degradation Thresholds
- **OK**: Within 20% of baseline
- **Degraded**: 20-100% slower than baseline (MEDIUM alert)
- **Critical**: 2x+ slower than baseline or timeout (HIGH alert)

### Timeline Tracking
Record metrics at each check interval to detect trends within the monitoring window:

```
LCP over monitoring window:
3.0s |
2.5s |  ● ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ budget
2.0s |
1.5s |  ●  ●  ●  ●
1.0s |                 ●  ●  ●  ●  ●  ●
0.5s |
     └──────────────────────────────────
      +0  +1  +2  +3  +4  +5  +6  +7  +8  +9 min
```

This example shows initial slowness (cache warming) followed by normal performance — a healthy pattern.

## Step 8: Health Status Determination

At the end of the monitoring window, determine overall status:

| Status | Condition |
|--------|-----------|
| **Healthy** | No persistent alerts. All metrics within baseline tolerance. |
| **Degraded** | MEDIUM alerts only. Performance slower but functional. No errors. |
| **Critical** | Any CRITICAL or HIGH alerts that persisted through the monitoring window. |

### Confidence Assessment
- **High confidence**: Monitored for full window, multiple check cycles, consistent results
- **Medium confidence**: Short window or intermittent issues that resolved
- **Low confidence**: Monitoring was interrupted or baseline was unavailable

## Output Structure

```markdown
## Canary Monitor: {Subject}

**Duration**: {monitoring window}
**Pages monitored**: {count}
**Check cycles completed**: {count}
**Health status**: {Healthy / Degraded / Critical}

### Alert Summary
| # | Severity | Page | Issue | First Seen | Persistent |
|---|----------|------|-------|------------|------------|
| 1 | {level} | {page} | {description} | {time} | {yes/no} |

### Visual Baseline Comparison
| Page | Desktop | Mobile | Status |
|------|---------|--------|--------|
| {page} | {match/diff} | {match/diff} | {OK/Regression} |

### Performance Timeline
| Metric | +0m | +2m | +4m | +6m | +8m | +10m | Trend |
|--------|-----|-----|-----|-----|-----|------|-------|
| LCP | {ms} | {ms} | {ms} | {ms} | {ms} | {ms} | {stable/improving/degrading} |

### Error Tracking
| Error | Status | Frequency | Pages |
|-------|--------|-----------|-------|
| {error} | {new/existing/resolved} | {count} | {pages} |

### Transient Issues (not alerted)
| Issue | Occurrences | Resolution |
|-------|-------------|------------|
| {issue} | {count} | {self-resolved after N checks} |

### Recommendation
{Continue monitoring / Safe to proceed / Rollback recommended}
{Specific actions if degraded or critical}
```

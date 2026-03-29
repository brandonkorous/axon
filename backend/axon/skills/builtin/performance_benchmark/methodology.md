# Performance Benchmark Methodology

You are performing a performance benchmark, measuring application speed and resource efficiency to detect regressions and enforce performance budgets.

## Step 1: Mode Selection

| Mode | Purpose | When to Use |
|------|---------|-------------|
| Baseline | Capture current metrics as reference point | First measurement, after major release |
| Quick | Homepage performance snapshot | Daily CI check, quick sanity |
| Diff | Compare current vs. baseline, flag regressions | Feature branches, pre-merge checks |
| Trend | Analyze multiple benchmarks for gradual degradation | Monthly reviews, sprint retrospectives |

Default to **quick** if mode is not specified.

## Step 2: Page Discovery

Determine which pages to benchmark:

1. **Auto-discover** — parse sitemap.xml, crawl navigation links, extract routes from framework config
2. **Custom list** — accept user-provided page list
3. **Priority pages** — if too many pages, prioritize:
   - Homepage (always)
   - Primary landing pages
   - High-traffic pages (from analytics if available)
   - Revenue-generating pages (checkout, pricing)
   - Pages with heavy dynamic content

For quick mode, benchmark homepage only. For other modes, benchmark all discovered pages.

## Step 3: Metrics Collection

### Core Web Vitals

| Metric | Description | Good | Needs Improvement | Poor |
|--------|-------------|------|-------------------|------|
| TTFB | Time to First Byte — server response time | <200ms | 200-600ms | >600ms |
| FCP | First Contentful Paint — first visible content | <1.8s | 1.8-3.0s | >3.0s |
| LCP | Largest Contentful Paint — main content visible | <2.5s | 2.5-4.0s | >4.0s |
| FID/INP | First Input Delay / Interaction to Next Paint | <100ms | 100-300ms | >300ms |
| CLS | Cumulative Layout Shift — visual stability | <0.1 | 0.1-0.25 | >0.25 |

### Extended Timing Metrics

| Metric | Description | Budget |
|--------|-------------|--------|
| DOM Interactive | DOM is parsed and ready for interaction | <2.0s |
| DOM Complete | DOM and all sub-resources loaded | <4.0s |
| Full Load | All resources including async | <6.0s |
| Time to Interactive | Page is fully interactive | <3.5s |

### Resource Analysis

Break down resources by type:

| Resource Type | Count | Transfer Size | Uncompressed Size |
|---------------|-------|--------------|-------------------|
| HTML | {n} | {KB} | {KB} |
| CSS | {n} | {KB} | {KB} |
| JavaScript | {n} | {KB} | {KB} |
| Images | {n} | {KB} | {KB} |
| Fonts | {n} | {KB} | {KB} |
| Other | {n} | {KB} | {KB} |
| **Total** | {n} | {KB} | {KB} |

### Network Summary
- Total requests
- Total transfer size
- Requests by domain (first-party vs. third-party)
- Blocking resources (render-blocking CSS/JS)
- Third-party script impact (time contribution)

## Step 4: Performance Budgets

Check against standard budgets:

| Metric | Budget | Actual | Status |
|--------|--------|--------|--------|
| LCP | <2.5s | {value} | Pass/Warn/Fail |
| FID/INP | <100ms | {value} | Pass/Warn/Fail |
| CLS | <0.1 | {value} | Pass/Warn/Fail |
| Total JS | <250KB | {value} | Pass/Warn/Fail |
| Total CSS | <100KB | {value} | Pass/Warn/Fail |
| Total images | <500KB | {value} | Pass/Warn/Fail |
| Total requests | <50 | {value} | Pass/Warn/Fail |
| Total transfer | <1MB | {value} | Pass/Warn/Fail |

Budget status:
- **Pass**: Within budget
- **Warn**: Within 20% of budget limit
- **Fail**: Exceeds budget

## Step 5: Regression Detection (Diff Mode)

Compare current metrics against baseline:

### Regression Thresholds

| Change | Severity | Description |
|--------|----------|-------------|
| >50% timing increase | Critical | Major performance regression |
| >25% timing increase | Warning | Notable degradation, investigate |
| >25% bundle growth | Warning | Significant asset growth |
| New blocking resource | Alert | New render-blocking asset detected |
| New third-party script | Alert | New external dependency |
| >10% request count increase | Info | More network activity |

### Per-Metric Comparison

| Metric | Baseline | Current | Delta | Status |
|--------|----------|---------|-------|--------|
| {metric} | {value} | {value} | {+/-value} ({%}) | {OK/Warning/Critical} |

### Root Cause Analysis

For each detected regression:
1. **What changed** — identify the specific resource, script, or configuration change
2. **Why it matters** — user-facing impact (slower load, layout shift, delayed interactivity)
3. **How to fix** — specific remediation steps

Common regression causes:
- New JavaScript bundle or larger existing bundle
- Unoptimized images added
- New third-party script (analytics, chat widget, A/B testing)
- Missing code splitting (loading everything upfront)
- Lost caching headers (re-downloading cached assets)
- Database query slowdown (backend TTFB increase)
- Missing compression (gzip/brotli not configured)

## Step 6: Resource Optimization Analysis

Identify specific optimization opportunities:

### Slowest Resources
List the top 10 slowest-loading resources with:
- URL or filename
- Size (transfer and uncompressed)
- Load time
- Whether it is render-blocking
- Optimization recommendation (compress, lazy load, defer, remove)

### Third-Party Script Impact
For each third-party script:
- Domain and purpose
- Load time contribution
- Whether it blocks rendering
- Whether it could be deferred or removed

### Unused Resources
Identify loaded but unused resources:
- CSS rules that never match (unused CSS percentage)
- JavaScript modules imported but not executed
- Fonts loaded but not used on the page
- Images below the fold loaded eagerly (should be lazy)

## Step 7: Trend Analysis (Trend Mode)

When multiple benchmark snapshots are available:

### Gradual Degradation Detection
- Compare metrics across snapshots chronologically
- Flag metrics that are slowly increasing (frog-in-boiling-water pattern)
- Example: LCP was 1.2s three months ago, 1.5s two months ago, 1.8s last month, 2.1s now — each change was small but the trend is concerning

### Trend Visualization

```
LCP over time:
2.5s ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ budget line ─ ─ ─ ─ ─
     |
2.0s |                              ●
     |                        ●
1.5s |                  ●
     |            ●
1.0s |      ●
     |  ●
0.5s |
     └──────────────────────────────────────────
      Jan   Feb   Mar   Apr   May   Jun
```

### Trend Summary
- Metrics improving: list with rate of improvement
- Metrics stable: list
- Metrics degrading: list with rate of degradation and projected date they will exceed budget

## Output Structure

```markdown
## Performance Benchmark: {Subject}

**Mode**: {baseline/quick/diff/trend}
**Pages tested**: {count}
**Date**: {timestamp}

### Core Web Vitals
| Metric | Value | Budget | Status |
|--------|-------|--------|--------|
| TTFB | {value} | <200ms | {status} |
| FCP | {value} | <1.8s | {status} |
| LCP | {value} | <2.5s | {status} |
| FID/INP | {value} | <100ms | {status} |
| CLS | {value} | <0.1 | {status} |

### Resource Breakdown
| Type | Count | Size | Budget | Status |
|------|-------|------|--------|--------|
| JS | {n} | {KB} | <250KB | {status} |
| CSS | {n} | {KB} | <100KB | {status} |
| Images | {n} | {KB} | <500KB | {status} |
| Total | {n} | {KB} | <1MB | {status} |

### Regressions (diff mode)
| Metric | Baseline | Current | Delta | Severity |
|--------|----------|---------|-------|----------|
| {metric} | {value} | {value} | {change} | {level} |

### Optimization Opportunities
| Resource | Issue | Impact | Fix |
|----------|-------|--------|-----|
| {resource} | {problem} | {savings estimate} | {remediation} |

### Trend Analysis (trend mode)
| Metric | 3mo Ago | 2mo Ago | 1mo Ago | Now | Trend |
|--------|---------|---------|---------|-----|-------|
| {metric} | {value} | {value} | {value} | {value} | {improving/stable/degrading} |

### Budget Status
{count} of {total} budgets passing
{list of failing budgets with remediation priorities}
```

# Optimize Performance Methodology

You are performing a comprehensive performance audit and optimization pass across loading speed, rendering efficiency, animation smoothness, and Core Web Vitals targets.

**Core principle:** Measure first, optimize second. Never optimize without identifying the actual bottleneck. The biggest gains come from fixing the biggest problems, not micro-optimizing what is already fast.

---

## Step 1: Profile — Establish Baseline

Before any optimization, establish current performance state.

### Core Web Vitals Targets

| Metric | Good        | Needs Improvement | Poor        | What It Measures                      |
|--------|-------------|-------------------|-------------|---------------------------------------|
| LCP    | < 2.5s      | 2.5s - 4.0s      | > 4.0s      | Largest Contentful Paint — perceived load speed |
| FID    | < 100ms     | 100ms - 300ms     | > 300ms     | First Input Delay — input responsiveness |
| INP    | < 200ms     | 200ms - 500ms     | > 500ms     | Interaction to Next Paint — overall responsiveness |
| CLS    | < 0.1       | 0.1 - 0.25       | > 0.25      | Cumulative Layout Shift — visual stability |
| TTFB   | < 800ms     | 800ms - 1800ms    | > 1800ms    | Time to First Byte — server responsiveness |
| FCP    | < 1.8s      | 1.8s - 3.0s      | > 3.0s      | First Contentful Paint — initial render |
| TBT    | < 200ms     | 200ms - 600ms     | > 600ms     | Total Blocking Time — main thread blocking |

### Profiling Approach
- Analyze the code for known performance patterns and anti-patterns
- Identify resource sizes (images, JS bundles, CSS, fonts)
- Note rendering patterns (DOM complexity, re-render frequency, layout triggers)
- Check animation implementation (GPU vs. CPU properties)
- Review network strategy (caching, preloading, lazy loading)

---

## Step 2: Loading Performance

### Image Optimization

| Technique         | Impact  | Implementation                                      |
|-------------------|---------|-----------------------------------------------------|
| Modern formats    | High    | WebP for photos, AVIF for high quality, SVG for icons |
| Responsive images | High    | `srcset` + `sizes` for viewport-appropriate sizes   |
| Lazy loading      | High    | `loading="lazy"` for below-fold images              |
| Dimension hints   | Medium  | Always specify `width` + `height` to prevent CLS    |
| Priority loading  | Medium  | `fetchpriority="high"` for LCP image                |
| Placeholder       | Medium  | Blur-up or dominant color placeholder while loading |

**Quick check:** Is the LCP element an image? If so, it should not be lazy-loaded. Use `fetchpriority="high"` and preload it.

### JavaScript Bundle Optimization

| Technique         | Impact  | Implementation                                      |
|-------------------|---------|-----------------------------------------------------|
| Code splitting    | High    | Route-based splitting, dynamic imports for heavy modules |
| Tree shaking      | High    | Ensure build tool eliminates dead code              |
| Dependency audit  | High    | Replace heavy libraries with lighter alternatives   |
| Defer/async       | Medium  | `defer` for non-critical scripts, `async` for independent |
| Compression       | Medium  | Brotli (preferred) or gzip for all text assets      |
| Bundle analysis   | —       | Use bundle visualizer to identify largest modules   |

**Common heavy dependencies to audit:**
- Moment.js (replace with date-fns or dayjs)
- Lodash (import individual functions, not entire library)
- Full icon libraries (import only used icons)
- Polyfills for features already supported by target browsers

### CSS Optimization

| Technique         | Impact  | Implementation                                      |
|-------------------|---------|-----------------------------------------------------|
| Critical CSS      | High    | Inline above-fold CSS, defer the rest               |
| Unused CSS        | Medium  | Remove unused rules (PurgeCSS or framework equivalent) |
| CSS containment   | Medium  | `contain: layout style paint` for isolated components |
| Minification      | Low     | Ensure build pipeline minifies CSS                  |

### Font Optimization

| Technique         | Impact  | Implementation                                      |
|-------------------|---------|-----------------------------------------------------|
| font-display:swap | High    | Prevents invisible text while font loads             |
| Subset fonts      | High    | Only include characters actually used                |
| Preload           | Medium  | `<link rel="preload">` for critical fonts           |
| Variable fonts    | Medium  | One file instead of multiple weight files            |
| System font stack | —       | Consider whether custom fonts are truly necessary    |

### Caching Strategy

| Resource Type    | Cache Strategy                                           |
|------------------|----------------------------------------------------------|
| HTML             | No cache or short TTL (< 5min) — always fresh            |
| CSS/JS (hashed)  | Immutable, long TTL (1 year) — filename changes on update |
| Images           | Long TTL (1 month+) with versioned URLs                  |
| Fonts            | Long TTL (1 year) — fonts rarely change                  |
| API responses    | Stale-while-revalidate where applicable                  |

---

## Step 3: Rendering Performance

### Layout Thrashing Prevention

Layout thrashing occurs when JavaScript reads layout properties (offsetWidth, getBoundingClientRect) then writes style changes in a loop, forcing the browser to recalculate layout multiple times.

**Detection:**
- Look for interleaved reads and writes to DOM in loops
- Check for forced synchronous layouts (read after write without frame boundary)
- Identify components that measure DOM in render or effect hooks

**Fixes:**
- Batch all reads, then batch all writes
- Use `requestAnimationFrame` to defer writes to next frame
- Cache layout measurements instead of re-reading
- Use CSS for layout when possible instead of JavaScript measurement

### DOM Complexity

| Metric          | Good        | Warning       | Critical      |
|-----------------|-------------|---------------|---------------|
| DOM nodes       | < 800       | 800 - 1500    | > 1500        |
| DOM depth       | < 15 levels | 15 - 25       | > 25          |
| Child elements  | < 60 per parent | 60 - 120  | > 120         |

**Fixes for excessive DOM:**
- Virtual scrolling for long lists (render only visible items)
- Pagination instead of infinite scroll for very large datasets
- Component lazy loading for off-screen sections
- Remove wrapper divs that serve no structural purpose

### Re-render Optimization
- Memoize expensive computations
- Use stable references for callbacks and objects passed as props
- Implement shouldComponentUpdate or memo for pure components
- Avoid creating new objects/arrays in render (triggers child re-renders)
- Move static elements outside components that re-render frequently

---

## Step 4: Animation Performance

### GPU-Composited Properties Only
Animations should only use properties that can be GPU-composited:

| Safe (GPU)                     | Unsafe (CPU layout trigger)           |
|--------------------------------|---------------------------------------|
| `transform: translate()`       | `top`, `left`, `right`, `bottom`      |
| `transform: scale()`          | `width`, `height`                      |
| `transform: rotate()`         | `margin`, `padding`                    |
| `opacity`                      | `border-width`, `font-size`           |

### Animation Performance Checklist
- [ ] All animations use transform/opacity only
- [ ] `will-change` applied before animation, removed after
- [ ] No JavaScript-driven animations that could be CSS
- [ ] requestAnimationFrame used for JS animations (never setTimeout)
- [ ] Animations tested at 4x CPU throttle
- [ ] Stagger sequences capped at 5 items with 50ms delay
- [ ] prefers-reduced-motion respected

### Scroll Performance
- Use `passive: true` on scroll event listeners
- Implement `IntersectionObserver` instead of scroll-position checks
- Use CSS `scroll-snap` instead of JavaScript scroll management where possible
- Apply `contain: strict` on scrollable containers
- Avoid heavy computation in scroll handlers

---

## Step 5: Resource Analysis

### Identify the Biggest Bottleneck

Rank all resources by their impact on the critical path:

1. **Render-blocking resources**: CSS and synchronous JS in `<head>`
2. **LCP resource**: Whatever paints the largest contentful element
3. **Largest JS bundle**: The heaviest script download
4. **Third-party scripts**: Analytics, ads, tracking that block or delay
5. **Largest images**: Unoptimized images above the fold

**The 80/20 rule applies:** 20% of resources cause 80% of performance issues. Find and fix the biggest offenders first.

### Code Splitting Strategy

| Split Point          | When to Split                                          |
|----------------------|--------------------------------------------------------|
| Routes               | Each route loads only its own code                     |
| Heavy features       | Features with large dependencies (charts, editors, maps)|
| Below-fold content   | Content not visible on initial load                    |
| Conditional features | Features behind feature flags or permissions           |
| Modals/dialogs       | Loaded only when triggered                             |

---

## Step 6: Optimization Prioritization

Order all optimizations by impact-to-effort ratio:

| Priority | Category                                           | Typical Impact     |
|----------|----------------------------------------------------|--------------------|
| 1        | Remove render-blocking resources                   | 500ms-2s LCP      |
| 2        | Optimize LCP element (image, text, or element)     | 500ms-1.5s LCP    |
| 3        | Code split largest bundle                          | 200ms-1s load     |
| 4        | Lazy load below-fold images                        | 100-500KB savings  |
| 5        | Add font-display:swap and preload critical fonts   | 200-500ms FCP     |
| 6        | Fix layout thrashing                               | 50-200ms INP      |
| 7        | Replace heavy dependencies                         | 50-200KB savings   |
| 8        | Implement virtual scrolling for long lists         | 100-500ms render   |
| 9        | GPU-accelerate animations                          | Smooth 60fps       |
| 10       | Add caching headers                                | Repeat visit speed |

---

## Output Structure

1. **Baseline Metrics**: Current or estimated values for LCP, FID/INP, CLS, TTFB, FCP, TBT, bundle size, and image weight.
2. **Bottleneck Ranking**: Top 5 performance bottlenecks ordered by impact, each with what it is, why it matters, and measured/estimated cost.
3. **Optimization Plan**: Prioritized list of all recommended optimizations, each with:
   - What to change
   - Expected improvement (quantified where possible)
   - Implementation complexity (low/medium/high)
   - Dependencies (what must be done first)
4. **Resource Audit**: Breakdown of largest resources (JS bundles, images, CSS, fonts) with sizes and optimization opportunities.
5. **Animation Audit**: List of animations with current implementation and GPU-acceleration status.
6. **Code Splitting Opportunities**: Identified split points with estimated bundle savings.
7. **Expected Improvement Summary**: Before/after projections for key metrics after implementing the full plan.
8. **Quick Wins**: Top 3 changes that can be made immediately with minimal effort and maximum impact.

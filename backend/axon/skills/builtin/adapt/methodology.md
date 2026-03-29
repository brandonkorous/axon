# Adapt Methodology

You are performing a cross-device and cross-context adaptation assessment to ensure the interface delivers an appropriate experience across all target environments.

---

## Step 1: Context Identification

Determine which contexts apply. If `target_contexts` is provided, focus on those. Otherwise, assess all relevant contexts based on the subject type.

**Default context set:** mobile, tablet, desktop. Add print and email only when the subject involves printable content or email-rendered HTML.

**Core philosophy:** "Adaptation is not just scaling — it's rethinking the experience for each context." Each context has unique constraints and opportunities.

---

## Step 2: Mobile Assessment (< 640px)

Mobile is the foundation. Design here first, then enhance upward.

### Requirements

- **Single column layout**: Content stacks vertically. No side-by-side panels that require horizontal scrolling.
- **Touch targets**: All interactive elements are at minimum 44x44px with adequate spacing between targets (minimum 8px gap).
- **Progressive disclosure**: Show essential information first. Secondary details behind taps, accordions, or drill-down views.
- **Bottom navigation**: Primary navigation is thumb-reachable. Top-of-screen-only navigation is a failure on tall devices.
- **Input optimization**: Use appropriate input types (`tel`, `email`, `date`). Avoid dropdowns with 20+ options — use search or type-ahead instead.
- **Viewport handling**: Content is readable without zooming. No fixed-width elements that cause horizontal scroll.

### Common Mobile Failures

- Touch targets below 44px (especially inline links and icon buttons)
- Hover-dependent interactions with no tap alternative
- Fixed headers consuming more than 15% of viewport height
- Modals that don't adapt to mobile (full-screen takeover preferred)
- Form fields too small to tap accurately

---

## Step 3: Tablet Assessment (640px - 1024px)

Tablets occupy a hybrid space. Neither phone nor desktop — leverage the extra space without desktop assumptions.

### Requirements

- **Split views**: Use the available width for master-detail patterns where appropriate.
- **Flexible grids**: 2-column layouts for content that was single-column on mobile.
- **Touch and pointer**: Support both touch and trackpad/mouse input. Don't assume either exclusively.
- **Orientation support**: Layout should work in both portrait and landscape without breaking.
- **Sidebar navigation**: Can introduce sidebar navigation that was bottom-bar on mobile.

---

## Step 4: Desktop Assessment (> 1024px)

Desktop provides the most space and precision. Use it to increase density and efficiency.

### Requirements

- **Multi-column layouts**: Use available width for information density — sidebars, panels, multi-column grids.
- **Hover states**: Provide hover feedback on interactive elements. Reveal secondary actions on hover.
- **Keyboard shortcuts**: Power users expect keyboard navigation. Tab order, hotkeys, search-to-navigate.
- **Data density**: Show more data per screen — wider tables, denser dashboards, expanded details inline.
- **Max content width**: Constrain reading content to 65-75ch. Don't let paragraphs stretch across 1920px screens.

---

## Step 5: Print Context

When content may be printed (reports, invoices, articles, documentation).

### Requirements

- **Remove navigation**: Hide all nav, sidebars, and interactive elements via `@media print`.
- **High contrast**: Ensure text is black on white. Remove background colors that waste ink.
- **Page breaks**: Use `break-before`, `break-after`, `break-inside` to control content flow across pages.
- **Expand collapsed content**: Accordions, tabs, and truncated text should be fully expanded in print.
- **Show URLs**: Display link URLs after anchor text using `a[href]::after { content: " (" attr(href) ")"; }`.
- **Remove fixed elements**: Sticky headers and floating buttons should not repeat on every page.

---

## Step 6: Email Context

When content is rendered in email clients (newsletters, notifications, transactional emails).

### Requirements

- **Table-based layout**: Email clients have inconsistent CSS support. Use HTML tables for structural layout.
- **Inline styles**: Most email clients strip `<style>` blocks. Critical styles must be inline.
- **Image fallbacks**: Always provide alt text. Design should be readable with images blocked.
- **Width constraint**: Design for 600px max width. Mobile email clients will scale down.
- **Font stacks**: Use web-safe fallbacks. Custom fonts are unreliable in email.
- **Link styling**: Ensure links are visually distinct — some clients override link colors.

---

## Step 7: Capability-Based Queries

Beyond viewport size, assess capability-aware adaptation.

### Pointer Precision

```css
@media (pointer: fine) { /* mouse/trackpad — smaller targets OK */ }
@media (pointer: coarse) { /* touch — 44px minimum targets */ }
```

### Hover Availability

```css
@media (hover: hover) { /* device supports hover — enable hover states */ }
@media (hover: none) { /* no hover — provide tap alternatives */ }
```

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) { /* minimize or remove animations */ }
```

### Container Queries

For component-level adaptation independent of viewport:

```css
.card-container { container-type: inline-size; }
@container (min-width: 400px) { /* wider layout within the container */ }
```

Container queries enable components to adapt based on their own available space, not the viewport. This is critical for reusable components placed in varying contexts.

---

## Step 8: Breakpoint Strategy

Define content-driven breakpoints rather than device-driven.

### Recommended Breakpoints

| Breakpoint | Width | Typical Use |
|-----------|-------|-------------|
| sm | 640px | Single to two-column transition |
| md | 768px | Tablet portrait, sidebar introduction |
| lg | 1024px | Desktop baseline, multi-column |
| xl | 1280px | Wide desktop, increased density |
| 2xl | 1536px | Ultra-wide, max content width enforcement |

**Content-driven principle:** Breakpoints should be placed where the content breaks, not at arbitrary device widths. If a layout looks good at 800px and breaks at 850px, the breakpoint is 850px.

### Fluid Sizing

Use `clamp()` for fluid typography and spacing:

```css
font-size: clamp(1rem, 0.5rem + 1.5vw, 1.5rem);
padding: clamp(1rem, 3vw, 3rem);
```

---

## Step 9: Scoring Per Context

For each assessed context, rate adaptation quality:

| Rating | Score | Criteria |
|--------|-------|----------|
| Excellent | 4 | Fully adapted for context; leverages context-specific opportunities |
| Good | 3 | Works well in context; minor issues or missed opportunities |
| Acceptable | 2 | Functional but feels like a scaled version, not a native experience |
| Poor | 1 | Major usability issues in this context; clearly an afterthought |
| Broken | 0 | Unusable in this context; layout breaks, interactions fail |

---

## Output Structure

1. **Context Scope**: Which contexts were assessed and why.
2. **Issues Per Context**: For each context — what breaks, what's suboptimal, what's missing. Each issue includes what/why/how-to-fix.
3. **Breakpoint Strategy**: Recommended breakpoints with rationale, including fluid sizing approach.
4. **Adaptation Plan**: Prioritized list of changes per context, ordered by impact. Each item specifies the context, the change, and implementation approach.
5. **Capability Queries**: Recommended capability-based media queries and container query opportunities.
6. **What's Working**: 2-3 things already adapting well across contexts.

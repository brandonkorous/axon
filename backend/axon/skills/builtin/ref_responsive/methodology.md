# Responsive Design Reference Methodology

You are performing a responsive design reference consultation, providing guidance on mobile-first strategy, breakpoints, capability queries, fluid design, touch targets, safe areas, and device testing.

## Section 1: Mobile-first Strategy

Write base styles for mobile, then layer on complexity with `min-width` media queries. This ensures the simplest, most constrained experience is the default, and wider screens receive enhancements.

**Why mobile-first**: mobile CSS is simpler (single column, stacked layout, full-width elements). Desktop CSS adds complexity (multi-column, sidebars, hover states). Loading simple first and adding complexity is more resilient than loading complex first and stripping it away.

```css
/* Base: mobile */
.layout { display: flex; flex-direction: column; }

/* Enhancement: wider screens */
@media (min-width: 768px) {
  .layout { flex-direction: row; }
}
```

**Common mistake**: writing desktop-first and using `max-width` queries to handle mobile. This results in more overrides, more code, and a fragile cascade where mobile styles fight desktop defaults.

## Section 2: Content-driven Breakpoints

### Standard Breakpoints

| Name | Width | Typical Devices |
|------|-------|----------------|
| Small | 640px | Large phones, small tablets in portrait |
| Medium | 768px | Tablets in portrait, small laptops |
| Large | 1024px | Tablets in landscape, standard laptops |
| XL | 1280px | Desktops, wide laptops |
| 2XL | 1536px | Large desktop monitors |

### Content-driven Approach

Standard breakpoints are starting points, not rules. Break when the content breaks:

1. Start at the smallest viewport
2. Slowly widen the browser
3. When a layout element breaks (text too wide, images too small, whitespace excessive), add a breakpoint at THAT width
4. The breakpoint values will be specific to your content, not to device categories

**Example**: if a card grid looks good at 1 column up to 520px and needs 2 columns after that, use `520px` as the breakpoint — not `640px` just because it is a standard value.

## Section 3: Capability Queries

Target device capabilities, not screen sizes:

| Query | Detects | Use For |
|-------|---------|---------|
| `@media (pointer: fine)` | Mouse/trackpad (precise pointing) | Smaller click targets, hover-dependent UI |
| `@media (pointer: coarse)` | Touch screen (imprecise pointing) | Larger touch targets, swipe gestures |
| `@media (hover: hover)` | Device supports hover | Hover effects, tooltip triggers |
| `@media (hover: none)` | No hover (touch only) | Alternatives to hover interactions |
| `@media (any-pointer: fine)` | At least one precise input | Hybrid devices (tablet + mouse) |

**Critical rule**: never rely on hover for functionality. Hover can enhance (show a preview, highlight a target) but must not be required (the only way to access a menu, reveal a button). Users with `hover: none` devices must have full functionality.

```css
/* Show on hover for mouse users, always visible for touch */
.action-button { opacity: 1; }

@media (hover: hover) {
  .action-button { opacity: 0; }
  .card:hover .action-button { opacity: 1; }
}
```

## Section 4: Fluid Design

Use `clamp()`, `min()`, and `max()` for sizes that smoothly scale with the viewport:

| Function | Syntax | Use Case |
|----------|--------|----------|
| `clamp()` | `clamp(min, preferred, max)` | Sizes that scale but stay within bounds |
| `min()` | `min(a, b)` | Take the smaller of two values |
| `max()` | `max(a, b)` | Take the larger of two values |

**Common patterns**:

```css
/* Container that scales but never exceeds 1200px or goes below 320px */
width: clamp(320px, 90vw, 1200px);

/* Padding that scales with container */
padding: clamp(16px, 4vw, 48px);

/* Font that scales between 1rem and 2rem */
font-size: clamp(1rem, 0.5rem + 2vw, 2rem);
```

**Avoid hardcoded pixel widths** for layout elements. A `width: 800px` sidebar breaks on narrow screens. Use `width: min(800px, 100%)` or `width: clamp(200px, 30vw, 400px)` instead.

## Section 5: Touch Targets

Minimum touch target sizes ensure usability for all finger sizes and motor abilities:

| Standard | Minimum Size | Source |
|----------|-------------|--------|
| Apple HIG | 44 × 44px | Apple Human Interface Guidelines |
| Material Design | 48 × 48dp | Google Material Design |
| WCAG 2.2 | 24 × 24px (target), 44 × 44px (recommended) | Web Content Accessibility Guidelines |

**Spacing between targets**: minimum 8px gap between adjacent touch targets. Without gaps, users accidentally tap neighboring targets.

**Expanding touch targets**: the visual element can be smaller than the touch target. Use padding or `::before`/`::after` pseudo-elements to expand the tappable area beyond the visible element.

```css
.small-icon-button {
  width: 24px;
  height: 24px;
  position: relative;
}

.small-icon-button::before {
  content: '';
  position: absolute;
  inset: -12px; /* Expands touch target to 48x48 */
}
```

**Labels expand targets**: a text label next to an icon should be part of the same tappable area. Wrap both in the interactive element, not just the icon.

## Section 6: Safe Area Handling

Modern devices have notches, dynamic islands, rounded corners, and home indicators that overlap content.

```css
/* Use env() for safe areas */
padding-top: env(safe-area-inset-top);
padding-bottom: env(safe-area-inset-bottom);
padding-left: env(safe-area-inset-left);
padding-right: env(safe-area-inset-right);
```

**Critical for**:
- Fixed bottom navigation (home indicator overlap)
- Fixed headers (notch/dynamic island overlap)
- Full-width backgrounds (rounded corner clipping)
- Landscape orientation (notch on the side)

**Enable safe area support** in the viewport meta tag:
```html
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
```

Without `viewport-fit=cover`, the browser adds its own padding and `env(safe-area-inset-*)` values are 0.

## Section 7: Testing

### Minimum Test Viewports

| Width | Device | Priority |
|-------|--------|----------|
| 375px | iPhone SE / Small phones | High — minimum viable width |
| 390px | iPhone 14 / Standard phones | High — most common phone |
| 768px | iPad / Tablets | Medium — tablet portrait |
| 1024px | Laptop / Tablet landscape | Medium — compact desktop |
| 1440px | Desktop / External monitors | High — standard desktop |

### Testing Checklist

| Check | Method |
|-------|--------|
| Text readable at all widths | Visual inspection at each breakpoint |
| No horizontal scroll | Verify `overflow-x` is controlled |
| Touch targets adequate | Check 44px minimum on coarse pointer |
| Images scale correctly | Verify no overflow or distortion |
| Navigation accessible | Menu works at all breakpoints |
| Forms usable | Inputs don't zoom on iOS, labels visible |
| Safe areas respected | Test on notched devices or simulator |

### Orientation

Test both portrait and landscape. Common failures:
- Fixed-height elements overflow in landscape on phones
- Modals become unusable in landscape on short viewports
- Keyboard open + landscape = almost no visible content — handle gracefully

## Output Structure

When providing responsive design guidance:

1. **Context assessment**: what the user is building and their current responsive approach
2. **Breakpoint strategy**: recommended breakpoints based on their content
3. **Fluid values**: specific `clamp()` / `min()` / `max()` expressions for their use case
4. **Touch considerations**: target sizes and spacing for touch interaction
5. **Testing priorities**: which viewports and orientations to verify

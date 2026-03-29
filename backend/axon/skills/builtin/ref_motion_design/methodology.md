# Motion Design Reference Methodology

You are performing a motion design reference consultation, providing guidance on animation timing, easing functions, GPU performance, accessibility, and interaction feedback thresholds.

## Section 1: Timing Rules

Every animation must have a justifiable duration. Too fast feels broken, too slow feels sluggish.

| Category | Duration | Examples | Rationale |
|----------|----------|----------|-----------|
| Feedback | 100-150ms | Button press, toggle, hover highlight, checkbox | User expects instant response — just enough to register |
| State change | 200-300ms | Accordion open/close, tab switch, card flip, tooltip | Content is changing but layout is stable |
| Layout shift | 300-500ms | Page transition, panel slide, sidebar resize, reorder | Layout is changing — user needs time to reorient |
| Entrance | 500-800ms | Fade in, staggered list, hero animation, skeleton → content | New content appearing — draw attention without blocking |

**Hard ceiling**: never exceed 1000ms for any single animation. Anything longer feels like a loading state, not a transition. If the transition genuinely takes longer (e.g., complex data visualization), show the end state quickly and animate details afterward.

**Compound animations**: when multiple properties animate together (e.g., scale + opacity), use the same duration for all properties. Mismatched durations create a "swimming" effect.

## Section 2: Easing Strategy

Easing determines character. The wrong easing makes a technically correct animation feel wrong.

| Easing | CSS Value | Use When |
|--------|-----------|----------|
| ease-out (decelerate) | `cubic-bezier(0.0, 0.0, 0.2, 1)` | Elements APPEARING — entering viewport, expanding, fading in |
| ease-in (accelerate) | `cubic-bezier(0.4, 0.0, 1, 1)` | Elements DISAPPEARING — leaving viewport, collapsing, fading out |
| ease-in-out | `cubic-bezier(0.4, 0.0, 0.2, 1)` | Elements TOGGLING — switch states, morph, reposition |
| linear | `linear` | Progress bars, continuous rotation, loading spinners only |

**Memory rule**: objects enter with ease-out (they decelerate as they arrive, like catching a ball), objects leave with ease-in (they accelerate as they depart, like throwing a ball). Toggling uses ease-in-out because the element is both leaving one state and arriving at another.

**Custom curves**: for premium feel, use slightly more pronounced curves:
- Snappy ease-out: `cubic-bezier(0.0, 0.0, 0.1, 1)` — arrives fast, settles gently
- Bouncy entrance: `cubic-bezier(0.34, 1.56, 0.64, 1)` — slight overshoot, use sparingly
- Smooth toggle: `cubic-bezier(0.45, 0.0, 0.15, 1)` — balanced acceleration/deceleration

## Section 3: GPU Acceleration

Only two CSS properties animate on the GPU compositing layer without triggering layout recalculation:

| Property | GPU Accelerated | Layout Cost |
|----------|----------------|-------------|
| `transform` | Yes | None — composited |
| `opacity` | Yes | None — composited |
| `width` / `height` | No | Full layout recalculation |
| `padding` / `margin` | No | Full layout recalculation |
| `top` / `left` / `right` / `bottom` | No | Full layout recalculation |
| `border-radius` | No | Repaint only |
| `background-color` | No | Repaint only |

**Translation**: use `transform: translateX()` instead of animating `left`. Use `transform: scale()` instead of animating `width/height`. Use `opacity` instead of `visibility` for show/hide.

**will-change**: use `will-change: transform` sparingly — it promotes the element to its own compositing layer, which uses GPU memory. Only apply it to elements that are about to animate, and remove it after animation completes. Never put `will-change` on more than a handful of elements simultaneously.

**Measuring**: if an animation drops below 60fps, open the browser performance panel and look for long "Layout" or "Recalculate Style" blocks. These indicate you are animating layout-triggering properties.

## Section 4: Reduced Motion

Respecting `prefers-reduced-motion` is not optional — it is an accessibility requirement.

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### What to Change Under Reduced Motion

| Animation Type | Reduced Motion Behavior |
|---------------|------------------------|
| Decorative (parallax, background movement, hover effects) | Remove entirely |
| Feedback (button press, toggle) | Replace with opacity-only, 0ms duration |
| State change (accordion, tab) | Instant switch, no transition |
| Informational (progress bar, loading spinner) | Keep — user needs this information |
| Entrance (fade in, stagger) | Show immediately without animation |

**Key principle**: reduced motion does not mean no change — it means no movement. Opacity changes (fade) are generally acceptable. Spatial movement (slide, scale, rotate) should be removed.

## Section 5: Stagger Caps

Staggered animations (items appearing one after another) create visual rhythm but become tedious at scale.

| Rule | Value | Reasoning |
|------|-------|-----------|
| Maximum items in a stagger | 5 | Beyond 5, the user is waiting, not enjoying |
| Delay between items | 50ms | Fast enough to feel connected, slow enough to perceive |
| Maximum total stagger duration | 300ms | 5 items × 50ms + last item's animation |
| Items beyond 5 | Appear simultaneously | Group or paginate the rest |

**Alternative for long lists**: stagger the first 3-5 items, then show the rest instantly. The initial stagger establishes the pattern; the brain fills in the rhythm for the remaining items.

**Stagger direction**: top-to-bottom or leading-edge-first. Follow the natural reading direction of the layout. Never stagger from the center outward unless the design specifically calls for a radial reveal.

## Section 6: The 80ms Threshold

Interaction response time determines perceived quality:

| Response Time | Perception | Example |
|---------------|------------|---------|
| <80ms | Instant — feels like direct manipulation | Button highlight, toggle switch |
| 80-150ms | Fast — slight delay but acceptable | Dropdown open, filter apply |
| 150-300ms | Noticeable — needs visual feedback | Search results, form validation |
| 300-1000ms | Slow — needs progress indication | API call, file upload start |
| >1000ms | Waiting — needs progress bar or skeleton | Page load, complex computation |

**Target 80ms** for all immediate interactions: button state changes, toggle switches, checkbox marks, radio selections, hover effects. These are the interactions users perform most often, and sub-80ms response makes the entire interface feel responsive.

**For 150ms+ interactions**: show a visual state change within 80ms even if the result is not ready. For example, a search button should change appearance immediately on click, even if search results take 500ms to load.

## Output Structure

When providing motion design guidance:

1. **Context assessment**: what the user is animating and why
2. **Timing recommendation**: specific duration and justification from the timing table
3. **Easing selection**: which curve to use and the CSS value
4. **Performance check**: whether the animated properties are GPU-friendly
5. **Accessibility**: what changes under reduced motion
6. **Code example**: CSS snippet implementing the recommendation

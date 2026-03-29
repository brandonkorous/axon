# Animate Methodology

You are performing a purposeful motion design pass to enhance an interface with animations and micro-interactions that improve usability, provide feedback, and create moments of delight.

**Core principle:** Every animation must have a purpose — feedback, orientation, hierarchy, or delight. Decorative-only motion is noise.

---

## Step 1: Prepare — Context Gathering

Before adding any motion, understand the context:

### Interface Inventory
- What are the primary user actions on this screen?
- What state changes occur (loading, success, error, navigation)?
- What elements appear, disappear, or transform?
- What is the current motion situation (no motion, some motion, excessive motion)?

### Motion Style Assessment
Determine the appropriate intensity level:

| Style    | Character                        | Use When                                    |
|----------|----------------------------------|---------------------------------------------|
| Subtle   | Barely noticeable, professional  | Enterprise tools, data-heavy dashboards     |
| Moderate | Noticeable but not distracting   | Most applications, balanced approach        |
| Dramatic | Bold, attention-grabbing         | Marketing sites, creative tools, onboarding |

### Constraints
- Does the product have an existing motion language to match?
- What is the target frame rate (60fps minimum)?
- What devices must be supported (low-end mobile to desktop)?
- Are there performance budgets to respect?

---

## Step 2: Assess — Identify Motion Opportunities

Scan the interface for areas where motion would improve the experience.

### Feedback Opportunities
- Button clicks without visual confirmation
- Form submissions without progress indication
- Toggle switches that snap without transition
- Hover states that appear/disappear instantly

### Orientation Opportunities
- Page transitions with no sense of direction
- Modals/drawers that appear from nowhere
- Tab switches with no connection between content
- List items that pop in without context

### Hierarchy Opportunities
- Important elements that do not draw attention
- Content that loads but does not announce itself
- Notifications that appear without emphasis
- Status changes that go unnoticed

### Delight Opportunities
- Completion moments (task done, goal reached)
- Empty-to-populated state transitions
- First-time experiences worth celebrating
- Subtle personality moments that reinforce brand

---

## Step 3: Strategy — Plan the Motion System

### Identify the Hero Moment
Every screen gets ONE hero moment — the single most impactful animation:
- It should reinforce the primary action or most important state change
- It gets the most attention, the longest duration, the most polish
- Everything else supports it, never competes with it

### Timing Framework

| Category            | Duration    | Use For                                          |
|---------------------|-------------|--------------------------------------------------|
| Micro-feedback      | 100-150ms   | Button press, toggle, checkbox, hover feedback   |
| State changes       | 200-300ms   | Tab switch, dropdown open, tooltip appear         |
| Layout shifts       | 300-500ms   | Accordion expand, panel slide, content reflow    |
| Entrances           | 300-500ms   | Modal open, page transition, drawer slide-in     |
| Complex sequences   | 500-800ms   | Multi-step reveals, celebration moments          |

**The 80ms threshold:** Anything under 80ms feels instant to humans. Use this for micro-feedback that should feel like direct manipulation (button depress, ripple start).

### Easing Rules

| Movement Type      | Easing                | Reason                                          |
|--------------------|-----------------------|-------------------------------------------------|
| Appearing/entering | ease-out (decelerate) | Objects arrive and settle naturally              |
| Disappearing/exit  | ease-in (accelerate)  | Objects pick up speed as they leave              |
| State toggle       | ease-in-out           | Smooth transition between two stable states      |
| Bounce/spring      | Avoid                 | Feels dated and unprofessional in most contexts  |

**Recommended curves:**
- Subtle: `cubic-bezier(0.25, 0.1, 0.25, 1)` (standard ease-out)
- Moderate: `cubic-bezier(0.16, 1, 0.3, 1)` (expressive ease-out)
- Snappy: `cubic-bezier(0.33, 1, 0.68, 1)` (quick settle)

### Stagger Rules
When animating lists or groups of items:
- Maximum 5 items in a stagger sequence (beyond 5, the last items wait too long)
- 50ms delay between items (shorter feels simultaneous, longer feels sluggish)
- Total stagger duration should not exceed 400ms
- Items beyond the stagger cap appear together with the last staggered item

### Layer Planning
Build motion in layers, each adding to the previous:

1. **Layer 1 — Essential feedback:** Button presses, toggle states, form validation. These are non-negotiable.
2. **Layer 2 — State transitions:** Content appearing/disappearing, navigation changes, loading states.
3. **Layer 3 — Orientation:** Page transitions, spatial relationships, scroll-linked effects.
4. **Layer 4 — Delight:** The hero moment, celebration animations, personality touches.

---

## Step 4: Implement — Technical Specifications

### GPU Acceleration Rules
Only animate properties that can be GPU-composited:
- **Safe (GPU):** `transform` (translate, scale, rotate), `opacity`
- **Unsafe (CPU):** `width`, `height`, `margin`, `padding`, `top`, `left`, `border`, `background-color`

If you need to animate size, use `transform: scale()` instead of `width`/`height`.
If you need to animate position, use `transform: translate()` instead of `top`/`left`.
If you need to animate color, crossfade two elements with `opacity` instead.

### Accessibility: prefers-reduced-motion

Every animation must have a reduced-motion alternative:

```
@media (prefers-reduced-motion: reduce) {
  /* Option A: Remove animation entirely */
  * { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }

  /* Option B (preferred): Reduce, don't remove */
  .animated-element {
    transition-duration: 0.1ms;  /* Near-instant but still shows state change */
    animation: none;              /* Remove decorative animations */
  }
}
```

**Rules:**
- Essential state changes (loading indicators, error states) must still be visible
- Decorative motion can be removed entirely
- Orientation animations (slide-in, fade-in) should become instant cuts
- Never remove the semantic meaning that motion conveys — find a static alternative

### Performance Checks
- Use `will-change` sparingly and only on elements about to animate
- Remove `will-change` after animation completes (or use animation events)
- Test on low-end devices (throttle CPU 4x in dev tools)
- Monitor paint counts — animations should not trigger layout or paint on other elements
- Prefer CSS animations over JavaScript for simple transitions
- Use `requestAnimationFrame` for JavaScript-driven animations, never `setTimeout`/`setInterval`

### Animation Anti-Patterns to Avoid
- Bounce/elastic easing (feels dated, rarely appropriate)
- Animating layout properties (causes layout thrashing)
- Using the default `ease` (a compromise that is rarely optimal)
- Animations longer than 800ms (feels sluggish)
- Animations on page load that delay usability
- Infinite animations (spinning logos, pulsing elements) without purpose
- Motion that obscures content or delays interaction

---

## Output Structure

1. **Context Summary**: Interface type, current motion state, recommended style (subtle/moderate/dramatic).
2. **Hero Moment**: The single most impactful animation, fully specified with timing, easing, and purpose.
3. **Motion Plan**: Every animation organized by layer (essential feedback → state transitions → orientation → delight), each with:
   - Element and trigger
   - Animation type (fade, slide, scale, etc.)
   - Duration and easing
   - Purpose (feedback/orientation/hierarchy/delight)
4. **Timing Specifications**: Complete timing table for all animations.
5. **Stagger Sequences**: Any list/group animations with item count, delay, and total duration.
6. **Accessibility Plan**: Reduced-motion alternatives for every animation.
7. **Performance Notes**: GPU acceleration strategy, will-change usage, performance concerns.
8. **Implementation Priority**: Ordered list from most impactful to least, so motion can be added incrementally.

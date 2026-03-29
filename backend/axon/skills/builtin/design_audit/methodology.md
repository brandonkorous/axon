# Design Audit Methodology

You are performing a comprehensive design quality audit. This framework combines anti-pattern detection, quantitative scoring, cognitive load analysis, and persona-based testing to produce an actionable assessment.

Run all applicable sections based on mode: **audit** (Sections 1-3), **critique** (Sections 1, 4-5), or **full** (all sections).

---

## Section 1: AI Slop Detection

**The AI Slop Test:** "If you showed this interface to someone and said 'AI made this,' would they believe immediately? If yes, that's the problem."

Check each category. For every indicator found, note its location and severity.

### Typography Slop
- **Overused fonts**: Inter, Roboto, Arial, Open Sans, Lato, Montserrat, system defaults used without customization. These aren't bad fonts — they're invisible. They signal "I didn't think about typography."
- **Monospace-as-technical**: Using monospace typography as lazy shorthand for "developer/technical" vibes.
- **Large icons with rounded corners above every heading**: Looks templated, rarely adds value.
- **Muddy hierarchy**: Too many font sizes too close together (14px, 15px, 16px, 18px). Good hierarchy uses distinct jumps.
- **Weak weight contrast**: Medium vs. Regular (barely visible difference). Use Regular + Bold, not Regular + Medium.

**Font alternatives for overused defaults:**
- Inter → Instrument Sans, Plus Jakarta Sans, Outfit
- Roboto → Onest, Figtree, Urbanist
- Arial/Helvetica → Geist, Switzer, General Sans
- Open Sans → Source Sans 3, Nunito Sans
- Montserrat → Sora, Lexend, Satoshi

### Color Slop
- **The AI color palette**: cyan-on-dark, purple-to-blue gradients, neon accents on dark backgrounds. This palette screams "generated."
- **Gradient text for impact**: Especially on metrics or headings. Decorative, not meaningful.
- **Default dark mode with glowing accents**: Looks "cool" without requiring actual design decisions.
- **Gray text on colored backgrounds**: Looks washed out and dead.
- **Pure black (#000) or pure white (#fff)**: Never appears in real designed products. Always tint slightly.
- **Pure gray (no chroma)**: Real shadows and surfaces always carry a subtle color cast. Use `oklch` with chroma 0.01+.

### Layout Slop
- **Everything wrapped in cards**: Not everything needs a container. Cards are for distinct, actionable content.
- **Cards nested inside cards**: Visual noise. Flatten the hierarchy.
- **Identical card grids**: Same-sized cards with icon + heading + text, repeated endlessly. The "feature grid" template.
- **The hero metric layout**: Big number, small label, supporting stats, gradient accent. Every AI dashboard looks like this.
- **Center everything**: Left-aligned text with asymmetric layouts feels more designed and intentional.
- **Same spacing everywhere**: Without rhythm (tight spacing vs. generous breathing room), layouts feel monotonous.

### Visual Effects Slop
- **Glassmorphism everywhere**: Blur effects, glass cards, glow borders used decoratively rather than functionally.
- **Rounded elements with thick colored border on one side**: A lazy accent that never looks intentional.
- **Sparklines as decoration**: Tiny charts that look sophisticated but convey no actual information.
- **Rounded rectangles with generic drop shadows**: Safe, forgettable, could be any AI output.
- **Modals used by default**: Modals are lazy UX. Use only when there's truly no inline or panel-based alternative.

### Motion Slop
- **Bounce or elastic easing**: Feels dated and tacky. Real objects decelerate smoothly (ease-out or quart/quint curves).
- **Animating layout properties**: Width, height, padding, margin instead of transform/opacity. Causes layout thrashing.
- **Using `ease`**: It's a compromise that's rarely optimal. Use `ease-out` for entrances, `ease-in` for exits.

### Content/UX Slop
- **Repeating information**: Redundant headers, intros that restate the heading, labels that duplicate placeholder text.
- **Every button is primary**: No hierarchy in button styling. One primary action per view.
- **OK/Submit/Yes/No button labels**: Lazy and ambiguous. Use specific verb + object ("Save changes", "Delete account").
- **Generic error messages**: "Something went wrong", "Invalid input" without specifics. Errors should say what happened, why, and how to fix it.
- **Empty states that just say "nothing here"**: Empty states are onboarding moments — explain value and provide an action.

### Scoring the Anti-Pattern Check
Count total indicators found:
- **0 indicators**: Score 4 — No AI tells. Distinctive, intentional design.
- **1-2 indicators**: Score 3 — Mostly clean. Subtle issues only.
- **3-4 indicators**: Score 2 — Some tells. Noticeable AI aesthetic.
- **5+ indicators**: Score 1 — Heavy AI aesthetic.
- **Pervasive across all categories**: Score 0 — AI slop gallery.

---

## Section 2: Audit Health Score (Technical, 0-20)

Rate each dimension 0-4. Be specific about what you observe.

### Dimension 1: Accessibility (0-4)
- 0: No accessibility consideration. Missing alt text, no keyboard nav, poor contrast.
- 1: Minimal — some alt text, basic heading structure.
- 2: Partial — reasonable contrast, some ARIA, keyboard mostly works.
- 3: Good — meets WCAG AA, semantic HTML, focus management.
- 4: Excellent — WCAG AA+, screen reader tested, skip links, reduced motion support.

**Check:** Contrast ratios (4.5:1 body, 3:1 large/UI), ARIA labels, keyboard navigation, semantic HTML, form labels, alt text, focus indicators.

### Dimension 2: Performance (0-4)
- 0: Major jank. Layout thrashing, expensive animations, no lazy loading.
- 1: Noticeable issues. Some layout property animations, large unoptimized images.
- 2: Acceptable. Minor issues. Could benefit from optimization.
- 3: Good. Transform/opacity animations, lazy loading present, reasonable bundle.
- 4: Excellent. Optimistic UI, progressive loading, code splitting, sub-second interactions.

**Check:** Animation properties used, image optimization, lazy loading, bundle size indicators, unnecessary re-renders.

### Dimension 3: Theming (0-4)
- 0: Hard-coded colors throughout. No theme system.
- 1: Some CSS variables but inconsistent. Dark mode broken.
- 2: Token system exists but has gaps. Some hard-coded values slip through.
- 3: Good token system. Light and dark modes work. Consistent application.
- 4: Two-layer tokens (primitive + semantic). Smooth theme switching. No hard-coded colors.

**Check:** CSS custom properties, hard-coded color values, dark mode support, theme consistency.

### Dimension 4: Responsive Design (0-4)
- 0: Fixed widths. Broken on mobile. Horizontal scrolling.
- 1: Some responsiveness but major breakpoint issues. Tiny touch targets.
- 2: Works on common sizes. Some cramped layouts. Touch targets inconsistent.
- 3: Good across devices. Proper breakpoints. Touch targets ≥44px.
- 4: Fluid layouts. Container queries. Pointer/hover media queries. Safe area handling.

**Check:** Fixed widths, touch targets (<44px is a fail), breakpoints, text scaling, horizontal scroll.

### Dimension 5: Anti-Patterns (0-4)
Use the score from Section 1.

**Total: Sum all 5 dimensions.**

| Range | Rating |
|-------|--------|
| 18-20 | Excellent — minor polish |
| 14-17 | Good — address weak dimensions |
| 10-13 | Acceptable — significant work needed |
| 6-9 | Poor — major overhaul |
| 0-5 | Critical — fundamental issues |

---

## Section 3: Cognitive Load Assessment

Evaluate each item as pass or fail:

1. **Single focus**: Can the user complete the primary task without distraction?
2. **Chunking**: Is information in digestible groups (≤4 items per group)?
3. **Grouping**: Are related items visually grouped (proximity, borders, shared background)?
4. **Visual hierarchy**: Is it immediately clear what's most important?
5. **One thing at a time**: Can the user focus on a single decision before the next?
6. **Minimal choices**: ≤4 visible options at any decision point?
7. **Working memory**: Does the user need to remember information from a previous screen?
8. **Progressive disclosure**: Is complexity revealed only when needed?

**Scoring:** 0-1 failures = low (good), 2-3 = moderate (needs attention), 4+ = critical (redesign needed).

**Named violations** — if you detect these specific patterns, call them out by name:
- **Wall of Options**: 10+ choices with no hierarchy
- **Memory Bridge**: Must remember info from step 1 for step 3
- **Hidden Navigation**: Mental map required to find things
- **Jargon Barrier**: Technical language forces mental translation
- **Visual Noise Floor**: Everything has the same visual weight
- **Inconsistent Pattern**: Similar actions work differently
- **Multi-Task Demand**: Reading + deciding + navigating simultaneously
- **Context Switch**: Must jump between screens for one decision

---

## Section 4: Design Health Score (Nielsen's 10 Heuristics, 0-40)

Rate each heuristic 0-4 with specific observations.

1. **Visibility of System Status** — Loading indicators, confirmations, progress, navigation location, form validation feedback.
2. **Match Between System and Real World** — Terminology, information order, icons, domain language, reading flow.
3. **User Control and Freedom** — Undo/redo, cancel, navigate back, clear filters, escape processes.
4. **Consistency and Standards** — Terminology, behavior, platform conventions, visual consistency, interaction patterns.
5. **Error Prevention** — Confirmations for destructive actions, input constraints, smart defaults, clear labels, autosave.
6. **Recognition Rather Than Recall** — Visible options, contextual help, recent items, autocomplete, labeled icons.
7. **Flexibility and Efficiency** — Keyboard shortcuts, customization, favorites, bulk actions, power user paths.
8. **Aesthetic and Minimalist Design** — Only necessary info, visual hierarchy, purposeful color, no clutter, focused layouts.
9. **Error Recovery** — Plain language errors, specific problem identification, actionable suggestions, non-blocking.
10. **Help and Documentation** — Searchable help, contextual hints, task-focused, concise, accessible.

| Range | Rating |
|-------|--------|
| 36-40 | Excellent — ship it |
| 28-35 | Good — address weak areas |
| 20-27 | Acceptable — significant improvements needed |
| 12-19 | Poor — major UX overhaul |
| 0-11 | Critical — redesign needed |

---

## Section 5: Persona Testing

Select 2-3 personas most relevant to the interface type and identify specific red flags.

### Alex (Impatient Power User)
Tests: speed, keyboard nav, bulk actions, efficiency.
**Red flags:** Forced tutorials, no keyboard shortcuts, slow unskippable animations, one-at-a-time workflows, redundant confirmations.

### Jordan (Confused First-Timer)
Tests: discoverability, onboarding, clarity.
**Red flags:** Icon-only navigation, technical jargon, no help option, ambiguous next steps, no success confirmation.

### Sam (Accessibility-Dependent)
Tests: screen reader flow, keyboard-only operation, contrast.
**Red flags:** Click-only interactions, missing focus indicators, color-only meaning, unlabeled buttons, time-limited actions.

### Riley (Stress Tester)
Tests: error handling, edge cases, resilience.
**Red flags:** Silent failures, technical error messages, useless empty states, data loss on refresh, inconsistent behavior.

### Casey (Distracted Mobile User)
Tests: touch targets, state persistence, progressive loading.
**Red flags:** Important actions at screen top only, no state persistence, text inputs instead of selection, heavy assets, tiny tap targets.

**Selection guide:**
- Dashboards/admin: Alex + Sam
- E-commerce/consumer: Casey + Riley + Jordan
- Forms/onboarding: Jordan + Sam
- Data-heavy/enterprise: Alex + Riley

---

## Issue Severity Classification

Every finding gets a severity:

| Priority | Name | Description | Action |
|----------|------|-------------|--------|
| **P0** | Blocking | Prevents task completion entirely | Fix immediately |
| **P1** | Major | Causes significant difficulty or confusion | Fix before release |
| **P2** | Minor | Annoyance, workaround exists | Fix in next pass |
| **P3** | Polish | Nice-to-fix, no real user impact | Fix if time permits |

**Tiebreaker:** "Would a user contact support about this?" If yes, at least P1.

---

## Output Structure

1. **AI Slop Verdict**: Pass/fail with specific indicators listed and anti-pattern score (0-4).
2. **Audit Health Score** (if mode = audit or full): Table of 5 dimensions with scores, key findings, total/20, and rating band.
3. **Cognitive Load** (if mode = audit or full): Pass/fail per item, named violations, overall level.
4. **Design Health Score** (if mode = critique or full): Table of 10 heuristics with scores, key issues, total/40, and rating band.
5. **Persona Red Flags** (if mode = critique or full): 2-3 personas with specific failure points.
6. **Priority Issues**: Top 3-5 most impactful findings, each tagged P0-P3 with what/why/fix.
7. **What's Working**: 2-3 things done well. Good audits aren't only about problems.
8. **Recommended Actions**: Prioritized list of specific fixes.

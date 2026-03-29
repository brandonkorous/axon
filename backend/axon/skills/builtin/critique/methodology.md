# UX Critique Methodology

You are performing a structured 10-dimension UX critique that evaluates design effectiveness through quantitative scoring, heuristic analysis, and persona-based testing.

This is a 4-phase process: conduct the critique, present findings, ask clarifying questions, and recommend fixes.

---

## Phase 1: Conduct the Critique

### 10-Dimension UX Evaluation (0-4 each, total 0-40)

Rate each dimension on a 0-4 scale. Be specific about what you observe.

#### Dimension 1: Visual Hierarchy (0-4)
- 0: No clear hierarchy. Everything competes for attention equally.
- 1: Weak hierarchy. Primary action is unclear, multiple elements fight for dominance.
- 2: Partial hierarchy. Main content is identifiable but secondary elements lack clear ordering.
- 3: Good hierarchy. Clear primary, secondary, tertiary levels. Eye flow is intentional.
- 4: Excellent hierarchy. Immediate focal point, natural scan pattern, deliberate emphasis and de-emphasis.

**Check:** Squint test (does structure emerge when blurred?), F-pattern or Z-pattern alignment, size/weight/color contrast between levels, whitespace as hierarchy tool.

#### Dimension 2: Typography (0-4)
- 0: No typographic system. Random sizes, weights, and fonts throughout.
- 1: Minimal system. Font chosen but sizes/weights are inconsistent. Hierarchy muddy.
- 2: Partial system. Reasonable type scale but gaps in application. Some AI slop fonts without customization.
- 3: Good system. Clear type scale with distinct size jumps. Weight contrast is effective. Intentional font choice.
- 4: Excellent system. Cohesive type scale, strong weight contrast (regular+bold, not regular+medium), line heights tuned per context, tracking adjusted for headings vs. body.

**Check:** Number of font sizes in use (ideal: 4-6), weight contrast ratios, line height consistency, font pairing quality, heading vs. body distinction.

#### Dimension 3: Spacing (0-4)
- 0: No spacing system. Random margins and padding throughout.
- 1: Inconsistent spacing. Some areas cramped, others too loose. No rhythm.
- 2: Basic spacing. Mostly consistent but breaks in several places. Lacks intentional rhythm.
- 3: Good spacing. Consistent scale applied. Clear grouping through proximity. Breathing room where needed.
- 4: Excellent spacing. Mathematical scale (4px/8px base), tight grouping for related items, generous separation for sections, rhythm creates visual pulse.

**Check:** Consistency of gaps between similar elements, section vs. element spacing ratio, padding within containers, alignment to a spacing scale.

#### Dimension 4: Color and Contrast (0-4)
- 0: Poor contrast throughout. Color used randomly or not at all. Accessibility failures.
- 1: Basic color use but inconsistent. Some contrast issues. No semantic color system.
- 2: Reasonable palette but application is uneven. Minor contrast issues. Some semantic colors.
- 3: Good palette with consistent application. Meets WCAG AA. Semantic colors for status/actions.
- 4: Excellent color system. WCAG AA+ throughout, intentional palette with clear semantic meaning, color used sparingly for maximum impact, no pure black/white.

**Check:** Contrast ratios (4.5:1 body text, 3:1 large text/UI), semantic consistency (red=error everywhere), number of colors in active use (ideal: 3-5 + neutrals), AI slop palette detection (cyan-on-dark, purple gradients).

#### Dimension 5: Interaction States (0-4)
- 0: No visible interaction states. Elements look the same in all states.
- 1: Hover states only. No focus, active, disabled, loading, or error states.
- 2: Hover and some focus states. Disabled states exist but are inconsistent.
- 3: Good coverage. Hover, focus, active, disabled states present. Loading states for async actions.
- 4: Complete state coverage. All 8 states addressed per interactive element (default, hover, focus, active, disabled, loading, error, success). Transitions between states are smooth.

**Check:** Hover effects on all clickable elements, visible focus rings for keyboard nav, disabled state visual distinction, loading indicators, error state styling, success confirmation.

#### Dimension 6: Responsive Design (0-4)
- 0: Fixed-width layout. Broken on mobile. Horizontal scrolling.
- 1: Some responsiveness but major issues at common breakpoints. Tiny touch targets.
- 2: Works at common sizes but layouts feel forced. Touch targets inconsistent.
- 3: Good across devices. Proper breakpoints, touch targets >= 44px, readable text at all sizes.
- 4: Fluid layouts. Container queries where appropriate. Pointer/hover media queries. Content reflows naturally. Mobile-specific optimizations.

**Check:** Fixed widths, touch target sizes, text readability at 320px, breakpoint behavior, horizontal overflow, image scaling.

#### Dimension 7: Content Quality (0-4)
- 0: Generic, unclear, or missing content. Jargon-heavy. No microcopy strategy.
- 1: Basic content present but vague. Generic button labels ("Submit", "OK"). Weak empty states.
- 2: Reasonable content but opportunities missed. Some specific labels, some generic. Error messages lack specifics.
- 3: Good content. Specific verb+object buttons, helpful error messages, informative empty states.
- 4: Excellent microcopy. Every label is precise, errors explain what/why/how-to-fix, empty states are onboarding moments, tone is consistent and human.

**Check:** Button labels (generic vs. specific), error message quality, empty state content, heading clarity, tooltip helpfulness, confirmation dialog text.

#### Dimension 8: AI Slop Detection (0-4)
- 0: Pervasive AI aesthetic across all categories. Looks entirely generated.
- 1: Heavy AI tells. 5+ indicators across typography, color, layout, and effects.
- 2: Some tells. 3-4 indicators. Noticeable "generated" feel.
- 3: Mostly clean. 1-2 minor indicators. Subtle issues only.
- 4: No AI tells. Distinctive, intentional design choices throughout.

**Check:** Default fonts without customization (Inter, Roboto), cyan-on-dark palette, purple gradients, cards-in-cards, glassmorphism everywhere, identical card grids, hero metric layouts, center-everything approach, bounce/elastic animations.

#### Dimension 9: Motion (0-4)
- 0: No motion at all, or jarring/broken animations.
- 1: Minimal motion. Some hover transitions but no system. Inconsistent timing.
- 2: Basic transitions present. Timing is reasonable but easing is default or inconsistent.
- 3: Good motion system. Appropriate easing (ease-out for entrances, ease-in for exits), consistent timing, respects prefers-reduced-motion.
- 4: Purposeful motion design. Animations serve feedback and orientation. Stagger effects for lists. GPU-accelerated (transform/opacity only). 60fps maintained. Micro-interactions enhance understanding.

**Check:** Easing functions used, animation duration ranges (100-500ms typical), layout property animations (bad) vs. transform/opacity (good), prefers-reduced-motion support, animation purpose (feedback vs. decoration).

#### Dimension 10: Performance Feel (0-4)
- 0: Sluggish. Visible loading delays, layout shifts, janky scrolling.
- 1: Noticeable lag. Some operations feel slow. No loading indicators.
- 2: Acceptable. Most interactions feel responsive. Occasional waits without feedback.
- 3: Good. Interactions feel snappy. Loading states present. Optimistic UI for common actions.
- 4: Excellent. Sub-100ms feedback on all interactions. Progressive loading. Skeleton screens. Perceived performance is instant.

**Check:** Time to first meaningful paint, interaction response latency, scroll performance, image loading strategy, skeleton/placeholder usage, optimistic updates.

### Dimension Scoring Summary

| Range  | Rating                                |
|--------|---------------------------------------|
| 36-40  | Excellent — production-grade polish   |
| 28-35  | Good — address weak dimensions        |
| 20-27  | Acceptable — significant work needed  |
| 12-19  | Poor — major UX overhaul required     |
| 0-11   | Critical — fundamental redesign       |

---

## Phase 2: Nielsen's 10 Heuristics (0-4 each, total 0-40)

Rate each heuristic with specific observations and examples.

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

| Range  | Rating                                    |
|--------|-------------------------------------------|
| 36-40  | Excellent — ship it                       |
| 28-35  | Good — address weak heuristics            |
| 20-27  | Acceptable — significant improvements     |
| 12-19  | Poor — major UX overhaul                  |
| 0-11   | Critical — redesign needed                |

---

## Phase 3: Persona Testing

Test the interface through 5 archetype lenses. Select 2-3 most relevant and identify specific red flags.

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

## Phase 4: Clarifying Questions and Fix Recommendations

After completing the evaluation, ask 2-3 targeted clarifying questions about design intent, constraints, or priorities that would refine recommendations.

Then produce prioritized fix recommendations. Every finding includes:
- **What**: The specific issue observed
- **Why**: The impact on user experience
- **How to fix**: Concrete, actionable steps

### Issue Severity Classification

| Priority | Name     | Description                            | Action            |
|----------|----------|----------------------------------------|--------------------|
| **P0**   | Blocking | Prevents task completion entirely      | Fix immediately    |
| **P1**   | Major    | Causes significant difficulty           | Fix before release |
| **P2**   | Minor    | Annoyance, workaround exists           | Fix in next pass   |
| **P3**   | Polish   | Nice-to-fix, no real user impact       | Fix if time permits|

---

## Output Structure

1. **Dimension Scores**: Table of all 10 dimensions with individual scores (0-4), key observations, total/40, and rating band.
2. **Nielsen's Heuristics**: Table of 10 heuristics with scores (0-4), specific findings, total/40, and rating band.
3. **Persona Findings**: 2-3 selected personas with specific red flags and failure points identified.
4. **Priority Issues**: Top 5 most impactful findings, each tagged P0-P3 with what/why/fix.
5. **What's Working**: 2-3 things done well. Good critiques are not only about problems.
6. **Clarifying Questions**: 2-3 questions about design intent or constraints.
7. **Recommended Fixes**: Prioritized list of specific, actionable improvements ordered by impact.

# Normalize Methodology

You are performing a design system consistency audit to identify deviations from established tokens, patterns, and standards, then producing a normalization plan.

---

## Step 1: Establish the Reference

Before auditing, identify the design system baseline:
- Locate token definitions (CSS custom properties, theme files, design token configs)
- Identify established component patterns already in use
- Note documented standards (spacing scale, type scale, color palette, motion tokens)
- If no explicit design system exists, infer the dominant patterns from the codebase

Document the reference system as a checklist of expected tokens and patterns.

---

## Step 2: 8-Dimension Deviation Scan

Examine each dimension systematically. For every deviation, record: the exact location, the current value, the expected value, and the severity.

### Dimension 1: Typography Tokens
**Expected:** All text uses named type scale tokens (font-size, font-weight, line-height, letter-spacing).
**Deviations to find:**
- Hard-coded font sizes (e.g., `font-size: 15px` instead of a token)
- Weights that do not match the defined scale
- Line heights that vary for the same text role
- Font families not from the approved set
- Letter spacing applied inconsistently

### Dimension 2: Color/Theme Tokens
**Expected:** All colors reference semantic or primitive tokens. No hard-coded hex/rgb/hsl values.
**Deviations to find:**
- Hard-coded color values (`#3b82f6`, `rgb(59, 130, 246)`)
- Colors that exist in the palette but are referenced by raw value instead of token
- Semantic misuse (using `--color-primary` for non-primary purposes)
- Dark mode failures (colors that do not adapt when theme changes)
- Opacity values that create non-standard shades

### Dimension 3: Spacing Scale
**Expected:** All spacing (margin, padding, gap) uses the defined scale (e.g., 4px base: 4, 8, 12, 16, 24, 32, 48, 64).
**Deviations to find:**
- Arbitrary spacing values (e.g., `margin: 13px`, `padding: 22px`)
- Inconsistent gap values in similar contexts
- Spacing that almost matches the scale but is off by 1-2px
- Negative margins used as workarounds for layout issues

### Dimension 4: Component Patterns
**Expected:** Reusable components are used instead of one-off implementations.
**Deviations to find:**
- Custom implementations of components that exist in the design system (buttons, inputs, cards, modals)
- Components with the same visual appearance but different markup
- Variants that should exist as component props but are hand-built
- Wrapper divs that duplicate existing layout components

### Dimension 5: Motion Tokens
**Expected:** Transitions use defined duration and easing tokens.
**Deviations to find:**
- Hard-coded transition durations (e.g., `transition: 0.2s` instead of a token)
- Inconsistent easing functions across similar interactions
- Missing transitions where the system defines them
- Animation durations that do not match the established timing scale

### Dimension 6: Responsive Behavior
**Expected:** Breakpoints and responsive patterns follow established conventions.
**Deviations to find:**
- Custom breakpoint values instead of defined breakpoints
- Responsive patterns that differ from established conventions (e.g., stacking at different points)
- Mobile-specific overrides that conflict with the responsive system
- Fixed widths that bypass the fluid/responsive approach

### Dimension 7: Accessibility Standards
**Expected:** Consistent accessibility patterns throughout.
**Deviations to find:**
- Focus styles that differ from the established focus ring pattern
- ARIA patterns that are inconsistent (e.g., different approaches for the same widget type)
- Contrast ratios that fall below the defined minimum
- Keyboard interaction patterns that differ between similar components

### Dimension 8: Information Hierarchy
**Expected:** Consistent heading levels, label styles, and content structure.
**Deviations to find:**
- Heading levels that skip or repeat inconsistently
- Labels styled differently for the same type of content
- Inconsistent emphasis patterns (bold vs. color vs. size for the same purpose)
- Content structure that deviates from established page/section templates

---

## Step 3: Root Cause Analysis

For each cluster of deviations, identify the root cause:

| Root Cause             | Description                                              | Fix Approach                        |
|------------------------|----------------------------------------------------------|-------------------------------------|
| Hard-coded values      | Developer used raw values instead of tokens              | Replace with token references       |
| Missing token          | The design system lacks a needed token                   | Add the token to the system         |
| Missing component      | No reusable component exists for this pattern            | Extract and add to component library|
| Pattern divergence     | Developer chose a different pattern than established     | Align to the established pattern    |
| Outdated reference     | Code references old tokens or deprecated patterns        | Update to current system            |
| Intentional override   | Deviation is deliberate for a specific context           | Document as exception or add variant|

---

## Step 4: Normalization Plan

Produce an ordered plan:
1. **Quick wins**: Simple token replacements (hard-coded values to tokens)
2. **Component alignment**: Replace custom implementations with design system components
3. **Token additions**: New tokens needed to support legitimate patterns
4. **Pattern consolidation**: Merge divergent implementations into a single approach
5. **Documentation updates**: Record exceptions and new patterns

---

## Output Structure

1. **Reference Summary**: The design system baseline used for comparison (tokens, patterns, standards).
2. **Deviation Report**: All deviations organized by dimension, each with location, current value, expected value, and severity.
3. **Root Cause Analysis**: Grouped root causes with counts and examples.
4. **Normalization Plan**: Ordered list of changes, grouped by effort level (quick wins through structural changes).
5. **New Tokens Needed**: Any tokens or components the design system should add to prevent future deviations.
6. **Exception Log**: Any intentional deviations that should be documented rather than normalized.

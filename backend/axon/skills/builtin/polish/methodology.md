# Polish Methodology

You are performing a final pre-deployment quality pass that catches the small issues separating good interfaces from great ones.

**Prerequisite:** The feature must be functionally complete before polishing. Polish is not about adding features — it is about perfecting what exists.

---

## Step 1: Pre-Check

Before starting, confirm:
- Feature is functionally complete and working
- No known blocking bugs remain
- Design intent is understood (reference design system or mockups if available)

If the feature is not functionally complete, stop and note what must be finished first.

---

## Step 2: 8-Dimension Polish Audit

Examine each dimension systematically. For every issue found, note the specific location, what is wrong, and the exact fix.

### Dimension 1: Pixel-Perfect Alignment

Verify every element aligns to the grid and to neighboring elements.

**Check for:**
- Elements that are 1-2px off from their intended alignment
- Inconsistent padding within similar containers
- Text baselines that do not align across columns
- Icons that are not optically centered (mathematical center vs. visual center)
- Border radius inconsistencies between similar elements
- Uneven margins between repeated items (e.g., card lists, nav items)
- Elements that break alignment at specific viewport widths

**Common fixes:** Snap to grid values, use consistent spacing tokens, adjust optical alignment for icons and rounded elements.

### Dimension 2: Typography Hierarchy

Verify the type system is applied consistently and creates clear hierarchy.

**Check for:**
- Font sizes that deviate from the type scale
- Weight inconsistencies (same role using different weights in different places)
- Line height mismatches for the same text style
- Letter spacing not adjusted for headings vs. body
- Orphaned words on headings (single word on last line)
- Text truncation without ellipsis or tooltip
- Missing font-feature-settings for tabular numbers in data displays

**Common fixes:** Map all text to named type scale tokens, apply consistent line heights, enable tabular-nums for numeric data.

### Dimension 3: Color and Contrast Compliance

Verify color usage is intentional, accessible, and consistent.

**Check for:**
- Contrast ratios below WCAG AA (4.5:1 body text, 3:1 large text and UI components)
- Inconsistent use of semantic colors (e.g., success green used for non-success purposes)
- Hard-coded color values instead of theme tokens
- Hover/focus colors that do not maintain sufficient contrast
- Dark mode colors that do not adapt properly (inverted but washed out)
- Opacity-based text colors that fall below readable contrast

**Common fixes:** Replace hard-coded values with tokens, adjust opacity minimums, verify contrast in both themes.

### Dimension 4: Interaction States (8 States Per Element)

Every interactive element must address all 8 states:

| State    | Requirement                                          |
|----------|------------------------------------------------------|
| Default  | Clear affordance that element is interactive         |
| Hover    | Visual feedback within 50ms, cursor change           |
| Focus    | Visible focus ring (not just outline: none)          |
| Active   | Pressed/depressed visual feedback                    |
| Disabled | Visually distinct, cursor: not-allowed, not focusable|
| Loading  | Spinner or skeleton, element non-interactive         |
| Error    | Red/semantic border or message, clear what went wrong|
| Success  | Confirmation feedback, auto-dismiss or next step     |

**Check for:** Missing states, inconsistent state styling across similar elements, focus rings that disappear, disabled elements that are still clickable.

### Dimension 5: Micro-Interactions

Verify transitions and animations are smooth and purposeful.

**Check for:**
- Transitions that animate layout properties (width, height, padding) instead of transform/opacity
- Missing transitions on state changes (jarring snaps)
- Inconsistent duration across similar transitions
- Animations that do not respect prefers-reduced-motion
- Frame drops during animations (not maintaining 60fps)
- Hover transitions without corresponding un-hover transitions
- Loading spinners that appear/disappear without fade

**Timing reference:**
- Micro-feedback (hover, press): 100-150ms
- State changes (toggle, tab switch): 200-300ms
- Layout shifts (expand, collapse): 300-500ms
- Entrances (modal, drawer): 300-500ms

### Dimension 6: Content Quality

Verify all text is clear, specific, and consistent.

**Check for:**
- Generic button labels ("Submit", "OK", "Yes", "Cancel" without context)
- Error messages that say "Something went wrong" without specifics
- Empty states that just say "No items" without guidance
- Placeholder text still present ("Lorem ipsum", "TODO", "TBD")
- Inconsistent capitalization (Title Case vs. Sentence case)
- Truncated text without tooltips or expand affordance
- Missing ARIA labels on icon-only buttons

**Common fixes:** Replace generic labels with verb+object ("Save changes"), add what/why/fix to errors, make empty states actionable.

### Dimension 7: Edge Cases

Verify the interface handles boundary conditions gracefully.

**Check for:**
- Very long text content (names, titles, descriptions)
- Empty or null data states
- Single item vs. many items in lists
- Rapid repeated interactions (double-click, fast toggle)
- Slow network simulation (loading states)
- Viewport extremes (320px mobile, ultrawide desktop)
- Text zoom at 200% (WCAG requirement)
- Right-to-left text content if applicable

### Dimension 8: Code Cleanliness

Verify the implementation supports long-term maintainability.

**Check for:**
- Inline styles that should be tokens or classes
- Magic numbers (hard-coded px values instead of spacing scale)
- Duplicated style blocks that should be shared
- z-index values that are arbitrary (use a defined scale)
- Console warnings or errors in browser dev tools
- Unused CSS rules or dead code
- Missing key props on list-rendered elements

---

## Step 3: Polish Scoring

Rate overall polish readiness on a 0-10 scale:

| Score | Rating                                                  |
|-------|---------------------------------------------------------|
| 9-10  | Ship-ready — exceptional attention to detail            |
| 7-8   | Nearly ready — minor issues, quick fixes only           |
| 5-6   | Needs work — noticeable rough edges in multiple areas   |
| 3-4   | Significant gaps — several dimensions need attention    |
| 1-2   | Not ready — major polish pass required across the board |
| 0     | Functionally incomplete — polish is premature           |

---

## Step 4: Fix Prioritization

Order all fixes by impact:

1. **Accessibility fixes** — Contrast, focus states, ARIA labels (always first)
2. **Interaction state gaps** — Missing hover, focus, disabled states
3. **Alignment and spacing** — Visual consistency issues
4. **Content quality** — Generic labels, unclear errors
5. **Micro-interaction polish** — Smooth transitions, timing
6. **Edge case handling** — Overflow, empty states, extremes
7. **Code cleanliness** — Tokens, magic numbers, dead code

---

## Output Structure

1. **Pre-Check Result**: Confirmation that the feature is functionally complete, or list of blockers.
2. **Issues by Dimension**: Each of the 8 dimensions with specific issues found, exact locations, and fixes.
3. **Polish Score**: Overall score (0-10) with justification.
4. **Fix Priority List**: All issues ordered by impact, each with what/why/fix.
5. **What's Already Polished**: 2-3 things that are already well-executed.
6. **Ship Readiness**: Clear yes/no verdict with conditions if applicable.

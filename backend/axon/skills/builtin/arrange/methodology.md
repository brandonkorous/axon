# Arrange Methodology

You are performing a layout and spacing assessment to optimize how space is used to create hierarchy, grouping, rhythm, and appropriate density throughout the interface.

---

## Step 1: Spacing Analysis

Evaluate whether spacing is consistent, intentional, and creates clear visual relationships.

### Consistency Check

- Are the same spacing values used for the same relationships throughout?
- Is there a discernible spacing scale (4px base unit, consistent multipliers)?
- Do padding and margin values follow a pattern or appear arbitrary?
- Are spacing values hard-coded or tokenized?

### Intentional Variety

Consistent does not mean identical. Good spacing creates rhythm through intentional variation:

- **Tight grouping** (8-12px): Within related items (label to input, icon to text, list items)
- **Medium spacing** (16-24px): Between peer groups (card to card, form field to form field)
- **Generous separation** (48-96px): Between sections (hero to features, features to testimonials)

### Common Spacing Failures

- **Same spacing everywhere**: 16px between everything — no rhythm, no grouping, monotonous
- **Too tight globally**: Everything cramped, no breathing room, cognitive overload
- **Too spacious globally**: Elements feel disconnected, no clear relationships
- **Inconsistent relationships**: 12px between some label-input pairs, 20px between others

### Scoring

| Rating | Criteria |
|--------|----------|
| 4 | Consistent scale with intentional variety; tight grouping within, generous between; tokenized |
| 3 | Mostly consistent; clear grouping; one or two inconsistencies |
| 2 | Some consistency but notable spacing irregularities; weak grouping |
| 1 | Arbitrary spacing; no discernible system; relationships unclear |
| 0 | No spacing system; random values throughout; no visual grouping |

---

## Step 2: Visual Hierarchy Assessment

Evaluate whether the layout makes importance immediately clear.

### The Squint Test

Blur your vision or view the interface at 25% zoom. You should still be able to identify:

1. What is the most important element on the page?
2. What are the major sections?
3. Where should the eye go first, second, third?

If everything looks the same when blurred, the hierarchy has failed.

### Hierarchy Through Space

Space creates hierarchy without adding visual noise:

- **More space around = more important**: Primary CTAs get generous surrounding whitespace
- **Tight grouping = related**: Items close together are perceived as a unit
- **Separation = distinct**: Clear space between sections signals topic change
- **Indentation = subordination**: Nested items signal hierarchy through horizontal offset

### Scoring

| Rating | Criteria |
|--------|----------|
| 4 | Instant identification of primary, secondary, tertiary content via spacing and size |
| 3 | Clear hierarchy; one area where competing elements have ambiguous importance |
| 2 | Hierarchy exists but requires effort to parse; some sections compete |
| 1 | Weak hierarchy; most elements feel equally important |
| 0 | No hierarchy; visual flat field with no clear entry point |

---

## Step 3: Grid Structure Assessment

Evaluate whether the layout follows a clear, logical grid system.

### Grid Properties

- **Column count**: Appropriate to content type (12-column for complex layouts, 4-6 for content-focused)
- **Gutter consistency**: Same gutter width throughout, or intentionally varied
- **Alignment**: Elements snap to grid lines — no arbitrary offsets
- **Content containers**: Consistent max-width with centered containment

### Modern Grid Techniques

```css
/* Self-adjusting grid with auto-fit */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-md);
}

/* Subgrid for aligned nested content */
.card {
  display: grid;
  grid-template-rows: subgrid;
  grid-row: span 3;
}
```

### Grid Failures

- Fixed column counts that don't adapt to content width
- Mixed gutter sizes without purpose
- Elements that don't align to any grid
- No maximum content width (text spanning 1920px screens)

### Scoring

| Rating | Criteria |
|--------|----------|
| 4 | Clear grid system; self-adjusting columns; consistent gutters; proper containment |
| 3 | Good grid structure; minor alignment issues or one area off-grid |
| 2 | Basic grid exists but inconsistent application; some alignment drift |
| 1 | Weak grid; elements placed without clear structural logic |
| 0 | No grid system; elements arbitrarily positioned |

---

## Step 4: Rhythm and Variety Assessment

Evaluate whether the layout creates visual interest through intentional spacing alternation.

### What Good Rhythm Looks Like

- Alternation between dense, information-rich sections and spacious, breathing sections
- Consistent internal spacing within a section, varied spacing between sections
- Visual "beats" — the eye moves naturally from one focal point to the next
- Variation in section height creates a dynamic vertical flow

### What Bad Rhythm Looks Like

- Every section is the same height with the same padding — monotonous, boring
- No variation in density — either all cramped or all spacious
- Sections run together without clear boundaries
- Content feels like a vertical list, not a composed layout

### Techniques for Better Rhythm

- **Section spacing variation**: Alternate between 48px and 96px section gaps based on content relationship
- **Content width variation**: Some sections use full width, others use narrow centered columns
- **Background alternation**: Alternate background colors or subtle tonal shifts to create section identity
- **Element variation**: Mix text-heavy sections with image-heavy or interactive sections

### Scoring

| Rating | Criteria |
|--------|----------|
| 4 | Dynamic rhythm with intentional alternation; engaging vertical flow; clear section identity |
| 3 | Good rhythm overall; one area feels monotonous |
| 2 | Some variation exists but feels accidental; mostly uniform |
| 1 | Monotonous layout; same spacing, density, and height throughout |
| 0 | No rhythm; content dumped vertically with no composition |

---

## Step 5: Density Matching Assessment

Evaluate whether the layout density is appropriate for the content type.

### Density by Content Type

| Content Type | Appropriate Density | Characteristics |
|-------------|-------------------|----------------|
| Data tables / dashboards | Compact | Tight row spacing, small text, minimal padding, high information per pixel |
| Forms / workflows | Comfortable | Generous field spacing, clear labels, adequate touch targets |
| Marketing / landing pages | Spacious | Large whitespace, dramatic headlines, focused sections |
| Documentation / articles | Comfortable | Generous line height, constrained width, ample paragraph spacing |
| Admin / settings | Compact to comfortable | Functional density, clear grouping, efficient use of space |

### Density Calibration

| Preference | Internal Padding | Section Spacing | Row/Item Spacing |
|-----------|-----------------|----------------|-----------------|
| Compact | 8-12px | 24-48px | 4-8px |
| Comfortable | 16-24px | 48-72px | 8-16px |
| Spacious | 24-48px | 72-120px | 16-24px |

### Scoring

| Rating | Criteria |
|--------|----------|
| 4 | Density perfectly matched to content type; supports the primary task |
| 3 | Mostly appropriate density; one area could be tighter or more spacious |
| 2 | Density is acceptable but doesn't feel optimized for the content |
| 1 | Density mismatch — too sparse for data or too dense for marketing |
| 0 | Severe mismatch — data drowning in whitespace or marketing content cramped |

---

## Step 6: Spacing Token System

Define a consistent spacing scale for implementation.

### Recommended 4pt Base Unit Scale

| Token | Value | Usage |
|-------|-------|-------|
| --space-xs | 4px | Inline icon gap, tight stacking |
| --space-sm | 8px | Related item spacing, compact padding |
| --space-md | 16px | Default padding, form field gaps |
| --space-lg | 24px | Card padding, group separation |
| --space-xl | 32px | Section internal padding |
| --space-2xl | 48px | Major group separation |
| --space-3xl | 64px | Section separation |
| --space-4xl | 96px | Hero/major section separation |

### Optical Adjustments

Mathematical centering does not always look centered. Common adjustments:

- **Buttons**: Add 1-2px extra top padding to visually center text (ascenders vs descenders)
- **Icons next to text**: Shift icon down 1px to align with text optical center
- **Cards in grids**: Bottom card may need 1-2px extra margin to feel evenly spaced against the page fold
- **Headings**: Reduce top margin slightly — the ascender height creates visual space that mathematical spacing ignores

**Philosophy:** "Space is the most underused design tool — it creates hierarchy, groups, and breathing room for free."

---

## Output Structure

1. **Spacing Audit**: Findings across all 5 assessment areas with 0-4 scores and specific observations per area.
2. **Layout Recommendations**: Prioritized list of layout and spacing improvements, each with what/why/how-to-implement.
3. **Token Definitions**: Complete spacing token system with values, names, and usage guidelines.
4. **Grid Specification**: Recommended grid system with column count, gutters, breakpoints, and containment strategy.
5. **Rhythm Improvements**: Specific changes to create better visual flow and section variety.
6. **Total Score**: Sum of 5 area scores (0-20) with rating band.

| Range | Rating |
|-------|--------|
| 18-20 | Excellent — polished spatial design |
| 14-17 | Good — minor spacing inconsistencies |
| 10-13 | Acceptable — noticeable layout issues |
| 6-9 | Poor — significant spacing problems |
| 0-5 | Critical — no spatial system |

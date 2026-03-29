# Typeset Methodology

You are performing a typography assessment and improvement to ensure the interface's type system is distinctive, readable, and creates clear visual hierarchy.

---

## Step 1: Font Choice Assessment

Evaluate whether the current font choices carry personality or default to invisible.

### The Invisible Font Problem

These fonts are not bad — they are invisible. They signal "I didn't think about typography":

| Invisible Default | Why It's a Problem |
|------------------|-------------------|
| Inter | Used by every AI-generated interface. Technically excellent, zero personality. |
| Roboto | Android system font. Signals "default" outside Material Design. |
| Arial/Helvetica | The fallback font. Using it as a choice says "no choice was made." |
| Open Sans | The Google Docs font. Safe, forgettable, ubiquitous. |
| Montserrat | Overused geometric sans-serif. Lost all distinctiveness through overuse. |
| Lato | The WordPress default era font. Dated and generic. |

### Distinctive Alternatives

| Instead Of | Try | Character |
|-----------|-----|-----------|
| Inter | Instrument Sans, Plus Jakarta Sans, Outfit | Modern, clean, but distinctive |
| Roboto | Onest, Figtree, Urbanist | Friendly, contemporary, fresh |
| Arial/Helvetica | Geist, Switzer, General Sans | Professional, sharp, intentional |
| Open Sans | Source Sans 3, Nunito Sans | Readable, warm, updated |
| Montserrat | Sora, Lexend, Satoshi | Geometric with personality |

### Personality-Based Selection

| Brand Personality | Display Font Direction | Body Font Direction |
|------------------|----------------------|-------------------|
| Warm | Rounded sans or humanist serif | Humanist sans-serif |
| Technical | Geometric sans or monospace display | Clean grotesque |
| Playful | Rounded, variable weight | Soft, open sans-serif |
| Elegant | High-contrast serif | Refined sans-serif |
| Bold | Heavy sans or slab serif | Strong, clear sans-serif |

### Scoring

| Rating | Criteria |
|--------|----------|
| 4 | Distinctive, intentional font choice that reinforces brand personality |
| 3 | Good font choice, not default, but could be more distinctive |
| 2 | Safe choice — readable but personality-neutral |
| 1 | Default/invisible font with no customization |
| 0 | System default with no font specification at all |

---

## Step 2: Hierarchy Assessment

Evaluate whether the type system creates instant, clear visual distinction between content levels.

### 5-Tier Hierarchy Model

| Tier | Purpose | Distinction Method |
|------|---------|-------------------|
| Display | Hero headlines, page titles | Largest size + distinctive font + tight tracking |
| H1 | Section headings | Bold weight + significant size jump from body |
| H2 | Subsection headings | Medium weight or color differentiation from H1 |
| Body | Primary content | Base size + comfortable weight + generous line height |
| Small | Captions, metadata, labels | Reduced size + lighter color or reduced weight |

### Hierarchy Tests

- **Squint test**: Blur your vision. Can you still identify 3+ distinct levels of importance?
- **Distance test**: From 2 meters away, can you see the headline, body, and small text as separate tiers?
- **Speed test**: In 2 seconds of scanning, can a user identify the most important content?

### Common Hierarchy Failures

- **Muddy sizes**: Sizes too close together (14, 15, 16, 18px). Good hierarchy uses distinct jumps.
- **Weak weight contrast**: Regular vs Medium is barely visible. Use Regular + Bold, or Light + Bold.
- **Color-only hierarchy**: Relying solely on gray shades without size or weight changes.
- **Too many levels**: More than 6-7 distinct type styles creates confusion, not clarity.

### Scoring

| Rating | Criteria |
|--------|----------|
| 4 | 5+ clear levels with instant visual distinction using size + weight + color |
| 3 | Clear hierarchy but one level blends with an adjacent level |
| 2 | Some hierarchy but sizes and weights are too similar to scan quickly |
| 1 | Minimal hierarchy — headings barely larger than body text |
| 0 | No discernible hierarchy — everything looks the same |

---

## Step 3: Sizing and Scale Assessment

Evaluate the mathematical relationships between type sizes.

### Type Scale Ratios

| Ratio | Name | Character |
|-------|------|-----------|
| 1.125 | Major second | Tight, subtle — good for dense data interfaces |
| 1.200 | Minor third | Compact but clear — general purpose |
| 1.250 | Major third | Balanced — most common for web |
| 1.333 | Perfect fourth | Pronounced — good for marketing and editorial |
| 1.500 | Perfect fifth | Dramatic — strong hierarchy, display-oriented |
| 1.618 | Golden ratio | Very dramatic — editorial and landing pages |

### Size Minimums

- Body text: 16px minimum (15px acceptable only with high x-height fonts)
- Small text: 12px absolute minimum, 13-14px recommended
- Touch targets with text: 14px minimum for legibility at arm's length

### Fluid Typography

```css
/* Fluid type scale using clamp() */
--font-display: clamp(2.5rem, 5vw, 4.5rem);
--font-h1: clamp(1.75rem, 3vw, 2.5rem);
--font-h2: clamp(1.25rem, 2vw, 1.75rem);
--font-body: clamp(0.9375rem, 1vw, 1.0625rem);
--font-small: clamp(0.8125rem, 0.8vw, 0.875rem);
```

### Scoring

| Rating | Criteria |
|--------|----------|
| 4 | Consistent scale ratio applied throughout; fluid sizing; appropriate minimums |
| 3 | Mostly consistent scale; one or two sizes break the pattern |
| 2 | Sizes are reasonable but no consistent ratio; some too-small text |
| 1 | Arbitrary sizes with no relationship; body text below 16px |
| 0 | No size system; random sizes throughout |

---

## Step 4: Readability Assessment

Evaluate whether text is comfortable to read in sustained use.

### Line Length

- **Optimal**: 45-75 characters per line (65ch is the sweet spot)
- **Implementation**: `max-width: 65ch` on text containers
- **Common failure**: Paragraphs stretching to 120+ characters on wide screens

### Line Height

| Content Type | Recommended Line Height |
|-------------|----------------------|
| Body text | 1.5-1.6 |
| Headings | 1.1-1.2 |
| Small text / captions | 1.4-1.5 |
| UI labels (single line) | 1.0-1.2 |
| Dense data tables | 1.3-1.4 |

### Paragraph Spacing

- Space between paragraphs should equal approximately one line height
- Avoid double-spacing (two blank lines between paragraphs)
- Heading space above should be greater than space below (groups heading with its content)

### Contrast

- Body text: minimum 4.5:1 contrast ratio against background
- Large text (18px+ or 14px+ bold): minimum 3:1
- Never use pure gray text — always tint slightly warm or cool to match the palette

### Scoring

| Rating | Criteria |
|--------|----------|
| 4 | Optimal line length, appropriate line heights, sufficient contrast, comfortable paragraph spacing |
| 3 | Good readability overall; one area (line length or line height) slightly off |
| 2 | Readable but uncomfortable — long lines, tight spacing, or low contrast |
| 1 | Significant readability issues — multiple problems across metrics |
| 0 | Text is difficult to read — very long lines, cramped, or insufficient contrast |

---

## Step 5: Consistency Assessment

Evaluate whether typography is applied consistently across the interface.

### Checks

- **Font family count**: Maximum 2-3 font families (display, body, optional monospace)
- **Weight consistency**: Same content type always uses the same weight
- **Size consistency**: Same semantic level uses the same size everywhere
- **Color consistency**: Text colors map to semantic meaning consistently
- **Spacing consistency**: Margins above and below headings follow a pattern

### Common Inconsistencies

- Different heading sizes on different pages for the same hierarchy level
- Mixed font weights for body text (400 on one page, 450 on another)
- Inconsistent text color — some labels at 60% opacity, others at 50%
- Different letter-spacing on headings across views

### Scoring

| Rating | Criteria |
|--------|----------|
| 4 | 2-3 families max; consistent weights, sizes, and colors throughout; clear token system |
| 3 | Mostly consistent with 1-2 minor deviations |
| 2 | Noticeable inconsistencies — different heading sizes on different pages |
| 1 | Significant inconsistencies — many one-off styles throughout |
| 0 | No consistency — styles appear randomly assigned |

---

## Step 6: Advanced Typography

Evaluate use of modern typographic techniques.

### OpenType Features

- **Ligatures** (`"liga" 1`): Standard ligatures for polished body text
- **Tabular numbers** (`"tnum" 1`): Fixed-width numbers for data alignment in tables
- **Fractions** (`"frac" 1`): Proper fraction rendering
- **Oldstyle figures** (`"onum" 1`): For elegant body text (not data tables)

### Variable Fonts

- Use variable fonts for fine-tuned weight control (wght axis)
- Reduce HTTP requests — one variable font replaces multiple weight files
- Enable optical sizing if available (opsz axis)

### Font Loading Strategy

```css
/* Ensure text is visible during load */
@font-face {
  font-family: 'CustomFont';
  font-display: swap;
  /* Preload the primary weight */
}
```

- Use `font-display: swap` for body fonts (text visible immediately)
- Use `font-display: optional` for display fonts (avoid layout shift)
- Preload critical font files with `<link rel="preload">`
- Subset fonts to reduce file size (Latin subset for English-only sites)

---

## Output Structure

1. **Current Assessment**: Score and findings for each of the 5 areas (font choice, hierarchy, sizing, readability, consistency) with 0-4 rating per area.
2. **Font Recommendations**: Specific font suggestions with pairing rationale and personality match.
3. **Hierarchy Spec**: Complete 5-tier type hierarchy with exact sizes, weights, line heights, and letter-spacing for each level.
4. **Implementation Guide**: CSS custom properties, fluid typography setup, font loading strategy, and OpenType features to enable.
5. **Quick Wins**: 2-3 highest-impact typographic improvements that can be made immediately.
6. **Total Score**: Sum of 5 area scores (0-20) with rating band.

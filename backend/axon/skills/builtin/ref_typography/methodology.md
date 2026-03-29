# Typography Reference Methodology

You are performing a typography reference consultation, providing guidance on type systems, vertical rhythm, font pairing, fluid sizing, and web font optimization.

## Section 1: Vertical Rhythm

Use line-height as the foundational unit for all vertical spacing. This creates a consistent visual cadence that makes layouts feel cohesive even when content varies.

**Base unit**: body line-height (typically 1.5 × body font size = 24px if body is 16px).

| Element | Line-height | Reasoning |
|---------|-------------|-----------|
| Body text | 1.5 | Optimal readability for paragraph text |
| Headings | 1.2 | Tighter — headings are shorter, less need for line separation |
| UI labels | 1.25-1.3 | Compact but readable for interface elements |
| Code blocks | 1.4-1.6 | Slightly more generous for scanability |

**Spacing rule**: all vertical spacing between elements should be multiples of the base unit. If the base unit is 24px, margins should be 24px, 48px, 72px — never 30px or 40px. This maintains rhythm even when elements have different sizes.

## Section 2: 5-tier Hierarchy

Every interface needs exactly 5 type tiers. Each must be instantly distinguishable without relying on context.

| Tier | Role | Size Ratio | Weight | Typical Use |
|------|------|-----------|--------|-------------|
| Display | Impact | 2.5-3x body | 700-900 | Hero headlines, splash screens |
| H1 | Page title | 2-2.5x body | 600-700 | Single per page, identifies the view |
| H2 | Section | 1.5-1.75x body | 600 | Section dividers, card titles |
| Body | Default | 1x (16px min) | 400 | Paragraphs, form inputs, descriptions |
| Small | Supporting | 0.75-0.875x body | 400-500 | Captions, timestamps, helper text |

**Minimum ratio between tiers**: 1.2x. If two tiers are too close in size, combine size + weight + color to create separation. Size alone is not enough — a 18px heading next to 16px body text looks like a mistake, not a hierarchy.

**Differentiation tools** (combine at least 2 per tier):
- Size (primary differentiator)
- Weight (bold vs regular)
- Color (muted vs full opacity)
- Letter-spacing (tight for headings, normal for body)
- Case (uppercase for labels, sentence case for content)

## Section 3: Readability

### Line Length
The single most impactful readability rule: `max-width: 65ch` on text containers. This limits lines to ~65 characters — the optimal range for comfortable reading (45-75ch).

### Minimum Sizes
| Context | Minimum Size | Reason |
|---------|-------------|--------|
| Body text (desktop) | 16px | Below this, most fonts strain readability |
| Body text (mobile) | 16px | Also prevents iOS zoom on form focus |
| Small/caption text | 12px | Below 12px is inaccessible for many users |
| Button labels | 14px | Needs to be legible at a glance |

### Paragraph Spacing
- Between paragraphs: 1em-1.5em (relative to the paragraph's own font size)
- After headings: 0.5em-0.75em (tight — heading belongs to the content below it)
- Before headings: 1.5em-2em (generous — creates clear section breaks)

### Color and Contrast for Text
- Body text on light backgrounds: use near-black (not pure black — `oklch(0.15 0.01 hue)`)
- Secondary text: reduce opacity to 60-70% rather than using gray (preserves color temperature)
- Links: must be distinguishable without relying on color alone — add underline or weight

## Section 4: Font Pairing

### Contrast Principle
Pair fonts that are clearly different. Similar fonts create visual confusion — the reader senses inconsistency without being able to identify it.

| Pairing Strategy | Example | Risk |
|-----------------|---------|------|
| Serif + Sans-serif | Fraunces + DM Sans | Low — reliable contrast |
| Geometric + Humanist | Geist + Source Serif | Low — clear differentiation |
| Same superfamily | Source Sans + Source Serif | Very low — designed to work together |
| Two sans-serifs | Inter + Roboto | High — too similar, avoid |
| Two serifs | Playfair + Georgia | High — needs careful weight differentiation |

### Maximum Families
Limit to 2-3 font families per project:
- 1 for headings (display/decorative weight)
- 1 for body text (high readability at small sizes)
- 1 for code (monospace, optional)

Adding a 4th family almost always creates visual noise rather than hierarchy.

## Section 5: Fluid Typography

### The clamp() Pattern
Use `clamp()` for type that smoothly scales between breakpoints without media queries:

```css
font-size: clamp(min, preferred, max);
font-size: clamp(1rem, 0.5rem + 2vw, 2rem);
```

| Parameter | Meaning | Rule |
|-----------|---------|------|
| min | Smallest allowed size | Never below readability minimums |
| preferred | Scales with viewport | Use `rem + vw` formula |
| max | Largest allowed size | Caps growth on wide screens |

**Formula**: `preferred = min + (max - min) * (100vw - minViewport) / (maxViewport - minViewport)`

Simplified: `clamp(1rem, calc(0.5rem + 1.5vw), 2.5rem)` covers most heading needs.

### Scale Application
Apply fluid sizing to headings and display text. Body text should stay fixed at 16px (1rem) — fluid body text creates inconsistent density that harms readability.

## Section 6: Web Font Optimization

### Loading Strategy
1. **font-display: swap** — show fallback font immediately, swap to web font when loaded. Prevents invisible text (FOIT).
2. **Preload critical fonts** — `<link rel="preload" href="font.woff2" as="font" type="font/woff2" crossorigin>` for fonts used above the fold.
3. **Subset fonts** — if only using Latin characters, subset to Latin range. Reduces file size by 50-80% for fonts with large character sets.
4. **Variable fonts** — one file replaces multiple weight/width files. A single variable font file is typically smaller than 2-3 static font files.

### Format Priority
Use woff2 exclusively for modern browsers. It provides 30% better compression than woff. Only add woff as a fallback if supporting IE11.

### Fallback Matching
Configure `size-adjust`, `ascent-override`, `descent-override` on the fallback font to match the web font's metrics. This minimizes layout shift when the web font loads.

## Section 7: Distinctive Font Choices

Avoid default-looking fonts that make interfaces feel generic:

| Instead Of | Consider | Why |
|-----------|----------|-----|
| Inter | Instrument Sans, Plus Jakarta Sans | Same clarity, more personality |
| Roboto | Onest, Figtree | Warmer, more distinctive |
| Arial/Helvetica | Geist, Switzer | Modern, designed for screens |
| Open Sans | General Sans, Satoshi | More contemporary feel |
| System monospace | JetBrains Mono, Fira Code, Cascadia Code | Ligatures, better readability |

These are not obscure fonts — they are high-quality, widely available alternatives that signal intentional design without sacrificing readability.

## Output Structure

When providing typography guidance:

1. **Context assessment**: what the user is building and their current type setup
2. **Relevant principles**: which sections above apply to their situation
3. **Specific values**: concrete CSS values, font recommendations, or scale numbers
4. **Hierarchy check**: whether their current type system has clear tier separation
5. **Performance notes**: font loading impact and optimization suggestions

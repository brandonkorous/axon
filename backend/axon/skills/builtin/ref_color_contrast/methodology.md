# Color and Contrast Reference Methodology

You are performing a color and contrast reference consultation, providing guidance on color systems, palette construction, contrast compliance, and dark mode strategy.

## Section 1: OKLCH Color Space

OKLCH is a perceptually uniform color space — equal numeric steps produce equal perceived brightness changes, unlike HSL where perceived brightness varies wildly across hues.

**Syntax**: `oklch(lightness chroma hue)`

| Parameter | Range | Meaning |
|-----------|-------|---------|
| Lightness | 0-1 (or 0%-100%) | Perceived brightness. 0 = black, 1 = white |
| Chroma | 0-0.4 | Color intensity. 0 = gray, 0.4 = maximum saturation |
| Hue | 0-360 | Color wheel angle. 0/360 = red, 120 = green, 240 = blue |

**Why OKLCH over HSL**: In HSL, `hsl(60, 100%, 50%)` (yellow) appears far brighter than `hsl(240, 100%, 50%)` (blue) despite identical lightness values. OKLCH fixes this — same lightness value = same perceived brightness regardless of hue. This makes systematic palette generation predictable.

**Browser support**: All modern browsers support `oklch()` in CSS. Use it directly — no fallbacks needed for current-year targets.

## Section 2: Palette Building

### Starting from Brand Primary

1. **Extract OKLCH values** from the brand primary color
2. **Derive semantic colors** by shifting hue while preserving lightness and chroma:
   - Success: shift hue toward green (~140-160)
   - Warning: shift hue toward amber (~80-95)
   - Error: shift hue toward red (~25-35)
   - Info: shift hue toward blue (~240-260)
3. **Build neutral scale** with a subtle color cast from the primary hue:
   - Take the primary hue
   - Set chroma to 0.01-0.02 (barely perceptible)
   - Generate 9-11 lightness steps from 0.1 to 0.98
4. **Generate tint/shade scales** for each color:
   - Use `color-mix()` for reliable tints: `color-mix(in oklch, var(--primary) 20%, white)`
   - Or directly set lightness values: 0.95 (lightest tint), 0.85, 0.70, 0.55 (base), 0.40, 0.30, 0.20 (darkest shade)

### Harmony Methods

| Method | Hue Relationship | Best For |
|--------|-----------------|----------|
| Complementary | +180° | High contrast, bold palettes |
| Analogous | ±30° | Harmonious, subtle palettes |
| Triadic | ±120° | Vibrant, balanced palettes |
| Split-complementary | +150° and +210° | Contrast with less tension |

## Section 3: 60-30-10 Distribution

The 60-30-10 rule ensures visual balance:

| Proportion | Role | Typical Usage |
|------------|------|---------------|
| 60% | Dominant | Background, page surface, large containers |
| 30% | Secondary | Cards, sidebars, secondary containers, supporting elements |
| 10% | Accent | CTAs, highlights, active states, key interactive elements |

Application rules:
- The dominant color is almost always a neutral (white, off-white, gray)
- The secondary color can be a muted version of the brand or a complementary neutral
- The accent color is the brand primary — use it sparingly so it draws attention when it appears
- Test by squinting: the 60-30-10 balance should be visible even when details blur

## Section 4: WCAG Contrast Standards

### Required Ratios

| Content Type | Level AA | Level AAA |
|-------------|----------|-----------|
| Normal body text (<18px, <14px bold) | 4.5:1 | 7:1 |
| Large text (≥18px or ≥14px bold) | 3:1 | 4.5:1 |
| UI components & graphical objects | 3:1 | 3:1 |
| Decorative / disabled elements | No requirement | No requirement |

### Calculating Contrast in OKLCH

Contrast is calculated from relative luminance, not OKLCH lightness directly. However, OKLCH lightness is a reliable proxy for quick checks:
- Lightness difference of 0.40+ between text and background is usually safe for body text
- Lightness difference of 0.30+ is usually safe for large text
- Always verify with a proper contrast ratio calculator for final compliance

### Common Failures

| Failure | Fix |
|---------|-----|
| Light gray text on white | Darken to at least oklch(0.45 0 0) |
| Colored text on colored background | Check both colors against each other, not just against white |
| Placeholder text too faint | Placeholders still need 4.5:1 if conveying information |
| Disabled state invisible | Use opacity + strikethrough or other non-color signal |
| Focus ring invisible | Focus ring needs 3:1 against adjacent colors |

## Section 5: Dark Mode Strategy

### Principles

Do not invert your light theme. Dark mode is a separate design that respects the same brand:

1. **Reduce saturation** — colors that look good on white are too vibrant on dark backgrounds. Reduce chroma by 20-30% for dark mode.
2. **Lower lightness range** — avoid pure black backgrounds. Use `oklch(0.15 0.01 hue)` as the darkest surface. Pure black creates too much contrast with text and causes visual fatigue.
3. **Increase contrast for readability** — text on dark backgrounds needs slightly more contrast than text on light backgrounds due to halation (light text appears to bleed into dark surroundings).
4. **Respect system preference** — always honor `prefers-color-scheme` media query. Let users override manually.

### Surface Elevation in Dark Mode

Use lightness to convey elevation instead of shadows (shadows are invisible on dark backgrounds):

| Surface Level | OKLCH Lightness | Usage |
|---------------|----------------|-------|
| Base | 0.15 | Page background |
| Elevated 1 | 0.20 | Cards, panels |
| Elevated 2 | 0.25 | Dropdowns, modals |
| Elevated 3 | 0.30 | Tooltips, popovers |

### Dark Mode Text Hierarchy

| Role | OKLCH Lightness | Opacity Alternative |
|------|----------------|-------------------|
| Primary text | 0.93 | white/87% |
| Secondary text | 0.75 | white/60% |
| Disabled text | 0.55 | white/38% |

## Output Structure

When providing color and contrast guidance:

1. **Context assessment**: what the user is trying to achieve
2. **Relevant principles**: which sections above apply to their situation
3. **Specific values**: concrete OKLCH/CSS values they can use
4. **Compliance check**: whether their approach meets WCAG AA
5. **Dark mode considerations**: how the guidance changes for dark mode if applicable

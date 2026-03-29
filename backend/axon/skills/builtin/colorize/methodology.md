# Colorize Methodology

You are performing a strategic color introduction to transform a monochromatic or visually dull interface into one with intentional, meaningful color that improves hierarchy, semantics, and engagement.

**Core principle:** Color is information. Every color choice must communicate something — status, hierarchy, category, or action. Decorative color is visual noise.

---

## Step 1: Assessment — Current Color State

### Inventory Existing Colors
- List every color currently in use (including neutrals, borders, backgrounds)
- Identify the dominant color temperature (warm, cool, neutral)
- Note any existing brand colors that must be preserved
- Count the total number of distinct colors (including shades/tints)

### Diagnose the Problem
Common color issues to identify:

| Problem                  | Symptoms                                                   |
|--------------------------|-----------------------------------------------------------|
| Monochromatic            | All grays, no hue variation. Functional but lifeless.     |
| No semantic color        | Success/error/warning all look the same.                  |
| Flat hierarchy           | No color-based visual distinction between element types.  |
| Muddy palette            | Colors lack contrast or vibrancy. Everything looks dull.  |
| Random color             | Colors applied without system or meaning.                 |
| Too many colors          | Rainbow effect, no clear system.                          |

---

## Step 2: Strategy — Build the Palette

### The 60-30-10 Rule

| Proportion | Role        | Description                                         |
|------------|-------------|-----------------------------------------------------|
| 60%        | Dominant    | Neutral backgrounds and surfaces. Sets the base tone.|
| 30%        | Secondary   | Supporting color for sections, cards, secondary UI. |
| 10%        | Accent      | Primary actions, highlights, active states.          |

**Maximum colors beyond neutrals:** 2-4 chromatic colors plus their tints/shades. More than 4 distinct hues creates visual chaos.

### OKLCH Color Space

Use OKLCH for perceptual uniformity — colors at the same lightness value look equally light to human eyes (unlike HSL where yellow and blue at the same L look completely different).

**OKLCH structure:** `oklch(lightness chroma hue)`
- **Lightness (L):** 0-1 (0 = black, 1 = white). Use 0.5-0.7 for UI colors.
- **Chroma (C):** 0-0.4 (0 = gray, higher = more vivid). Use 0.05-0.15 for subtle, 0.15-0.25 for vivid.
- **Hue (H):** 0-360 degrees. The color wheel position.

**Generating harmonious palettes in OKLCH:**
- Keep lightness constant, vary hue for equal-prominence colors
- Keep hue constant, vary lightness for tints and shades of one color
- Adjacent hues (within 30 degrees) create harmonious pairs
- Complementary hues (180 degrees apart) create strong contrast

### Palette Roles

Every palette needs these functional slots:

| Role           | Purpose                                | Example Application           |
|----------------|----------------------------------------|-------------------------------|
| Primary        | Main brand/action color                | Primary buttons, active nav   |
| Secondary      | Supporting brand color                 | Secondary buttons, sections   |
| Accent         | Highlight, attention                   | Badges, indicators, links     |
| Success        | Positive outcomes                      | Confirmations, valid states   |
| Warning        | Caution needed                         | Approaching limits, alerts    |
| Error          | Problems, destructive actions          | Validation errors, delete     |
| Info           | Neutral information                    | Tips, informational banners   |
| Surface        | Background variations                  | Cards, panels, elevated areas |

---

## Step 3: Strategic Application

### Where to Apply Color (Priority Order)

1. **Semantic meaning** — Status colors (success/error/warning) are the highest-value use of color. They communicate meaning instantly.
2. **Primary actions** — The main call-to-action button, active navigation state, selected items. Color draws the eye to what matters.
3. **Data visualization** — Charts, graphs, status indicators. Color distinguishes categories.
4. **Surface differentiation** — Subtle background tints to distinguish sections, cards from background, elevated from flat.
5. **Accents and highlights** — Badges, new indicators, progress bars. Small pops of color for emphasis.
6. **Typography** — Sparingly. Link color, heading accents. Most text should be neutral.

### Application Rules
- Use full-chroma color on small areas (buttons, badges, icons)
- Use low-chroma tints for large areas (backgrounds, panels, sections)
- Never put vivid color on large surfaces — it overwhelms
- Ensure text on colored backgrounds maintains WCAG AA contrast
- Dark mode: reduce chroma slightly, increase lightness slightly

### Neutral Strategy
Neutrals are not colorless — add subtle warmth or coolness:
- Warm neutrals: `oklch(L 0.01 80)` — adds coziness, organic feel
- Cool neutrals: `oklch(L 0.01 250)` — adds crispness, technical feel
- True neutrals: `oklch(L 0 0)` — use sparingly, can feel dead

Never use pure `#000000` or `#ffffff`. Always carry a subtle color cast.

---

## Step 4: Refinement and Verification

### Contrast Checks

Every color combination must pass WCAG AA:

| Combination                | Minimum Ratio |
|---------------------------|---------------|
| Body text on background   | 4.5:1         |
| Large text on background  | 3:1           |
| UI components on background| 3:1          |
| Focus indicators          | 3:1           |

### Anti-Patterns to Avoid

- **Rainbow overuse**: More than 4 chromatic colors with no system
- **Random application**: Color used decoratively without meaning
- **Purple-blue gradients**: The default AI-generated palette. Avoid unless it is genuinely the brand.
- **Neon on dark**: Cyan, electric blue, hot pink on dark backgrounds. Screams "generated."
- **Gradient text**: Almost never adds value. Hard to read, decorative only.
- **Color-only meaning**: Never use color as the sole indicator. Always pair with text, icon, or pattern.
- **Same color, different meaning**: Using the same green for "success" and "go" and "online" without distinction.

### Dark Mode Adaptation
When adapting the palette for dark mode:
- Backgrounds: use very dark versions of the dominant color (not pure black)
- Text: off-white with slight color cast matching the palette
- Accent colors: reduce chroma by 10-20%, increase lightness by 5-10%
- Semantic colors: maintain recognizability but soften intensity
- Surfaces: layer using opacity or lightness steps, not distinct colors

---

## Output Structure

1. **Current State Assessment**: Inventory of existing colors, diagnosed problems.
2. **Palette Definition**: Complete palette with each color's hex value, OKLCH value, semantic role, and usage notes.
3. **60-30-10 Distribution Map**: Which colors fill each proportion and where they appear in the interface.
4. **Application Plan**: Ordered list of where to introduce color, starting with highest-impact areas.
5. **Contrast Verification**: Table of all color combinations with their contrast ratios and pass/fail status.
6. **Dark Mode Adaptation**: How the palette adjusts for dark theme.
7. **Anti-Pattern Check**: Confirmation that the palette avoids common color anti-patterns.

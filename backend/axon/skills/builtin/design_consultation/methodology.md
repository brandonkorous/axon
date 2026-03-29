# Design Consultation Methodology

You are performing a complete design system creation, guiding the user from product context through visual research to a fully specified design system documented as DESIGN.md.

## Phase 1: Product Context & Research

Gather foundational information before making any visual decisions:

### Product Purpose
- What does this product do in one sentence?
- What is the core value proposition?
- What category does it belong to (SaaS, developer tool, consumer app, internal tool, marketplace)?

### Target Users
- Who is the primary user? Be specific (job title, company size, technical level).
- Who is the secondary user?
- What is the user's emotional state when they arrive (stressed, curious, skeptical, excited)?
- What devices and contexts do they use (desk, mobile, dark room, bright office)?

### Competitive Landscape
- Name 3-5 direct competitors
- What do their designs have in common?
- Where do they all fall short visually?
- What visual territory is unclaimed?

### Existing Brand Elements
- Logo (if exists): colors, style, mood
- Brand guidelines (if exist): voice, values, personality
- Previous design work: what to keep, what to abandon
- Non-negotiable constraints: platform requirements, accessibility mandates, brand colors

## Phase 2: Visual Research

Before proposing a system, analyze the design landscape:

### Competitor Analysis
For each major competitor:
- **Visual tone**: cold/warm, minimal/rich, playful/serious
- **Color approach**: monochrome, complementary, analogous, brand-heavy
- **Typography**: sans/serif/mono, tight/loose, heavy/light
- **Layout**: grid-rigid, fluid, asymmetric, card-based
- **Standout element**: what makes their design recognizable

### Inspiration References
Identify 3-5 non-competitor references that capture elements of the desired aesthetic:
- What specifically to borrow from each
- What to avoid from each

## Phase 3: System Proposal

For every design decision, present two options:

### Aesthetic Direction
| Option | Description | Gain | Lose |
|--------|-------------|------|------|
| Safe | {description} | {what you gain} | {what you lose} |
| Risk | {description} | {what you gain} | {what you lose} |

Directions to evaluate:
- **Modern** — clean lines, generous whitespace, geometric shapes
- **Classic** — serif typography, traditional layouts, timeless feel
- **Playful** — rounded shapes, bright colors, casual tone
- **Minimal** — extreme restraint, monochrome-adjacent, content-first
- **Bold** — strong colors, large typography, dramatic contrast

### Decoration Level
| Level | Description | Best For |
|-------|-------------|----------|
| Minimal | No decorative elements. Content and typography only. | Developer tools, data-heavy apps |
| Moderate | Subtle borders, light shadows, occasional illustrations | SaaS, professional tools |
| Rich | Illustrations, patterns, textures, gradients | Consumer apps, marketing sites |

### Layout Approach
- **Grid-based**: predictable columns, consistent spacing, easy to implement
- **Fluid**: responsive to content, organic feel, harder to maintain consistency
- **Asymmetric**: distinctive, editorial feel, requires strong design skill to maintain

### Color Palette

Define complete palette with specific hex values:

| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| Primary | {name} | {hex} | Main actions, navigation highlights, key UI elements |
| Secondary | {name} | {hex} | Supporting actions, secondary navigation |
| Accent | {name} | {hex} | Highlights, badges, notifications |
| Neutral 50 | {name} | {hex} | Backgrounds |
| Neutral 100 | {name} | {hex} | Card backgrounds, subtle borders |
| Neutral 200 | {name} | {hex} | Borders, dividers |
| Neutral 300 | {name} | {hex} | Disabled states |
| Neutral 400 | {name} | {hex} | Placeholder text |
| Neutral 500 | {name} | {hex} | Secondary text |
| Neutral 600 | {name} | {hex} | Body text |
| Neutral 700 | {name} | {hex} | Headings |
| Neutral 800 | {name} | {hex} | Primary text |
| Neutral 900 | {name} | {hex} | High-contrast text |
| Success | {name} | {hex} | Positive states, confirmations |
| Warning | {name} | {hex} | Caution states, alerts |
| Error | {name} | {hex} | Error states, destructive actions |
| Info | {name} | {hex} | Informational states, tips |

For each color, verify:
- WCAG AA contrast ratio against intended backgrounds
- Works in both light and dark mode
- Distinguishable for color-blind users (test deuteranopia, protanopia)

**Safe option vs. risk option**: Present a conventional palette alongside a distinctive one. Explain what each gains and loses.

### Typography

Recommend fonts for three roles:

| Role | Font | Weight Range | Usage |
|------|------|-------------|-------|
| Display | {font} | {weights} | Headings, hero text, marketing |
| Body | {font} | {weights} | Paragraphs, UI labels, form fields |
| Mono/Data | {font} | {weights} | Code, numbers, tabular data |

Define the type scale:

| Token | Size | Line Height | Weight | Usage |
|-------|------|-------------|--------|-------|
| xs | {px/rem} | {ratio} | {weight} | Captions, fine print |
| sm | {px/rem} | {ratio} | {weight} | Secondary text, labels |
| base | {px/rem} | {ratio} | {weight} | Body text, default |
| lg | {px/rem} | {ratio} | {weight} | Lead text, subheadings |
| xl | {px/rem} | {ratio} | {weight} | Section headings |
| 2xl | {px/rem} | {ratio} | {weight} | Page headings |
| 3xl | {px/rem} | {ratio} | {weight} | Hero headings |

### Spacing Scale

Define base unit and scale:

| Token | Value | Usage |
|-------|-------|-------|
| space-1 | {px} | Tight gaps (icon-to-label) |
| space-2 | {px} | Element padding, small gaps |
| space-3 | {px} | Component internal padding |
| space-4 | {px} | Between related elements |
| space-6 | {px} | Between sections |
| space-8 | {px} | Major section separation |
| space-12 | {px} | Page-level spacing |
| space-16 | {px} | Maximum spacing |

### Motion Approach

| Level | Description | Timing | Usage |
|-------|-------------|--------|-------|
| Subtle | Barely perceptible transitions | 100-150ms | State changes, hover effects |
| Moderate | Noticeable but not distracting | 200-300ms | Page transitions, reveals |
| Expressive | Deliberate and characterful | 300-500ms | Onboarding, celebrations, key moments |

Specify easing functions:
- **Enter**: ease-out (fast start, slow finish)
- **Exit**: ease-in (slow start, fast finish)
- **Movement**: ease-in-out (smooth acceleration and deceleration)

### Border Radius Scale

| Token | Value | Usage |
|-------|-------|-------|
| none | 0 | Sharp corners (tables, code blocks) |
| sm | {px} | Subtle rounding (inputs, buttons) |
| md | {px} | Standard rounding (cards, modals) |
| lg | {px} | Prominent rounding (large cards, containers) |
| full | 9999px | Pills, avatars, circular elements |

### Shadow Scale

| Token | Value | Usage |
|-------|-------|-------|
| sm | {shadow} | Subtle lift (cards on hover) |
| md | {shadow} | Medium elevation (dropdowns, popovers) |
| lg | {shadow} | High elevation (modals, dialogs) |

### Icon Style
- **Outline**: clean, modern, pairs with minimal aesthetics
- **Solid**: bold, confident, pairs with rich aesthetics
- **Duo-tone**: distinctive, pairs with playful or bold aesthetics
- Recommended icon set and sizing conventions

## Phase 4: Presentation of Choices

For EACH major decision area, present:

1. **Safe option** — conventional, proven, lower risk
   - What you gain: familiarity, faster development, broad appeal
   - What you lose: distinctiveness, personality, memorability

2. **Risk option** — distinctive, opinionated, higher reward
   - What you gain: uniqueness, strong brand identity, emotional impact
   - What you lose: potential alienation of some users, harder to maintain

Let the user choose. Do not default to safe options — present both with equal enthusiasm.

## Phase 5: Visual Previews

When possible, generate HTML/CSS mockups demonstrating:
- A sample card component with the proposed palette and typography
- A sample form with input states
- A sample navigation bar
- Light mode and dark mode side by side

## Phase 6: DESIGN.md Assembly

Compile all decisions into a single DESIGN.md file that serves as the source of truth:

## Output Structure

```markdown
## Design System: {Product Name}

### Brand Context
- **Product**: {one-line description}
- **Users**: {primary and secondary}
- **Personality**: {3-5 trait words}
- **Aesthetic direction**: {chosen direction with rationale}

### Color Palette
{Complete table with hex values, roles, contrast ratios}

#### Light Mode
{Token-to-value mapping for light theme}

#### Dark Mode
{Token-to-value mapping for dark theme}

### Typography
{Font families, type scale, usage guidelines}

### Spacing
{Scale with tokens and values}

### Motion
{Approach, timing, easing functions}

### Border Radius
{Scale with tokens and values}

### Shadows
{Scale with tokens and values}

### Icons
{Style, set, sizing conventions}

### Component Patterns
{Key component specifications — buttons, forms, cards, navigation}

### Decisions Log
| Decision | Choice | Alternative Considered | Rationale |
|----------|--------|----------------------|-----------|
| {area} | {what was chosen} | {what was rejected} | {why} |
```

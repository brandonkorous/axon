# Design Exploration Methodology

You are performing a multi-variant design exploration, generating genuinely distinct visual directions for comparison and iterative refinement.

## Step 1: Context Gathering

Before generating any variants, establish the design context:

### Who does this design serve?
- Primary user profile (role, technical level, aesthetic expectations)
- Secondary users (if any)
- User's emotional state when they encounter this design

### What job does this design accomplish?
- Core task or workflow
- Success criteria (what does "working well" look like)
- Failure modes (what does "broken" look like)

### What exists already?
- Current design system (colors, typography, components)
- Brand guidelines or personality
- Platform constraints (web, mobile, desktop, embedded)
- Accessibility requirements

### What user flows are involved?
- Entry point (how user arrives)
- Core interaction sequence
- Exit point (how user leaves or completes)

## Step 2: Variant Generation

Generate the requested number of variants (default 3, range 2-4). Each variant must be genuinely distinct — not minor tweaks of the same idea.

### Variant Differentiation Requirements

Each variant must differ in at least 3 of these dimensions:
- **Color approach**: warm vs. cool, monochrome vs. colorful, muted vs. saturated
- **Typography style**: serif vs. sans, tight vs. loose, heavy vs. light
- **Layout structure**: grid vs. fluid, dense vs. spacious, symmetric vs. asymmetric
- **Visual weight**: minimal vs. rich, flat vs. elevated, restrained vs. decorative
- **Emotional tone**: professional vs. casual, serious vs. playful, calm vs. energetic

### Variant Specification

For each variant, provide:

**Identity**
- **Name**: A descriptive concept name (e.g., "Bold Minimalist", "Warm Editorial", "Tech Forward", "Organic Calm")
- **One-line concept**: What makes this direction distinctive

**Visual Characteristics**
- **Color direction**: Primary and accent colors, overall palette mood
- **Typography**: Font families (display and body), weight distribution, tracking
- **Layout approach**: Grid structure, spacing philosophy, density level
- **Decorative elements**: Borders, shadows, gradients, illustrations, icons
- **Motion personality**: Static, subtle transitions, or expressive animations

**Strengths and Trade-offs**
- **Best for**: What context, audience, or mood this serves well
- **Risk**: Where this direction could go wrong
- **Scalability**: How well this direction holds up across more pages and features

**Key Design Decisions**
| Element | Choice | Rationale |
|---------|--------|-----------|
| Primary color | {hex + name} | {why this color for this concept} |
| Display font | {font name} | {why this font} |
| Body font | {font name} | {why this font} |
| Border radius | {value} | {sharp/rounded/pill and why} |
| Spacing density | {tight/normal/loose} | {why this density} |
| Shadow approach | {none/subtle/prominent} | {why} |

## Step 3: Comparison Matrix

Present all variants in a side-by-side comparison:

| Dimension | Variant A: {name} | Variant B: {name} | Variant C: {name} |
|-----------|-------------------|-------------------|-------------------|
| Color palette | {description} | {description} | {description} |
| Typography | {description} | {description} | {description} |
| Layout density | {description} | {description} | {description} |
| Visual weight | {description} | {description} | {description} |
| Emotional tone | {description} | {description} | {description} |
| Accessibility | {WCAG status} | {WCAG status} | {WCAG status} |
| Implementation effort | {low/medium/high} | {low/medium/high} | {low/medium/high} |
| Scalability | {how well it extends} | {how well it extends} | {how well it extends} |

## Step 4: Recommendation

Based on the context gathered in Step 1, recommend a direction:

1. **Primary recommendation** — which variant best fits the product, users, and constraints
2. **Rationale** — specific reasons tied to user needs, not personal preference
3. **Hybrid suggestion** — if applicable, how to combine the best elements of multiple variants

## Step 5: Feedback Capture & Refinement

After presenting variants, support iterative refinement:

### Feedback Types
- **Rating**: 1-5 per variant
- **Element preference**: "I like the colors from A but the layout from C"
- **Directional feedback**: "Make it warmer", "Less playful", "More dense"
- **Rejection**: "Not this direction at all" with reason

### Refinement Operations
- **Remix**: Combine specific elements from multiple variants into a new direction
- **Evolve**: Take one variant and push it further in a stated direction
- **Constrain**: Apply new requirements (accessibility, brand, platform) to a variant
- **Diverge**: Generate a new variant that is intentionally different from all existing ones

### Taste Memory

Track demonstrated preferences across the session:

| Preference | Evidence | Confidence |
|------------|----------|------------|
| {e.g., "Prefers warm colors"} | {which variant was rated higher} | {low/medium/high} |

Apply accumulated taste preferences to bias future variant generation toward demonstrated aesthetic.

## Step 6: Final Direction Selection

When a direction is chosen, produce:

1. **Design brief** — summary of the chosen direction with all key specifications
2. **Token draft** — preliminary design tokens (colors, fonts, spacing) ready for implementation
3. **Next steps** — what to design or build next with this direction

## Output Structure

```markdown
## Design Exploration: {Subject}

### Context
- **Users**: {who}
- **Job**: {what}
- **Constraints**: {existing system, platform, accessibility}

### Variant A: {Name}
- **Concept**: {one-line description}
- **Color**: {palette description with hex values}
- **Typography**: {font choices}
- **Layout**: {approach}
- **Mood**: {emotional tone}
- **Best for**: {strengths}
- **Risk**: {trade-offs}

### Variant B: {Name}
{same structure}

### Variant C: {Name}
{same structure}

### Comparison Matrix
| Dimension | A | B | C |
|-----------|---|---|---|
| {dimension} | {value} | {value} | {value} |

### Recommendation
**Recommended**: {Variant name}
**Rationale**: {why this fits best}
**Hybrid option**: {if applicable}

### Taste Preferences Detected
| Preference | Evidence |
|------------|----------|
| {pattern} | {from ratings/feedback} |
```

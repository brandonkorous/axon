# Frontend Design Methodology

You are performing production-grade interface design and creation, producing distinctive, high-quality interfaces that avoid generic AI aesthetics and demonstrate clear creative intent.

---

## Phase 1: Establish Aesthetic Direction

Every interface needs a point of view. A design without direction is a template.

### Direction Framework

Answer these before writing any code:

1. **Purpose**: What is this interface for? What task does it serve?
2. **Tone**: How should the user feel? (Confident, calm, energized, focused, delighted)
3. **Differentiation**: What makes this visually distinct from competitors or generic templates?
4. **Reference**: What existing designs (not necessarily digital) inspire the aesthetic? (Architecture, print design, industrial design, art movements)

### If an `aesthetic` parameter is provided, use it as the starting direction. Otherwise, derive from the subject matter.

---

## Phase 2: AI Fingerprint Avoidance

These patterns immediately identify a design as AI-generated. Avoid them explicitly.

### Typography Fingerprints

- **Overused fonts**: Inter, Roboto, Arial, Open Sans, system defaults without customization. These are invisible — they signal "didn't think about typography."
- **Monospace-as-technical**: Using monospace typography as lazy shorthand for developer/technical vibes.
- **Large icons with rounded corners above every heading**: Templated. Rarely adds value.
- **Muddy hierarchy**: Font sizes too close together (14px, 15px, 16px, 18px). Use distinct jumps.

### Color Fingerprints

- **Cyan-on-dark**: The default AI color palette.
- **Purple-to-blue gradients**: Screams "generated."
- **Neon accents on dark backgrounds**: Looks cool without requiring design decisions.
- **Gradient text on headings**: Decorative, not meaningful.
- **Pure black (#000) or pure white (#fff)**: Real products always tint slightly.
- **Pure gray (no chroma)**: Shadows and surfaces carry subtle color casts. Use `oklch` with chroma 0.01+.

### Layout Fingerprints

- **Everything in cards**: Not everything needs a container.
- **Cards nested inside cards**: Visual noise. Flatten hierarchy.
- **Identical card grids**: Same-sized cards with icon + heading + text. The "feature grid" template.
- **Center everything**: Left-aligned text with asymmetric layouts feels more designed.
- **Same spacing everywhere**: Without rhythm, layouts feel monotonous.
- **3-column grids with icons**: The most common AI layout pattern.

### Effect Fingerprints

- **Glassmorphism everywhere**: Blur effects used decoratively, not functionally.
- **Dark mode with glowing accents**: Default aesthetic that requires no decisions.
- **Decorative blur and gradient borders**: Effects that serve no hierarchy purpose.

---

## Phase 3: Typography System

Typography carries 80% of the design's personality.

### Font Selection

Avoid invisible defaults. Choose distinctive fonts that carry personality:

| Instead Of | Try |
|-----------|-----|
| Inter | Instrument Sans, Plus Jakarta Sans, Outfit |
| Roboto | Onest, Figtree, Urbanist |
| Arial/Helvetica | Geist, Switzer, General Sans |
| Open Sans | Source Sans 3, Nunito Sans |
| Montserrat | Sora, Lexend, Satoshi |

### Hierarchy System

Create a 5+ level hierarchy with clear visual distinction at each level:

| Level | Purpose | Technique |
|-------|---------|-----------|
| Display | Hero headlines, page titles | Largest size, distinctive font, tight tracking |
| H1 | Section headings | Bold weight, significant size jump from body |
| H2 | Subsection headings | Medium weight or color differentiation |
| Body | Primary content | 16px minimum, comfortable reading weight |
| Small | Captions, metadata, labels | Reduced size, lighter color or weight |

### Technical Implementation

```css
/* Fluid typography with clamp() */
--font-display: clamp(2.5rem, 5vw, 4.5rem);
--font-h1: clamp(1.75rem, 3vw, 2.5rem);
--font-h2: clamp(1.25rem, 2vw, 1.75rem);
--font-body: clamp(0.9375rem, 1vw, 1.0625rem);
--font-small: clamp(0.8125rem, 0.8vw, 0.875rem);
```

- Use `font-display: swap` for web fonts
- Enable OpenType features: `font-feature-settings: "liga" 1, "tnum" 1`
- Tight tracking on headings: `letter-spacing: -0.02em`
- Comfortable line height: 1.5 body, 1.2 headings

---

## Phase 4: Color System

Color creates mood, guides attention, and establishes identity.

### Modern Color Techniques

```css
/* Use oklch() for perceptually uniform color */
--primary: oklch(0.65 0.12 180);
--primary-light: color-mix(in oklch, var(--primary), white 30%);
--primary-dark: color-mix(in oklch, var(--primary), black 20%);

/* Warm neutrals, never pure gray */
--surface: oklch(0.97 0.005 80);
--text: oklch(0.20 0.01 80);
--text-secondary: oklch(0.45 0.01 80);
```

### Color Rules

- **Intentional palette**: Every color has a reason. Not random, not default.
- **Semantic usage**: Colors map to meaning (primary action, success, warning, error, neutral).
- **High contrast**: WCAG AA minimum (4.5:1 body, 3:1 large text/UI components).
- **10% accent rule**: Only 10% of the interface uses accent colors. 90% is neutrals.
- **No pure values**: No `#000`, `#fff`, or chromaless grays. Always tint.

---

## Phase 5: Layout Architecture

Layout creates rhythm, hierarchy, and visual interest.

### Principles

- **Content-driven breakpoints**: Break where the content breaks, not at arbitrary device widths.
- **Mobile-first**: Start with single column, add complexity at wider viewports.
- **Fluid sizing**: Use `clamp()` for spacing and typography that scales smoothly.
- **Asymmetry**: Left-aligned content with intentional asymmetric layouts feels designed.
- **Rhythm through variation**: Alternate between dense and spacious sections.

### Modern CSS Layout

```css
/* Container queries for component-level adaptation */
.card-container { container-type: inline-size; }
@container (min-width: 400px) { .card { flex-direction: row; } }

/* :has() selector for parent-aware styling */
.form-group:has(:invalid) { border-color: var(--error); }

/* View transitions for page-level animation */
@view-transition { navigation: auto; }

/* Subgrid for aligned nested layouts */
.grid-item { display: grid; grid-template-rows: subgrid; }
```

### Content Width

- Body text: max-width 65ch
- Wide content (tables, dashboards): max-width 1200-1400px
- Full-bleed sections: edge-to-edge with internal padding

---

## Phase 6: Component Design

Each component should feel considered, not assembled from a generic library.

### Design Principles Per Component

- **Buttons**: Clear hierarchy (primary, secondary, ghost). Specific verb+object labels ("Save changes", not "Submit"). One primary per view.
- **Forms**: Generous spacing between fields. Clear labels above inputs (not just placeholders). Inline validation with helpful messages.
- **Cards**: Only when content is a discrete, actionable unit. Vary card sizes and layouts. Never identical grids.
- **Navigation**: Appropriate to context (sidebar for desktop, bottom bar for mobile). Active state clearly distinct.
- **Tables**: Zebra striping or clear row separation. Sticky headers. Sortable columns indicated. Adequate cell padding.
- **Modals**: Use sparingly — only when inline alternatives don't work. Backdrop click to dismiss. Focus trapped inside.

---

## Phase 7: Copy and Content

Words are design. Cut ruthlessly.

### Rules

- **Cut word count by 50%**: The first draft is always too long. Remove every word that doesn't earn its place.
- **Specific labels**: "Save changes" not "Submit". "Delete account" not "OK".
- **Active voice**: "You created 3 projects" not "3 projects were created".
- **No placeholder text in production**: Every string should be final copy, not lorem ipsum.
- **Error messages tell what, why, how**: "Email already registered. Try signing in instead." not "Invalid input."

---

## Phase 8: Visual Polish

The details that separate good from great.

### Checklist

- **Consistent border radius**: Use one radius for small elements (4-6px), one for medium (8-12px), one for large (16-24px).
- **Shadow system**: 3 levels — subtle (cards), medium (dropdowns), deep (modals). Consistent direction and warmth.
- **Icon consistency**: Same style (outlined or filled, not mixed), same weight, same size grid.
- **Alignment**: Elements snap to a consistent grid. Optical alignment where mathematical alignment looks wrong.
- **Transition consistency**: Same easing and duration for similar interactions throughout.
- **Focus states**: Visible, consistent, using the primary color ring pattern.

---

## Phase 9: The AI Test

Final check against the core question:

**"If you said AI made this, would they believe immediately? If yes, that's the problem."**

### Pass Criteria

- The design has a clear aesthetic point of view
- Typography choices are distinctive and intentional
- Layout breaks from the standard 3-column grid template
- Color palette feels curated, not defaulted
- There's at least one element of visual surprise or delight
- The overall impression is "someone designed this" not "something generated this"

---

## Phase 10: Responsive Implementation

Build mobile-first, enhance upward.

### Breakpoint Strategy

```css
/* Mobile-first base styles */
.layout { display: grid; gap: 1rem; }

/* Tablet: introduce sidebar */
@media (min-width: 768px) {
  .layout { grid-template-columns: 240px 1fr; }
}

/* Desktop: increase density */
@media (min-width: 1024px) {
  .layout { grid-template-columns: 280px 1fr 300px; }
}
```

### Fluid Spacing

```css
--space-xs: clamp(0.25rem, 0.5vw, 0.5rem);
--space-sm: clamp(0.5rem, 1vw, 0.75rem);
--space-md: clamp(1rem, 2vw, 1.5rem);
--space-lg: clamp(1.5rem, 3vw, 3rem);
--space-xl: clamp(2rem, 5vw, 5rem);
```

---

## Output Structure

1. **Design Direction**: Chosen aesthetic with purpose, tone, differentiation, and references.
2. **Anti-Pattern Check**: AI fingerprints explicitly avoided, with what was done instead.
3. **Component Specs**: For each component — visual design, interaction behavior, responsive behavior, and accessibility notes.
4. **Implementation Notes**: Modern CSS techniques used, font loading strategy, color system definition, and layout approach.
5. **Code**: Complete, production-ready code implementing the design.
6. **Polish Checklist**: Final verification of consistency, alignment, transitions, and focus states.

# Spatial Design Reference Methodology

You are performing a spatial design reference consultation, providing guidance on spacing systems, grid layouts, visual hierarchy through space, container queries, and optical adjustments.

## Section 1: 4pt Base Unit

All spacing values should be multiples of 4px. This constraint creates visual consistency across every element, component, and layout in the interface.

**The 4pt scale**: 4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96px.

| Value | Use Case |
|-------|----------|
| 4px | Icon-to-label gap, inline element spacing, tight padding |
| 8px | Grouped item spacing, compact component padding |
| 12px | Between related form fields, small card padding |
| 16px | Default component padding, standard gap between elements |
| 20px | Slightly generous component padding |
| 24px | Between related sections, card padding |
| 32px | Between distinct sections, generous component padding |
| 48px | Major section separation, page-level gutters |
| 64px | Large section breaks, hero spacing |
| 96px | Page-level breathing room, header/footer margins |

**Why not arbitrary values**: 7px, 13px, 22px create visual noise. The eye detects inconsistency even when the conscious mind does not. A 4pt grid ensures that elements align and spacing relationships are proportional.

**Checking alignment**: zoom to 400% and overlay a 4px grid. Every spacing value should snap to a grid line.

## Section 2: Semantic Spacing Tokens

Name spacing by intent, not by value. This decouples design decisions from implementation:

| Token | Value | Purpose |
|-------|-------|---------|
| `--space-xs` | 4px | Inline spacing, icon gaps, tight associations |
| `--space-sm` | 8px | Tight grouping, compact layouts, chip padding |
| `--space-md` | 16px | Default padding, standard gaps between components |
| `--space-lg` | 24px | Between related sections, card internal spacing |
| `--space-xl` | 32px | Between distinct sections, panel gutters |
| `--space-2xl` | 48px | Major section separation, layout gutters |
| `--space-3xl` | 64-96px | Page-level breathing room, hero margins |

**Usage rules**:
- Components use `--space-sm` through `--space-lg` internally
- Layout uses `--space-xl` through `--space-3xl` between components
- Never use raw pixel values in component CSS — always reference tokens
- Scale tokens responsively: `--space-lg` might be 24px on desktop but 16px on mobile

## Section 3: Self-adjusting Grids

Use CSS Grid with `auto-fit` and `minmax()` for layouts that adapt to content and container width without media queries:

```css
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--space-lg);
}
```

| Pattern | CSS | Behavior |
|---------|-----|----------|
| Auto-fill cards | `repeat(auto-fit, minmax(250px, 1fr))` | Cards fill available space, wrap when container narrows |
| Sidebar + content | `minmax(200px, 300px) 1fr` | Sidebar has flexible range, content takes remainder |
| Dashboard widgets | `repeat(auto-fit, minmax(300px, 1fr))` | Widgets reflow from 3-column to 2-column to 1-column |
| Gallery | `repeat(auto-fill, minmax(150px, 1fr))` | Thumbnails fill space, auto-fill leaves empty tracks |

**auto-fit vs auto-fill**: `auto-fit` collapses empty tracks (items stretch to fill). `auto-fill` keeps empty tracks (items maintain minimum size with gaps). Use `auto-fit` for most card layouts, `auto-fill` for galleries where consistent item size matters.

**Avoid fixed column counts** when content is dynamic. `grid-template-columns: repeat(3, 1fr)` breaks when there are fewer than 3 items or when the container is too narrow.

## Section 4: Visual Hierarchy via Space

Spacing IS the hierarchy. You do not need borders, backgrounds, or dividers when spacing alone communicates grouping and separation.

**Proximity principle**: elements that are close together are perceived as related. Elements with more space between them are perceived as separate groups.

| Spacing Intent | Value Range | Effect |
|---------------|-------------|--------|
| Tight grouping | 4-12px | "These items are a unit" — label+input, icon+text |
| Standard separation | 16-24px | "These items are siblings" — list items, form fields |
| Section boundary | 32-48px | "These are different groups" — card sections, form groups |
| Major division | 64-96px | "These are different contexts" — page sections, content zones |

**The contrast matters most**: the difference between tight spacing and generous spacing IS the hierarchy. If you use 16px everywhere, there is no hierarchy. If you use 8px within groups and 48px between groups, the structure is immediately visible.

**Removing borders**: before adding a border or divider line, try increasing the spacing between groups instead. If 32px of space clearly separates two sections, the border is decorative noise.

## Section 5: Container Queries

Container queries let components adapt to their container, not the viewport. This makes components truly reusable — they work in a sidebar, a modal, or a full-width layout without modification.

```css
.card-container {
  container-type: inline-size;
}

@container (min-width: 400px) {
  .card { /* horizontal layout */ }
}

@container (max-width: 399px) {
  .card { /* stacked layout */ }
}
```

| Rule | Detail |
|------|--------|
| Set `container-type: inline-size` on the parent | Required — children cannot query a container that does not declare itself |
| Use `@container` instead of `@media` for component internals | Components should not know about the viewport |
| Name containers for clarity | `container-name: sidebar` + `@container sidebar (min-width: 200px)` |
| Nest containers carefully | A container query resolves against the nearest ancestor with `container-type` |

**When to use container queries vs media queries**:
- Container queries: component layout decisions (card orientation, grid columns within a component)
- Media queries: page layout decisions (sidebar visibility, navigation style, overall page structure)

## Section 6: Optical Adjustments

Mathematical precision does not always equal visual correctness. The eye perceives geometry differently than a pixel grid.

| Illusion | Fix |
|----------|-----|
| Mathematical center looks too high | Offset content down 5-10% from true center. For a 500px container, place content at ~255px instead of 250px. |
| Round shapes look smaller than rectangles | Give circular elements ~10% more padding than rectangular ones at the same size. A 40px circle icon needs the visual weight of a ~44px square. |
| Text with capitals looks uneven | First line of all-caps text needs slightly less top padding because capitals already have built-in whitespace above. |
| Horizontal lines look thinner than vertical | Horizontal rules or borders may need 1px more thickness to appear equal weight to vertical ones. |
| Right-aligned text looks indented | Right-aligned text in a container appears to float away from the edge. Add a slight right padding reduction or visual anchor. |
| Nested spacing compounds | A card inside a card: inner card padding + outer card padding = too much space visually. Reduce inner padding when nesting. |

**Practical approach**: design to the grid first (mathematically correct), then adjust by 1-4px where things "look wrong." Document these optical adjustments with comments so future developers understand the intentional deviation.

## Output Structure

When providing spatial design guidance:

1. **Context assessment**: what the user is spacing and the layout structure
2. **Token recommendations**: which spacing tokens to use and where
3. **Grid strategy**: whether a self-adjusting grid applies and the pattern to use
4. **Hierarchy check**: whether the current spacing creates clear visual grouping
5. **Optical notes**: any adjustments needed for visual correctness

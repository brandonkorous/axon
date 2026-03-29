# Extract Components Methodology

You are performing a component extraction analysis to identify reusable patterns, consolidate duplicated implementations, and enrich the design system with well-defined, generalized components.

**Core principle:** Extract what is clearly reusable now (3+ instances), not speculative patterns. Premature abstraction is worse than duplication.

---

## Phase 1: Discovery — Find Patterns

### Pattern Types to Identify

| Type               | What to Look For                                        | Examples                              |
|--------------------|---------------------------------------------------------|---------------------------------------|
| UI Components      | Repeated visual elements with similar structure         | Cards, badges, avatars, stat blocks   |
| Design Tokens      | Hard-coded values that should be variables              | Colors, spacing, shadows, radii       |
| Layout Patterns    | Repeated structural arrangements                        | Grid layouts, sidebar+content, stacks |
| Interaction Patterns| Repeated behavioral sequences                          | Dropdown menus, modals, toast notifications |

### Discovery Process

1. **Visual scan**: Look for elements that appear similar across different screens or sections.
2. **Code scan**: Search for duplicated markup structures, repeated style blocks, similar component logic.
3. **Token scan**: Find hard-coded values (hex colors, pixel values, font sizes) that repeat across files.
4. **Behavioral scan**: Identify similar interaction patterns implemented differently in different places.

### Pattern Documentation

For each discovered pattern, record:
- **Name**: Descriptive name for the pattern
- **Instance count**: How many times it appears (must be 3+ to justify extraction)
- **Locations**: Where each instance exists in the codebase
- **Variations**: How instances differ from each other
- **Current implementation**: Is it already a component, or are instances independent?

### Red Flags — What NOT to Extract
- Patterns with fewer than 3 instances (wait for the third before extracting)
- Elements that look similar but serve fundamentally different purposes
- Patterns where every instance has significant unique logic
- Components that would require more props than lines of markup

---

## Phase 2: Planning — Prioritize Extraction

### Prioritization Criteria

Rate each candidate 1-5 on three factors:

| Factor          | 1 (Low)                         | 5 (High)                            |
|-----------------|---------------------------------|--------------------------------------|
| **Frequency**   | 3 instances                     | 10+ instances                        |
| **Inconsistency**| Instances are nearly identical | Instances diverge significantly       |
| **Maintenance cost** | Simple, rarely changes      | Complex, frequently modified         |

**Priority score** = Frequency + Inconsistency + Maintenance cost. Extract highest scores first.

### Component API Design

For each component to extract, define:
- **Props**: What varies between instances? Each variation becomes a prop.
- **Slots/children**: What content is injected by the consumer?
- **Variants**: Are there named variants (e.g., size: sm/md/lg) or is it continuous?
- **Defaults**: What is the most common configuration? Make it the default.

**Rules for good component APIs:**
- Fewer than 8 props (if more, split into sub-components)
- Required props should be minimal (1-3)
- Naming follows existing conventions in the design system
- Boolean props for binary options, string/enum for multiple options
- Avoid prop combinations that conflict or are mutually exclusive

### Naming Conventions

Align with the existing design system naming:
- If the system uses `Button`, `Card`, `Badge` — follow that pattern
- If the system uses prefixes (`ui-button`, `ds-card`) — maintain the prefix
- Compound components: `Dialog.Header`, `Dialog.Body`, `Dialog.Footer`
- Variants: `variant="primary"` not `isPrimary={true}` (unless the system already uses boolean props)

---

## Phase 3: Extraction — Build Generalized Versions

### Extraction Process

For each component:

1. **Start from the simplest instance**: Pick the most basic usage as the foundation.
2. **Add variations as props**: For each difference between instances, add a prop or slot.
3. **Consolidate styles**: Merge all style variations into the component, controlled by props.
4. **Extract tokens**: Any hard-coded values become design tokens.
5. **Add defaults**: The most common prop values become defaults.
6. **Write the component**: Clean implementation with clear prop types and documentation.

### Quality Checklist

Before considering a component "extracted":
- [ ] Works for all identified instances without modification
- [ ] Props are typed and documented
- [ ] Default props cover the most common use case
- [ ] Accessibility attributes are built-in (ARIA, keyboard, focus management)
- [ ] Responsive behavior is handled internally
- [ ] Dark mode / theme support works
- [ ] Edge cases handled (empty content, overflow, long text)

---

## Phase 4: Migration — Replace and Document

### Migration Strategy

For each extracted component:

1. **Create the component** in the design system directory.
2. **Replace one instance** as a proof of concept. Verify it works identically.
3. **Replace remaining instances** one at a time, verifying each.
4. **Delete old code** once all instances are migrated.
5. **Document the component**: usage examples, props table, do/don't guidelines.

### Migration Order
- Start with low-risk instances (non-critical pages, internal tools)
- Move to high-visibility instances last
- Never migrate all instances in a single change — keep diffs reviewable

### Documentation Template
Each extracted component should have:
- **Purpose**: One sentence describing what this component is for
- **Usage**: Code example showing the most common usage
- **Props**: Table of all props with type, default, and description
- **Variants**: Visual examples of each variant
- **Do / Don't**: Common misuses to avoid

---

## Output Structure

1. **Discovery Report**: All patterns found, grouped by type (UI components, tokens, layouts, interactions), each with instance count and locations.
2. **Priority Matrix**: Patterns ranked by extraction priority with scores.
3. **Extraction Plan**: For each component to extract: proposed name, props API, slot/children strategy, and design token needs.
4. **Migration Steps**: Ordered plan for replacing instances, starting with lowest risk.
5. **Token Additions**: Design tokens that need to be created to support the extracted components.
6. **Effort Estimate**: Rough sizing for each extraction (small: <1hr, medium: 1-4hr, large: 4hr+).

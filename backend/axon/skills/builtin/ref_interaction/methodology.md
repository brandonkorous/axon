# Interaction Design Reference Methodology

You are performing an interaction design reference consultation, providing guidance on interactive states, focus management, form design, native platform tools, undo patterns, and keyboard navigation.

## Section 1: 8 Interactive States

Every interactive element should define all 8 states. Even if some share styles, explicitly considering each state prevents gaps in the user experience.

| State | Description | Visual Signal |
|-------|-------------|---------------|
| Default | Resting, idle, no user interaction | Base appearance — the "normal" look |
| Hover | Mouse cursor is over the element | Subtle highlight — background tint, slight scale, underline |
| Focus | Element has keyboard focus | Focus ring — 2-3px outline with offset, 3:1 contrast |
| Active | Being pressed or clicked (mousedown / touchstart) | Compressed — slight scale-down, darker background, pressed appearance |
| Disabled | Not available for interaction | Reduced opacity (40-50%), no pointer events, `cursor: not-allowed` |
| Loading | Processing an action | Spinner or skeleton replacing content, disabled interaction |
| Error | Invalid state or failed action | Error color border/background, error message visible |
| Success | Action completed successfully | Success color flash, checkmark, then return to default |

**State transitions**:
- Default → Hover → Active → Loading → Success/Error → Default
- Default → Focus → Active → Loading → Success/Error → Default (keyboard path)
- Any state → Disabled (externally controlled)

**Common mistakes**:
- Missing active state — button looks the same when pressed and unpressed
- Hover styling applied to touch — `:hover` sticks on mobile after tap
- Disabled without explanation — user doesn't know WHY it's disabled (add a tooltip)
- Loading state with no timeout — infinite spinner with no fallback

## Section 2: Focus Management

### Focus Visibility

Use `:focus-visible` instead of `:focus` to show focus rings only for keyboard navigation:

```css
/* Shows ring only for keyboard focus, not mouse clicks */
button:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}

/* Remove default outline — only if replacing with focus-visible */
button:focus:not(:focus-visible) {
  outline: none;
}
```

### Focus Ring Specifications

| Property | Value | Reason |
|----------|-------|--------|
| Width | 2-3px | Visible but not overwhelming |
| Style | solid | Dashed or dotted are harder to see |
| Offset | 2px | Prevents ring from overlapping element content |
| Contrast | 3:1 against background | WCAG requirement for UI components |
| Color | Primary brand color or high-contrast default | Consistent with the application's interactive color |

### Focus Trapping

Modals and dialogs must trap focus — Tab cycles within the dialog, not behind it:

1. On open: move focus to the first focusable element inside the dialog
2. Tab from last element wraps to first element
3. Shift+Tab from first element wraps to last element
4. On close: return focus to the element that triggered the dialog

The native `<dialog>` element handles focus trapping automatically — use it.

### Skip Links

Provide a "Skip to main content" link as the first focusable element on the page. It should be visually hidden until focused:

```css
.skip-link {
  position: absolute;
  top: -100%;
  left: 0;
}
.skip-link:focus {
  position: static;
}
```

## Section 3: Label Requirements

### Every Input Needs a Visible Label

| Pattern | Acceptable | Why |
|---------|-----------|-----|
| `<label>` paired with `<input>` | Yes | Accessible, clickable, always visible |
| Floating label | Yes (if visible in all states) | Stays visible after input has value |
| Placeholder only | No | Disappears on focus — user forgets what the field is for |
| Adjacent text without `for` attribute | No | Not programmatically associated — screen readers miss it |

### Form Grouping

- Use `<fieldset>` and `<legend>` to group related inputs (radio groups, address fields, date ranges)
- `<legend>` acts as a group label — screen readers announce it before each input in the group
- Nested fieldsets are valid for sub-groups

### Error Association

- Use `aria-describedby` to link error messages to their inputs
- Error messages should appear near the input, not in a summary at the top
- Inline validation on blur is preferred over submit-time validation — errors appear in context

## Section 4: Native Tools First

Prefer built-in HTML elements and APIs over custom implementations. Native tools provide accessibility, keyboard handling, and platform integration for free.

| Need | Native Solution | Advantage Over Custom |
|------|----------------|----------------------|
| Modal dialog | `<dialog>` element | Focus trapping, Escape to close, backdrop, `showModal()` API |
| Tooltip / dropdown | Popover API (`popover` attribute) | Auto-positioning, light dismiss, no z-index management |
| Accordion | `<details>` / `<summary>` | Expand/collapse, keyboard accessible, no JavaScript needed |
| Positioned element | CSS anchor positioning | Declarative positioning relative to anchor, auto-flip on overflow |
| Date input | `<input type="date">` | Native date picker, locale-aware, keyboard navigable |
| Color picker | `<input type="color">` | System color picker, no library needed |
| Progress | `<progress>` and `<meter>` | Semantic, accessible, styleable |

**When to go custom**: only when native behavior does not meet the interaction requirement. Document WHY the native solution was insufficient — this prevents future developers from rebuilding what the platform already provides.

## Section 5: Undo Over Confirmation

### The Problem with Confirmation Dialogs

Confirmation dialogs ("Are you sure?") suffer from habituation — users click "Yes" without reading after the first few encounters. They interrupt flow, add a click to every action, and provide a false sense of safety.

### The Undo Pattern

Instead of asking before the action, perform the action immediately and offer a brief undo window:

| Step | Implementation |
|------|---------------|
| 1. User clicks "Delete" | Item is removed from view immediately |
| 2. Toast appears | "Email deleted. Undo?" with a 5-8 second countdown |
| 3. User ignores toast | After countdown, deletion is committed (soft-delete or hard-delete) |
| 4. User clicks "Undo" | Item is restored instantly, toast dismissed |

### When Confirmation IS Appropriate

| Scenario | Why Undo Doesn't Work |
|----------|----------------------|
| Irreversible destructive action (delete account) | Cannot be undone technically |
| Action affects other users | Undo only applies to the actor's view |
| Financial transaction | Reversal has real-world cost |
| Publishing / broadcasting | Cannot un-send a notification |

For these cases, use a confirmation that requires deliberate action — not just "OK" but typing the resource name or a confirmation phrase.

## Section 6: Keyboard Navigation

### Core Patterns

| Key | Action | Context |
|-----|--------|---------|
| Tab | Move to next focusable element | Global navigation |
| Shift+Tab | Move to previous focusable element | Global navigation (reverse) |
| Enter | Activate button / submit form | Buttons, links, form submission |
| Space | Activate button / toggle checkbox | Buttons, checkboxes, switches |
| Escape | Close modal / dismiss popup / cancel | Overlays, dropdowns, search |
| Arrow keys | Navigate within a component | Tabs, menus, radio groups, lists |
| Home/End | Jump to first/last item | Lists, tabs, menus |

### Component-specific Navigation

| Component | Arrow Behavior | Tab Behavior |
|-----------|---------------|--------------|
| Tab bar | Left/Right moves between tabs | Tab moves focus OUT of the tab bar (one tab stop) |
| Menu | Up/Down moves between items | Tab moves focus OUT of the menu |
| Radio group | Up/Down or Left/Right selects option | Tab moves focus OUT of the group |
| Tree view | Up/Down moves, Left/Right expands/collapses | Tab moves focus OUT of the tree |
| Grid / Table | Arrow keys move between cells | Tab moves focus OUT of the grid |

**Roving tabindex**: within a component (tabs, radio group), only one item has `tabindex="0"` (the active/selected item). Others have `tabindex="-1"`. Arrow keys move `tabindex="0"` between items. This makes Tab enter and exit the component as a single stop.

### Logical Tab Order

Tab order should follow visual layout: left-to-right, top-to-bottom for LTR languages. If the tab order does not match the visual order, the layout or the DOM order needs fixing — do not use `tabindex` values greater than 0 to force order.

## Output Structure

When providing interaction design guidance:

1. **Context assessment**: what element or pattern the user is implementing
2. **State coverage**: which of the 8 states need attention and how to style each
3. **Focus behavior**: how focus should move and appear for this element
4. **Keyboard plan**: which keys do what within this component
5. **Native alternative**: whether a native HTML element can replace the custom implementation
6. **Accessibility check**: ARIA attributes, labels, and announcements needed

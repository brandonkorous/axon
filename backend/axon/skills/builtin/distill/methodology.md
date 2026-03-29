# Distill Methodology

You are performing a complexity reduction pass to strip an interface down to its essential purpose while preserving discoverability and usability.

---

## Step 1: Extract Essential Purpose

Answer the core question: **"If you could only keep 3 things on this screen, which 3?"**

- Identify the ONE primary goal of the view (not two, not three — one)
- State it as a single sentence: "This screen lets the user ___."
- List supporting goals in priority order
- Flag anything present that does not serve the primary or supporting goals

**The litmus test:** If a user opens this screen, completes the primary goal, and leaves — did the screen succeed? If yes, everything else is secondary.

---

## Step 2: 6-Dimension Simplification Audit

Evaluate complexity across each dimension. Rate current complexity 1-5 (1 = simple, 5 = overwhelming).

### Dimension 1: Information Architecture
- How many distinct categories of information are visible?
- Are there items that belong on a different screen?
- Is there redundant information (same data shown two ways)?
- Could sections be collapsed or moved to sub-views?

**Target:** No more than 3-4 information categories visible at once.

### Dimension 2: Visual Design
- How many visual styles, colors, and decorative elements are present?
- Are there purely decorative elements that add no meaning?
- Could visual variety be reduced without losing hierarchy?
- Are borders, shadows, and backgrounds all earning their place?

**Target:** Remove decoration that does not communicate. Every visual treatment should have a purpose.

### Dimension 3: Layout
- How many columns, rows, and sections exist?
- Could the layout be flattened (fewer nesting levels)?
- Are there card-in-card or container-in-container patterns?
- Could a simpler single-column or two-column layout work?

**Target:** Minimum viable layout structure. Fewer containers, less nesting.

### Dimension 4: Interactions
- How many clickable/interactive elements are visible?
- Are there actions that fewer than 20% of users need?
- Could actions be consolidated (e.g., dropdown menu for rare actions)?
- Is the primary action immediately obvious?

**Target:** One clear primary action. Secondary actions de-emphasized. Rare actions hidden behind progressive disclosure.

### Dimension 5: Content
- How many words are on the screen?
- Can any text be cut in half while preserving meaning?
- Are there instructional paragraphs that could be inline hints?
- Could labels be shorter without losing clarity?

**Target:** Minimum words for maximum clarity. Every word earns its place.

### Dimension 6: Code
- How many components/elements are rendered?
- Could components be consolidated?
- Are there conditional branches that add rarely-seen UI?
- Could state be simplified (fewer modes, fewer flags)?

**Target:** Fewer components, less conditional rendering, simpler state.

---

## Step 3: Triage — Keep, Demote, Remove

Categorize every element on the screen:

| Category   | Definition                                                    | Action                              |
|------------|---------------------------------------------------------------|-------------------------------------|
| **Keep**   | Directly serves the primary goal                              | Leave in place, possibly elevate    |
| **Demote** | Useful but secondary — does not serve the primary goal        | Move to progressive disclosure, secondary view, or smaller treatment |
| **Remove** | Does not serve any identified goal, or duplicates other content | Delete entirely                     |

**The demotion spectrum** (from most visible to least):
1. Visible on the main view but smaller/quieter
2. Behind a "Show more" or expandable section
3. In a secondary tab or panel
4. In a settings or advanced options area
5. Removed entirely (available via search or help)

---

## Step 4: Progressive Disclosure Strategy

For demoted elements, design the progressive disclosure:
- **Default view**: Only primary goal elements. Clean, focused, fast.
- **Expanded view**: Secondary information revealed on demand.
- **Detail view**: Full complexity available but not forced on anyone.

**Rules for progressive disclosure:**
- The trigger to reveal more must be obvious (not hidden)
- The most common next action after the primary goal should be one click away
- Never hide something that 50%+ of users need on every visit
- Revealed content should feel like a natural extension, not a surprise

---

## Step 5: Prevent Oversimplification

Check that simplification has not gone too far:
- Can users still discover all features within 2-3 clicks?
- Are power user workflows still possible (even if less prominent)?
- Is critical information still visible without extra interaction?
- Does the interface still communicate what it does to a new user?

**Warning signs of oversimplification:**
- Users must memorize hidden feature locations
- Essential actions require too many clicks to reach
- The interface looks clean but communicates nothing about its capabilities
- New users cannot figure out what the screen is for

---

## Step 6: Complexity Scoring

Rate before and after on a 0-10 scale:

| Score | Level          | Description                                        |
|-------|----------------|----------------------------------------------------|
| 0-2   | Minimal        | Almost nothing on screen. May be too sparse.       |
| 3-4   | Simple         | Focused, clear purpose. Easy to scan.              |
| 5-6   | Moderate       | Some density but manageable. Reasonable for experts.|
| 7-8   | Complex        | Dense, requires effort to parse. Many competing elements.|
| 9-10  | Overwhelming   | Too much everything. Cognitive overload.           |

**Target range:** 3-5 depending on audience (consumer apps: 3-4, professional tools: 4-5).

---

## Output Structure

1. **Essential Purpose**: One sentence describing the primary goal of the view.
2. **Top 3 Keepers**: The 3 most important elements that must stay.
3. **Complexity Scores**: Before and after scores (0-10) for each of the 6 dimensions.
4. **Triage Table**: Every element categorized as keep/demote/remove with justification.
5. **Progressive Disclosure Plan**: How demoted elements will be accessed.
6. **Oversimplification Check**: Confirmation that discoverability is preserved.
7. **Recommended Actions**: Ordered list of specific changes to implement the distillation.

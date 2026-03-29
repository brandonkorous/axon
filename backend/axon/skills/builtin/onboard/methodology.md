# Onboard Methodology

You are performing an onboarding and first-time user experience assessment to design a path from signup to value realization that feels natural, not forced.

---

## Step 1: Identify the Aha Moment

The "aha moment" is when the user first experiences the product's core value — not when they understand it intellectually, but when they feel it.

### Analysis

- What is the single action that delivers the product's core value?
- How many steps currently stand between signup and that action?
- Can any of those steps be deferred or eliminated?
- What does the user need to know to reach that moment? (Minimize this list ruthlessly.)

### User Type Calibration

Adjust complexity based on `user_type` if provided:

| User Type | Approach |
|-----------|----------|
| Beginner | Hand-holding, visual guidance, simple vocabulary, celebrate small wins |
| Intermediate | Lighter guidance, option to skip, focus on differentiating features |
| Technical | Minimal guidance, quick-start code/config, documentation links, keyboard shortcuts |
| Mixed | Layered approach — quick path for experienced users, expandable help for beginners |

---

## Step 2: Welcome and Setup Flow

Design the initial experience from first visit to first meaningful action.

### Principles

- **Value proposition first**: Before asking for anything, show what the user gets.
- **Minimal required data**: Collect only what's needed to start. Defer profile completion, preferences, and integrations.
- **Show progress**: If setup has multiple steps, show a progress indicator (but keep it to 3-5 steps max).
- **Allow skipping**: Every non-essential step should be skippable with a clear "skip" option.
- **Smart defaults**: Pre-fill what you can. Reduce decisions to confirmations.

### Anti-Patterns to Avoid

- Asking for information before showing value
- Requiring email verification before any access
- Multi-page forms before the user sees the product
- Forcing team invites or integrations during initial setup
- "Tell us about yourself" surveys that don't visibly affect the experience

---

## Step 3: Empty States

Empty states are onboarding moments — they appear at the exact point where a feature becomes relevant.

### Design Requirements

Every empty state must include:

1. **What this area is for**: One sentence explaining the value, not the feature name.
2. **Why it's empty**: Briefly acknowledge the blank state ("No projects yet" not just a blank screen).
3. **Primary action**: A clear, prominent button to create the first item.
4. **Optional illustration**: A simple visual that reinforces the value proposition (not decorative stock art).

### Empty State Quality Scale

| Rating | Criteria |
|--------|----------|
| 4 | Explains value, provides action, includes helpful context or illustration |
| 3 | Explains value and provides action |
| 2 | Acknowledges emptiness and provides action but doesn't explain value |
| 1 | Just says "Nothing here" or shows blank space with an add button |
| 0 | Completely blank — no indication of what should be here or what to do |

### Key Empty States to Design

- Dashboard/home (first login)
- Primary content list (no items yet)
- Search results (no matches)
- Filtered view (filters too narrow)
- Activity feed (no activity yet)
- Notifications (nothing new)

---

## Step 4: Contextual Tooltips

Tooltips should appear when the user is near a feature, not on a timer or forced sequence.

### Design Rules

- **Triggered by proximity**: Show when user hovers near or navigates to a feature area for the first time.
- **One at a time**: Never show multiple tooltips simultaneously.
- **Dismissible**: Always include a clear close/dismiss action.
- **Non-blocking**: Tooltips should not cover the element they're explaining.
- **Progressive**: Show basic tooltips first, advanced ones after the user has used basic features.
- **Remember state**: Once dismissed, don't show the same tooltip again (persist in user preferences).

### Tooltip Content Formula

"[What this does] — [Why you'd use it]"

Keep to 1-2 sentences maximum. If it needs more, use a different format (popover, panel, guide).

---

## Step 5: Feature Tour

A guided walkthrough of key features, shown once and never forced.

### Design Rules

- **3-7 steps maximum**: More than 7 and users will abandon. Prioritize ruthlessly.
- **Skippable**: "Skip tour" visible on every step. Never trap users.
- **Resumable**: If interrupted, offer to resume later (not restart from the beginning).
- **Highlight real UI**: Point to actual interface elements, not screenshots or illustrations.
- **Action-oriented**: Each step should ask the user to do something, not just read.
- **Progress indicator**: Show "Step 2 of 5" so users know the commitment.

### Tour Step Structure

For each step:
1. **Target element**: What UI element is being highlighted
2. **Title**: 3-5 words describing the feature
3. **Body**: 1-2 sentences on what it does and why it matters
4. **Action**: What the user should try ("Click here to create your first...")
5. **Placement**: Where the tooltip appears relative to the target (top, bottom, left, right)

---

## Step 6: Interactive Tutorials

For complex features, learn-by-doing beats learn-by-reading.

### Design Principles

- **Sandbox mode**: Let users experiment with sample data, not their real data.
- **Immediate feedback**: Every action produces a visible result within 1 second.
- **Forgiving**: Undo is always available. Mistakes are cheap.
- **Celebrate completion**: Mark tutorial completion visibly. Unlock a badge, show a success state.
- **Optional depth**: Basic tutorial for everyone, advanced tutorial for those who want it.

### Anti-Patterns

- **Forced tutorials**: Never block the product behind a mandatory tutorial.
- **Info-dumping**: Showing all features at once instead of progressively.
- **Blocking modals**: Interrupting the user's flow to teach something they didn't ask about.
- **Tooltip overload**: More than 3 tooltips visible in a session without user action.
- **Reading-heavy**: Paragraphs of text instead of interactive steps.
- **No escape hatch**: Tutorial with no skip or exit option.

---

## Step 7: Drop-Off Analysis

Identify where users are most likely to abandon the onboarding flow.

### Common Drop-Off Points

| Point | Risk | Mitigation |
|-------|------|------------|
| Signup form | High friction | Reduce fields, allow social auth |
| Email verification | Blocks access | Allow limited access before verification |
| Profile setup | Feels irrelevant | Defer to after first value moment |
| First feature use | Confusion | Guided first action with sample data |
| Return visit | Forgot context | Welcome back state with next suggested action |

### Success Metrics

- **Time to aha moment**: How long from signup to first value experience?
- **Setup completion rate**: What percentage complete the setup flow?
- **Tour completion rate**: What percentage finish the feature tour?
- **Day-1 retention**: Do users return within 24 hours?
- **Feature adoption**: Are users discovering features beyond the initial flow?

---

## Output Structure

1. **Aha Moment**: What it is, how many steps to reach it, and how to reduce that number.
2. **Onboarding Flow**: Step-by-step sequence with rationale, required vs. optional flags, and estimated time per step.
3. **Empty States**: For each key view — copy, action, and quality rating (0-4).
4. **Tour Steps**: 3-7 steps with target, title, body, action, and placement for each.
5. **Drop-Off Risks**: Identified risk points with mitigation strategies.
6. **Anti-Patterns Found**: Any current onboarding anti-patterns detected in the subject.
7. **Metrics to Track**: Recommended success metrics for measuring onboarding effectiveness.

# Design Review Methodology

You are performing a pre-implementation design audit, scoring a proposal across seven dimensions to identify gaps before any code is written.

## Philosophy: Boil the Lake

With AI assistance, completeness is near-free. Specify all edge cases, states, and interactions upfront rather than discovering them during implementation. Every ambiguity in a design becomes a decision made by a developer under time pressure — and those decisions are usually wrong.

The goal is not to slow down building. The goal is to make building faster by eliminating "what should happen when...?" questions before they arise.

## Step 1: Context Gathering

Before scoring, establish context:

1. **What is being designed?** — feature, page, flow, component, or system
2. **Who is it for?** — specific user type and their context of use
3. **What is the success metric?** — how do we know this design worked
4. **What exists already?** — design system, existing patterns, prior art
5. **What are the constraints?** — technical limitations, timeline, platform

## Step 2: Seven-Dimension Scoring

### Dimension 1: Information Architecture (0-10)

Evaluate how information is organized, prioritized, and navigated:

| Score | Level | Description |
|-------|-------|-------------|
| 0-2 | Poor | No clear hierarchy. User cannot find what they need. |
| 3-4 | Weak | Some structure but inconsistent. Navigation is confusing. |
| 5-6 | Adequate | Clear primary hierarchy. Some secondary elements misplaced. |
| 7-8 | Good | Strong hierarchy and navigation. Content is logically grouped. |
| 9-10 | Excellent | Information architecture is intuitive. Zero friction to find anything. |

Check for:
- Visual priority matches importance priority
- Navigation structure is predictable
- Content grouping follows user mental models
- Labels are specific and unambiguous
- No orphaned content (pages reachable only by direct URL)

### Dimension 2: Interaction State Coverage (0-10)

Every interactive element has multiple states. Evaluate completeness:

| State | Description | Common Oversight |
|-------|-------------|-----------------|
| Default | Normal resting state | Rarely missed |
| Hover | Mouse over (desktop) | Missing on custom components |
| Active/Pressed | During interaction | Often identical to hover |
| Focus | Keyboard navigation | Frequently forgotten entirely |
| Loading | Async operation in progress | Spinner only, no skeleton |
| Empty | No data to display | Generic "no results" message |
| Error | Something went wrong | Stack trace or generic "error" |
| Success | Operation completed | Flash message that disappears too fast |
| Partial | Some data, some missing | Not considered at all |
| Disabled | Cannot interact | Unclear why disabled |
| Overflow | Too much content | Text truncation without tooltip |

| Score | Level | Description |
|-------|-------|-------------|
| 0-2 | Poor | Only default state specified. |
| 3-4 | Weak | Default and one or two others. Major gaps. |
| 5-6 | Adequate | Most common states covered. Edge cases missing. |
| 7-8 | Good | All major states specified. Minor gaps in edge cases. |
| 9-10 | Excellent | Every state for every element is explicitly designed. |

### Dimension 3: User Journey & Emotional Arc (0-10)

Storyboard the emotional experience from arrival to completion:

1. **Entry point** — how does the user arrive? What is their mindset?
2. **First impression** — what do they see and feel in the first 3 seconds?
3. **Core task** — what is the primary action? How many steps?
4. **Friction points** — where might the user hesitate, get confused, or feel frustrated?
5. **Completion** — how does the user know they are done? What do they feel?
6. **Return motivation** — why would they come back?

| Score | Level | Description |
|-------|-------|-------------|
| 0-2 | Poor | No consideration of user journey. Feature exists in isolation. |
| 3-4 | Weak | Basic happy path described. No emotional consideration. |
| 5-6 | Adequate | Journey is mapped but friction points are not addressed. |
| 7-8 | Good | Clear journey with intentional emotional design at key moments. |
| 9-10 | Excellent | Every touchpoint is designed for both function and feeling. |

### Dimension 4: AI Slop Risk (0-10)

Detect generic AI-generated design patterns that lack intentional specificity:

| Pattern | AI Slop Signal | Intentional Alternative |
|---------|---------------|----------------------|
| Generic gradients | Blue-to-purple gradient on everything | Brand-specific color with purpose |
| Stock metaphors | Lightbulb for ideas, rocket for launch | Unique visual language |
| Buzzword copy | "Revolutionize your workflow" | Specific value proposition |
| Cookie-cutter layout | Hero, 3 cards, testimonials, CTA | Layout serves content structure |
| Default animations | Everything fades in on scroll | Motion serves a specific purpose |
| Over-decoration | Shadows, borders, gradients on every element | Restraint, whitespace, hierarchy |

| Score | Level | Description |
|-------|-------|-------------|
| 0-2 | High slop | Design feels AI-generated. No distinctive choices. |
| 3-4 | Moderate slop | Some generic patterns. A few intentional choices visible. |
| 5-6 | Low slop | Mostly intentional. A few lazy defaults remain. |
| 7-8 | Minimal slop | Nearly every choice is deliberate and specific. |
| 9-10 | Zero slop | Every element has a reason. Design has a clear point of view. |

### Dimension 5: Design System Alignment (0-10)

Conformance to existing design tokens, components, and patterns:

| Score | Level | Description |
|-------|-------|-------------|
| 0-2 | Disconnected | Uses none of the existing design system. Custom everything. |
| 3-4 | Loosely aligned | Some tokens used, many custom overrides. Inconsistent. |
| 5-6 | Partially aligned | Core components used. Some deviations justified, others not. |
| 7-8 | Well aligned | Consistent use of design system. Deviations are documented. |
| 9-10 | Fully aligned | 100% design system components and tokens. Feels like one product. |

Check for:
- Color tokens match the design system (not hardcoded hex values)
- Typography follows the type scale
- Spacing uses the spacing scale (not arbitrary pixel values)
- Components match existing patterns (buttons, forms, cards, modals)
- Icons match the existing icon style
- New patterns are documented as design system extensions

If no design system exists, score based on internal consistency within the proposal.

### Dimension 6: Responsive & Accessibility (0-10)

Mobile, tablet, keyboard, and screen reader compliance:

| Score | Level | Description |
|-------|-------|-------------|
| 0-2 | Non-compliant | Desktop only. No keyboard support. No ARIA. |
| 3-4 | Minimal | Basic responsive layout. Some keyboard support. No ARIA. |
| 5-6 | Partial | Responsive breakpoints defined. Keyboard works. ARIA incomplete. |
| 7-8 | Good | Full responsive design. Keyboard accessible. ARIA labels present. |
| 9-10 | Excellent | WCAG AA compliant. Tested with screen reader. Reduced motion supported. |

Check for:
- Responsive breakpoints (mobile 320px, tablet 768px, desktop 1024px+)
- Touch targets minimum 44x44px on mobile
- Keyboard navigation for all interactive elements
- Focus management (modals trap focus, returns focus on close)
- ARIA labels on non-text interactive elements
- Color contrast ratios meet WCAG AA (4.5:1 for text, 3:1 for large text)
- `prefers-reduced-motion` respected for animations
- Screen reader announcement for dynamic content changes

### Dimension 7: Unresolved Decisions (0-10, inverse scale)

10 means no ambiguity. 0 means many open questions.

| Score | Level | Description |
|-------|-------|-------------|
| 0-2 | Many open questions | Critical decisions unmade. Developers will guess. |
| 3-4 | Several gaps | Important edge cases undecided. Some guesswork required. |
| 5-6 | Some gaps | Minor decisions open. Core flows are clear. |
| 7-8 | Few gaps | Nearly everything specified. One or two edge cases open. |
| 9-10 | Fully specified | Every decision is made. Implementation is mechanical. |

List every unresolved decision with:
- **Decision**: What needs to be decided
- **Impact**: What happens if a developer guesses wrong
- **Recommendation**: Suggested resolution

## Step 3: Total Score Calculation

Sum all seven dimension scores for a total of 0-70:

| Total | Rating | Recommendation |
|-------|--------|---------------|
| 0-20 | Not ready | Major redesign needed before implementation |
| 21-35 | Needs work | Specific dimensions must be addressed |
| 36-50 | Acceptable | Can proceed with noted improvements |
| 51-60 | Good | Minor refinements only |
| 61-70 | Excellent | Ready for implementation |

## Step 4: Mockup Recommendations

Based on gaps identified, recommend specific mockups or prototypes:

1. **What to mock up** — the specific view, interaction, or state
2. **Why** — what question does this mockup answer
3. **Fidelity** — wireframe (structure), low-fi (layout + content), high-fi (visual design)
4. **Priority** — must-have before implementation vs. nice-to-have

## Step 5: Iterative Refinement

After initial scoring, offer specific improvements for the lowest-scoring dimensions. For each suggestion:
- What to change
- Why it improves the score
- Expected new score after the change

## Output Structure

```markdown
## Design Review: {Proposal Name}

### Dimension Scores

| # | Dimension | Score | Key Finding |
|---|-----------|-------|-------------|
| 1 | Information Architecture | {0-10} | {one-line finding} |
| 2 | Interaction State Coverage | {0-10} | {one-line finding} |
| 3 | User Journey & Emotional Arc | {0-10} | {one-line finding} |
| 4 | AI Slop Risk | {0-10} | {one-line finding} |
| 5 | Design System Alignment | {0-10} | {one-line finding} |
| 6 | Responsive & Accessibility | {0-10} | {one-line finding} |
| 7 | Unresolved Decisions | {0-10} | {one-line finding} |

**Total Score: {sum}/70 — {rating}**

### Detailed Analysis
{Per-dimension analysis with specific findings}

### Unresolved Decisions
| Decision | Impact | Recommendation |
|----------|--------|---------------|
| {decision} | {impact of guessing wrong} | {suggested resolution} |

### Mockup Recommendations
| Mockup | Why | Fidelity | Priority |
|--------|-----|----------|----------|
| {what} | {question it answers} | {wire/low/high} | {must/nice} |

### Quick Wins
{Top 3 changes that would most improve the total score}
```

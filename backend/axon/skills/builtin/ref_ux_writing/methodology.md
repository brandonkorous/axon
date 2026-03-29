# UX Writing Reference Methodology

You are performing a UX writing reference consultation, providing guidance on action-oriented language, error messaging, tone matching, conciseness, accessibility in copy, terminology consistency, and common rewrites.

## Section 1: Action-oriented Language

Buttons and CTAs should say what they DO, not what they ARE. Specific labels reduce cognitive load because the user can predict the outcome before clicking.

| Bad | Good | Why |
|-----|------|-----|
| Submit | Save changes | "Submit" is vague — save what? |
| OK | Delete account | "OK" hides the consequence |
| Continue | Start free trial | "Continue" to where? Be explicit |
| Click here | Download report | "Click here" says nothing about the action |
| Yes | Remove from team | "Yes" requires reading the question above |
| Cancel | Keep editing | "Cancel" what? The positive phrasing is clearer |

**Rules**:
- Use verb + noun: "Save draft", "Send invite", "Create project"
- The button label should make sense without reading anything else on the page
- Destructive actions use specific, unambiguous verbs: "Delete", "Remove", "Revoke" — never "OK" or "Yes"
- Primary action gets the specific label; secondary gets the softer alternative ("Delete account" / "Keep account")

## Section 2: Error Messaging Formula

Every error message has three parts: **what happened** + **why** + **how to fix**.

| Component | Purpose | Example |
|-----------|---------|---------|
| What happened | State the problem clearly | "Email address is invalid" |
| Why | Explain the constraint | "Must include @ and a domain" |
| How to fix | Give the next action | "Check the address and try again" |

### Bad vs Good Errors

| Bad | Problem | Good |
|-----|---------|------|
| "Invalid input" | No what, no why, no fix | "Email must include @ symbol. Check the address and try again." |
| "Something went wrong" | No specificity at all | "Could not save changes — the server is temporarily unavailable. Your edits are preserved locally. Try again in a few minutes." |
| "Error 422" | Technical code, no human meaning | "This email is already registered. Sign in instead or use a different email." |
| "You entered an invalid password" | Blames the user | "Password must be at least 8 characters with one number." |
| "Request failed" | No why, no fix | "Could not load messages — check your internet connection and refresh." |

### Tone in Errors
- Never blame the user ("You entered...", "You failed to...")
- Never be vague ("Something went wrong", "An error occurred")
- Be calm and specific — the user is already frustrated
- If the error is on your end, say so: "Our servers are experiencing issues"

## Section 3: Tone Matching

Match the emotional weight of the copy to the emotional context of the moment:

| Context | Tone | Example |
|---------|------|---------|
| Error / failure | Empathetic, calm, helpful | "We couldn't process your payment. Your card was not charged. Try a different payment method." |
| Success / completion | Brief, positive, forward-looking | "Project created. Invite your team to get started." |
| Onboarding / first use | Encouraging, clear, minimal | "Name your first project. You can change this anytime." |
| Empty state | Motivating, action-oriented | "No messages yet. Start a conversation to see them here." |
| Loading / waiting | Patient, informative | "Setting up your workspace. This usually takes about 30 seconds." |
| Destructive action | Serious, precise, consequence-aware | "This will permanently delete all project data. This cannot be undone." |
| Confirmation | Neutral, factual | "Your changes have been saved." |

**Anti-patterns**:
- Cheerful tone during errors ("Oops! Something went wrong! 😊") — dismissive of user frustration
- Formal tone during onboarding ("Please complete the required fields") — creates distance when you want engagement
- Casual tone for destructive actions ("Bye bye, data!") — trivializes serious consequences

## Section 4: Conciseness Rules

### The 50% Rule
Write the message. Then cut the word count by 50%. The second version is almost always better.

| Before (wordy) | After (concise) | Words cut |
|----------------|-----------------|-----------|
| "In order to continue, you will need to verify your email address" | "Verify your email to continue" | 8 → 6 |
| "There are currently no items in your shopping cart" | "Your cart is empty" | 10 → 4 |
| "You can use this feature to export your data" | "Export your data" | 10 → 4 |
| "Please note that this action cannot be undone" | "This cannot be undone" | 9 → 5 |

### Filler Words to Cut

| Word | Why | Exception |
|------|-----|-----------|
| just | Minimizes — "just click" implies the user is slow | None |
| simply | Same as "just" — implies it should be easy | None |
| very / really | Weak intensifiers — find a stronger word | None |
| basically | Vague hedge — say what you mean | None |
| actually | Usually adds nothing | Correcting a misconception |
| please | Unnecessary in UI (labels, buttons) | Error recovery, support context |
| in order to | Use "to" | None |
| a number of | Use the specific number | When the number is unknown |

### Formatting for Scanning
- One idea per sentence
- Front-load the important word (start with what matters)
- Use numerals (5, not "five") for faster scanning
- Bulleted lists over paragraphs for multiple items
- Bold the key term in instructional text

## Section 5: Accessibility in Copy

### Avoid Directional Language

| Bad | Good | Why |
|-----|------|-----|
| "Click the button on the left" | "Click Save" | Layout may differ on mobile, RTL, or screen readers |
| "See the red error below" | "See the error message for Email" | Color-blind users can't rely on red |
| "In the sidebar" | "In Settings" | Sidebar may be collapsed or absent |
| "The top menu" | "The main navigation" | Position varies by device |

### Don't Rely on Color Alone
If you reference an element by color ("the green checkmark"), also provide a non-color identifier ("the checkmark next to Status"). Color-blind users need an alternative signal.

### Screen Reader Considerations
- Links should describe their destination: "Read the privacy policy" not "Click here"
- Image alt text should describe function, not appearance: "Submit form" not "Blue button"
- Abbreviations should be expanded on first use: "PR (pull request)" then "PR" thereafter
- Icons should have `aria-label` if they are the only content of an interactive element

## Section 6: Terminology Consistency

### One Term, One Concept

Pick ONE term for each concept and use it everywhere in the product:

| Concept | Pick One | Not Both |
|---------|----------|----------|
| Authentication | "Sign in" | "Log in" |
| Removal | "Delete" | "Remove" |
| Creation | "Create" | "Add" / "New" |
| Navigation | "Go to" | "Navigate to" / "Visit" |
| Sending | "Send" | "Submit" / "Post" |

### Build a Glossary

Maintain a simple terminology glossary for the product:

| Term | Used For | Never Use |
|------|----------|-----------|
| Project | Top-level container | Workspace, Space, Organization |
| Member | Person in a project | User, Teammate, Collaborator |
| Task | Unit of work | Item, Ticket, Issue |

### Consistency Audit
- Search the codebase for synonyms of key terms
- Check button labels, headings, error messages, and tooltips
- When two terms exist, pick the more specific one and replace all instances of the other

## Section 7: Common Rewrites

Patterns that recur in almost every interface:

| Original | Rewrite | Principle |
|----------|---------|-----------|
| "Please enter your email address" | "Email" (as label) | Drop "please" in form labels — it adds length without value |
| "Click here to learn more" | "Learn about pricing" | Specific link text, not "click here" |
| "N/A" | "No data yet. Import records to see stats." | Explain what's missing and how to fix it |
| "Error 404" | "Page not found. Try searching or go back home." | Human language with a next step |
| "Are you sure you want to delete?" | "Delete project? This removes all data permanently." | State the consequence, not a vague question |
| "Loading..." | "Loading your dashboard..." | Be specific about what's loading |
| "No results found" | "No results for 'query'. Try a different search term." | Echo the search term, suggest an action |
| "Success!" | "Changes saved." | State what succeeded, not just that something did |
| "Welcome back!" | "Good morning, Alex." | Personalize when possible, skip generic greetings |
| "Untitled" | "New project — click to rename" | Guide the user instead of showing placeholder state |

## Output Structure

When providing UX writing guidance:

1. **Context assessment**: what the user is writing and where it appears in the interface
2. **Tone recommendation**: which emotional context applies and the appropriate voice
3. **Specific rewrites**: before/after versions of the copy with the principle behind each change
4. **Consistency check**: whether the terminology aligns with the rest of the product
5. **Accessibility review**: whether the copy works without visual context

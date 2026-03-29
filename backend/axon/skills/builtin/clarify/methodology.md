# Clarify Methodology

You are performing a systematic UX microcopy review to identify and fix unclear, ambiguous, or unhelpful text throughout an interface.

---

## Step 1: Inventory All Copy

Catalog every piece of user-facing text in the subject:
- Page/section headings
- Button labels and link text
- Form labels, placeholders, and help text
- Error messages and validation text
- Empty states and zero-data views
- Tooltips and contextual help
- Confirmation dialogs and destructive action warnings
- Success/completion messages
- Navigation labels and menu items
- Loading and progress text

---

## Step 2: Apply the 5 Golden Rules

Evaluate every piece of copy against these rules:

### Rule 1: Be Specific
- Bad: "Something went wrong" / Good: "Could not save — the file exceeds 10MB"
- Bad: "Invalid input" / Good: "Email must include @ and a domain (e.g., name@company.com)"
- Bad: "Error 403" / Good: "You do not have permission to edit this project"

### Rule 2: Be Concise
- Cut filler words: "In order to" → "To", "Please be aware that" → (delete)
- One idea per sentence. If it needs a comma splice, split it.
- Labels: 1-3 words. Descriptions: 1 sentence. Errors: 2 sentences max.

### Rule 3: Use Active Voice
- Bad: "Your password has been changed" / Good: "Password changed"
- Bad: "The file will be deleted" / Good: "This deletes the file permanently"
- Bad: "An error was encountered" / Good: "We could not connect to the server"

### Rule 4: Sound Human
- Avoid robotic language: "Operation completed successfully" → "Done"
- Match the product's personality. Formal products can still be warm.
- Do not over-apologize: "Sorry, something went wrong" → "Could not save. Try again."
- Avoid blame: "You entered an invalid date" → "Enter a date in MM/DD/YYYY format"

### Rule 5: Be Helpful
- Every error tells the user what to do next
- Empty states explain value and provide an action
- Confirmations restate what will happen, not just "Are you sure?"
- Loading states set expectations ("Loading 24 projects..." not just a spinner)

---

## Step 3: Pattern-Specific Review

### Button Labels
Replace generic labels with verb + object:

| Instead of    | Use                  |
|---------------|----------------------|
| Submit        | Save changes         |
| OK            | Confirm deletion     |
| Yes / No      | Delete / Keep        |
| Cancel        | Discard changes      |
| Click here    | View report          |
| Send          | Send invitation      |

Buttons should complete the sentence: "I want to ___."

### Error Messages
Every error must answer three questions:
1. **What happened?** — "Could not save the document"
2. **Why?** — "The server is temporarily unavailable"
3. **What now?** — "Try again in a few minutes, or download a local copy"

### Empty States
Empty states are onboarding moments, not dead ends:
- Bad: "No items found"
- Good: "No projects yet. Create your first project to get started."
- Include: an explanation of what will appear here, a primary action to populate it, and optionally a benefit statement.

### Form Labels and Help Text
- Labels: noun or short noun phrase ("Email address", not "Enter your email address here")
- Placeholders: example format, not instruction ("name@company.com", not "Enter email")
- Help text: only when the label is not self-explanatory. Keep to one line.

### Confirmation Dialogs
- Title: action being confirmed ("Delete this project?")
- Body: consequence ("This removes all files and cannot be undone.")
- Primary button: specific action ("Delete project")
- Secondary button: safe exit ("Keep project")

### Tooltips
- Max 1-2 sentences
- Explain what the element does, not what it is
- Only add tooltips when the UI element is not self-explanatory

---

## Step 4: Tone Consistency Audit

Assess overall tone across the interface:
- Is the tone consistent between different sections?
- Does the tone match the product personality?
- Are error states more formal/cold than success states? (Common mismatch)
- Is there jargon that assumes technical knowledge the audience may not have?

Rate tone consistency:
- **Consistent**: Same voice throughout, appropriate to audience
- **Mostly consistent**: Minor mismatches in 1-2 areas
- **Inconsistent**: Different voices across sections, noticeable shifts

---

## Step 5: Common Anti-Patterns Checklist

Flag any instances of:
- [ ] Jargon or technical terms without explanation
- [ ] Passive voice where active would be clearer
- [ ] Double negatives ("not unlike", "do not disable")
- [ ] Ambiguous pronouns ("it", "this", "that" without clear referent)
- [ ] Redundant text (label repeats placeholder, heading repeats intro)
- [ ] ALL CAPS for emphasis (use bold or hierarchy instead)
- [ ] Exclamation marks in errors or warnings
- [ ] Latin abbreviations (e.g., i.e., etc. — write them out)
- [ ] "Please" overuse (once per flow is enough)

---

## Output Structure

1. **Copy Inventory**: Summary of all text elements reviewed, grouped by type.
2. **Issues Found**: Each issue with location, current text, problem type (jargon/ambiguity/passive/missing context/tone mismatch), and severity.
3. **Rewrites**: Before/after for every issue, with brief rationale for the change.
4. **Tone Assessment**: Overall tone consistency rating with specific examples of mismatches.
5. **Anti-Pattern Flags**: Any checked items from the anti-patterns checklist with locations.
6. **Style Guide Notes**: 2-3 recommended guidelines to prevent future issues (e.g., "Always use verb+object for buttons").

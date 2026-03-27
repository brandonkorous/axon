# Technical Writing Methodology

## 1. Identify Your Audience

Before writing a single line, answer these questions:

- **Who will read this?** Developer, PM, executive, ops engineer, end-user?
- **What do they already know?** Assume the minimum shared context and build from there.
- **What do they need to DO after reading?** Every document should enable action.

Tailor vocabulary, depth, and examples to the audience. A runbook for on-call engineers is not the same as an RFC for architects.

## 2. Choose the Right Format

Match the format to the purpose:

| Format   | When to use                                      |
|----------|--------------------------------------------------|
| Spec     | Defining behavior, contracts, or interfaces      |
| RFC      | Proposing a change that needs review/approval     |
| Guide    | Teaching someone how to use or integrate          |
| Runbook  | Step-by-step operational procedures               |
| ADR      | Recording an architectural decision and rationale |

If unsure, default to a guide structure — it serves the widest audience.

## 3. Structure With Clear Sections

Every technical document should follow a predictable skeleton:

1. **Title** — concise, descriptive, searchable.
2. **Context / Motivation** — WHY this document exists. Lead with the problem.
3. **Overview** — a one-paragraph summary of what follows.
4. **Body sections** — the core content, organized logically (not chronologically).
5. **Examples** — concrete, runnable where possible.
6. **Glossary / Definitions** — define every term on first use.
7. **References / Links** — point to related docs, source code, tickets.

## 4. Lead With Context and Motivation

The first section answers: "Why should I care?" and "What problem does this solve?"

- State the current situation (what exists, what is broken, what is missing).
- State the desired outcome.
- Keep it to 3-5 sentences. If you need more, the scope is too large — split the doc.

## 5. Write With Precision

Follow these rules strictly:

- **Be concrete.** "The service responds within 200ms at p99" beats "The service is fast."
- **Use active voice.** "The scheduler assigns tasks" not "Tasks are assigned by the scheduler."
- **One idea per paragraph.** If a paragraph covers two concepts, split it.
- **Avoid weasel words.** Remove "basically", "simply", "just", "obviously."
- **Show, don't tell.** Include code snippets, CLI examples, diagrams, or sample payloads.

## 6. Define Terms on First Use

The first time you use a domain-specific term, acronym, or internal name:

- Spell it out: "The Agent Routing Layer (ARL) handles..."
- If the document has more than five such terms, add a glossary section at the end.

## 7. Include Actionable Examples

Every non-trivial concept needs at least one example. Good examples are:

- **Minimal** — show only what is needed to illustrate the point.
- **Correct** — never include example code that would not compile or run.
- **Annotated** — add inline comments or follow-up explanation.

## 8. Quality Checklist Before Finishing

Before delivering, verify:

- [ ] Can someone unfamiliar with the codebase follow this without asking questions?
- [ ] Are all acronyms defined?
- [ ] Are there concrete examples for every key concept?
- [ ] Does every section earn its place? Remove anything that does not serve the reader.
- [ ] Is the document scannable? Use headers, bullets, and tables — not walls of prose.

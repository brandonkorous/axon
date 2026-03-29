# Seeing the System

Seeing the system means understanding a design not just in its happy-path state but across three critical lenses: before (empty states, onboarding, first impressions), after (confirmation, follow-up, what happens next), and when things break (errors, edge cases, degraded states). Most design effort focuses on the steady-state middle, but users spend significant time in these peripheral states, and that is where trust is built or lost.

Apply this when reviewing any feature design, during QA, or when users report confusion that does not show up in the happy-path prototype.

**Steps to apply:**
1. **Before** — What does the user see when there is no data? What is the first-time experience? How do they get started?
2. **After** — What confirmation do they receive? What is the next logical step? How do they return?
3. **When things break** — What happens on errors, timeouts, invalid input, or permission issues? Is the failure graceful and recoverable?
4. Design each of these states with the same care as the primary flow.

**Common mistakes:** Designing only for the populated, working, happy-path state. Treating error states as developer concerns rather than design opportunities. Ignoring empty states, which are often the very first thing a new user sees.

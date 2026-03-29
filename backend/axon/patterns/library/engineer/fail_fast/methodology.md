# Fail Fast

Fail fast means that when something goes wrong, the system should report the error immediately and clearly at the point where it occurred, rather than continuing with bad data and failing unpredictably later. A null pointer caught at input validation is trivial to debug. The same null pointer discovered three layers deep in a calculation is a nightmare. Early, loud failure is a gift to the developer.

Apply this when writing input validation, designing API contracts, or anywhere bad data could silently propagate. It is especially critical in systems where silent corruption is worse than a visible crash.

**Steps to apply:**
1. Validate inputs at the boundary — function entry, API endpoints, config loading, deserialization.
2. Use assertions and guard clauses for invariants that must always hold.
3. Throw specific, descriptive errors — include what was expected, what was received, and where.
4. Prefer crashing over returning default values when the default would mask a bug.

**Common mistakes:** Swallowing exceptions with empty catch blocks. Returning null or default values instead of throwing when the input is invalid. Deferring validation to "later" where the context for a good error message is lost. Confusing fail-fast with fragile — fail fast is about detection, not about lacking resilience.

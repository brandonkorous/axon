# Debugging Methodology

You are performing structured root cause analysis. Do not guess-and-fix. Follow this systematic approach to find the actual cause, verify it, and prevent recurrence.

## Phase 1: Symptom Characterization

Before forming any hypothesis, understand what is actually happening:

- **Exact error**: Copy the precise error message, stack trace, or unexpected output. Paraphrasing errors loses critical detail.
- **Expected behavior**: What should happen instead? Be specific.
- **Reproduction conditions**: When does it happen? Every time, intermittently, or only under specific conditions?
- **Scope**: Is this affecting all users, one user, one environment? What is the blast radius?
- **Timeline**: When did it start? What changed around that time? Recent deployments, config changes, dependency updates, data migrations?

Write these down before proceeding. Skipping characterization leads to fixing symptoms instead of causes.

## Phase 2: Reproduce

A bug you cannot reproduce is a bug you cannot verify is fixed.

1. **Isolate the minimal reproduction case**: Strip away everything that is not necessary to trigger the bug. Fewer variables means faster debugging.
2. **Confirm the reproduction**: Run it twice. Flaky reproduction means you have not isolated the trigger.
3. **Identify what makes it work vs. fail**: Change one variable at a time. What is different between the working case and the failing case?

If you cannot reproduce:
- Check if it is environment-specific (OS, runtime version, configuration).
- Check if it is data-dependent (specific input values, database state).
- Check if it is timing-dependent (race condition, timeout, caching).
- Add logging at key points and wait for the next occurrence.

## Phase 3: Hypothesize

Generate a ranked list of possible causes. Do not commit to one theory prematurely.

For each hypothesis:
- **Cause**: What specifically could produce this symptom?
- **Likelihood**: High / Medium / Low, based on the evidence so far.
- **Test**: What single action would confirm or eliminate this hypothesis?

Rank by likelihood. Investigate the most likely cause first, but do not ignore low-probability hypotheses if the high-probability ones are eliminated.

Common cause categories to consider:
- **Recent changes**: New code, config changes, dependency updates.
- **Input/data issues**: Unexpected values, encoding, missing fields, corrupt data.
- **State issues**: Stale cache, race condition, leaked connections, exhausted resources.
- **Environment issues**: Versions, permissions, network, disk space, env vars.
- **Integration issues**: API contract changes, schema drift, timeout mismatches.

## Phase 4: Test Hypotheses

Use binary search to narrow down the cause efficiently:

1. **Divide the problem space in half**: If you suspect a code change, use git bisect. If you suspect a data issue, test with a known-good input vs. the failing input.
2. **Change one thing at a time**: Multiple changes simultaneously make it impossible to attribute cause.
3. **Add targeted logging**: Insert log statements that will confirm or deny a specific hypothesis. Do not add logging everywhere — that creates noise.
4. **Check assumptions**: Verify that what you think is true actually is. Print the variable you assume has a value. Check the config you assume is set. Query the state you assume exists.

For each test:
- State what you expect to observe if the hypothesis is correct.
- State what you expect to observe if it is wrong.
- Run the test and record the actual result.

Eliminate hypotheses explicitly. Do not just move on — cross them off with evidence.

## Phase 5: Verify the Fix

Finding the cause is not the same as fixing the bug:

1. **Implement the minimal fix**: Fix the root cause, not the symptom. A try/catch that swallows the error is not a fix.
2. **Confirm the reproduction case now passes**: Run the exact reproduction from Phase 2.
3. **Check for regressions**: Does the fix break anything else? Run the relevant test suite.
4. **Test edge cases**: Does the fix handle related edge cases, or did it only fix the specific reported instance?

If the fix is a workaround rather than a root cause fix, document it as such and create a follow-up to address the real cause.

## Phase 6: Document

Every non-trivial bug is a learning opportunity. Record:

- **Root cause**: One sentence explaining why this happened.
- **Contributing factors**: What made this bug possible? Missing tests, unclear API, implicit assumptions?
- **Fix applied**: What changed and why.
- **Prevention**: How to prevent this class of bug — new tests, better validation, type safety, monitoring, documentation.
- **Detection**: If this happens again, how will we know sooner? Alerting, logging, health checks.

## Debugging Principles

- **Do not guess**: Hypothesize, test, confirm. Guessing leads to patching symptoms while the root cause persists.
- **Trust the evidence, not your assumptions**: The code does what it does, not what you think it does. Read it again.
- **Simplify before you investigate**: Remove complexity until the bug disappears, then add it back to find which piece causes it.
- **Check the obvious first**: Is it plugged in? Is the service running? Is the config pointing to the right environment?
- **Rubber duck it**: Explain the problem out loud, step by step. You will often find the gap in your reasoning mid-sentence.

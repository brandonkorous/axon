# Two-Week Smell Test

If a competent engineer cannot ship a meaningful piece of work in two weeks, something is wrong — and it is usually not the engineer. The problem is almost always that the work has not been decomposed properly, the system is too hard to change safely, or onboarding into that area of the codebase is too costly. Two weeks is a forcing function that exposes these structural problems.

Apply this pattern during planning and estimation. When a task is estimated at more than two weeks, do not simply accept the timeline. Investigate why. The answer reveals important truths about your system's health.

**Steps:** (1) Take the proposed task and ask: "Why can't this ship in two weeks?" (2) If the answer is scope, break it into smaller shippable increments. (3) If the answer is system complexity, that is technical debt worth addressing. (4) If the answer is lack of context, that is an onboarding and documentation problem. (5) Address the root cause, do not just extend the timeline.

The most common mistake is treating the two-week target as a deadline rather than a diagnostic tool. The point is not to rush — it is to reveal what is slowing you down.

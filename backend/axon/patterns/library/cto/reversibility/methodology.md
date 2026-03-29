# Reversibility

Reversibility is the practice of designing every change so it can be undone quickly and safely. Feature flags, A/B tests, incremental rollouts, and backward-compatible migrations are all tools that keep the undo button available. The goal is to make deploying code a non-event — something you can do and undo many times a day without drama.

Apply this pattern to every change that reaches production. The more users affected, the more important reversibility becomes. If you cannot describe how to roll back a change in one sentence, the change is not ready to ship.

**Steps:** (1) Before writing code, define the rollback plan. (2) Use feature flags to decouple deployment from activation. (3) Roll out incrementally — 1% of traffic, then 10%, then 50%, then 100%. (4) Monitor key metrics at each stage before expanding. (5) Keep the old code path alive until the new path is proven. (6) Only remove the old path after the new path has been stable for a full cycle.

The most common mistake is treating feature flags as permanent — they accumulate into a tangled mess if not cleaned up. The second mistake is making database schema changes that cannot be rolled back without data loss.

# Blast Radius

Blast radius is the total scope of damage when something goes wrong. Every change to a system — a deploy, a migration, a configuration update — has a potential blast radius. The goal is not to avoid all risk but to ensure that when failures happen, they are contained to the smallest possible area.

Apply this pattern before any deployment, migration, or architectural change. Ask: "If this goes wrong, what breaks? How many users are affected? Can we recover without data loss?" The answer determines how much caution, testing, and rollback planning the change deserves.

**Steps:** (1) Identify all systems and users affected by the change. (2) Map the dependency chain — what calls what. (3) Define the worst-case failure scenario. (4) Design containment boundaries — feature flags, canary deploys, circuit breakers, database backups. (5) Ensure rollback is possible and tested. (6) Size the rollout inversely to the blast radius.

The most common mistake is assuming a "small change" has a small blast radius. Shared libraries, database migrations, and authentication changes often have enormous blast radii despite being few lines of code.

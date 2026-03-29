# Conway's Law

Organizations design systems that mirror their own communication structure. If three teams build a compiler, you get a three-pass compiler. This is not a suggestion — it is a near-physical law of software development. The boundaries between teams become the interfaces between modules, whether you planned it that way or not.

Apply this pattern when you notice architectural boundaries that do not make technical sense, or when a reorg is being planned without considering its effect on the codebase. Use it proactively by structuring teams around the architecture you want, not the other way around. This is sometimes called the "inverse Conway maneuver."

**Steps:** (1) Map your current team boundaries. (2) Map your current system boundaries. (3) Identify where they align and where they conflict. (4) When conflicts exist, decide whether to change the teams or change the architecture — fighting both simultaneously always fails. (5) Ensure each team owns a coherent slice of the system with clear API contracts at the boundaries.

The most common mistake is ignoring Conway's Law and hoping good architecture will survive misaligned teams. The second mistake is reorganizing teams without giving the codebase time to follow.

# Debug by Bisection

Debug by bisection applies binary search to debugging. Instead of reading code line by line or guessing at the cause, you divide the problem space in half, test which half contains the bug, and repeat. This converts an O(n) search into O(log n). Whether you are searching through commits (git bisect), code paths, configuration changes, or data records, the principle is the same: halve and conquer.

Apply this when a bug exists but the cause is unclear, when a regression appeared between two known states, or when a system has too many moving parts to inspect one by one.

**Steps to apply:**
1. Define two known states — one where it works and one where it does not.
2. Find the midpoint between those states (a commit, a code section, a config change).
3. Test at the midpoint. Determine which half contains the problem.
4. Repeat on the failing half until you isolate the exact change or line.
5. For git regressions, use `git bisect` to automate this process.

**Common mistakes:** Starting with a hypothesis and hunting for confirmation instead of systematically narrowing down. Skipping the bisection and reading all code linearly. Not automating the test — each bisection step should be a quick, repeatable check. Bisecting on the wrong axis (searching commits when the issue is data-dependent).

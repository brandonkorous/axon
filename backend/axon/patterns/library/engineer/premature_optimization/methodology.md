# Premature Optimization

Knuth's famous observation states that premature optimization is the root of all evil. Engineers instinctively optimize code they think will be slow, but intuition about performance bottlenecks is wrong more often than right. Optimized code is typically harder to read, harder to change, and harder to debug. The cost of optimization is complexity, and you should only pay that cost when measurement proves it is necessary.

Apply this whenever you feel the urge to optimize during initial development, or when a teammate proposes a complex solution for performance reasons without profiling data.

**Steps to apply:**
1. Write the simplest, clearest implementation first.
2. Measure actual performance under realistic conditions.
3. Profile to identify the real bottleneck — it is almost never where you guessed.
4. Optimize only the measured bottleneck, and only enough to meet the requirement.
5. Document why the optimization exists so future developers do not simplify it away.

**Common mistakes:** Optimizing based on gut feeling instead of profiling. Optimizing code that runs once during startup as if it were a hot loop. Making the codebase permanently harder to maintain for a performance gain nobody notices.

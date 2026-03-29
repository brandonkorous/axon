# Essential vs Accidental Complexity

Essential complexity is inherent to the problem you are solving — tax law is complex, scheduling is complex, distributed consensus is complex. No amount of engineering can remove it. Accidental complexity is everything you add on top through your own choices — convoluted build systems, unnecessary abstractions, poor data models, or overengineered frameworks.

Apply this pattern when a system feels harder than it should. When engineers complain about velocity, ask: "Is this hard because the domain is hard, or because we made it hard?" Most struggling codebases suffer from accidental complexity masquerading as essential complexity.

**Steps:** (1) Identify the core problem the system solves. (2) List the sources of complexity engineers encounter daily. (3) For each source, ask whether it would exist in any correct solution or only exists because of your implementation choices. (4) Prioritize removing accidental complexity ruthlessly — simpler data models, fewer abstractions, less indirection. (5) Accept and manage essential complexity with clear documentation and domain expertise.

The most common mistake is assuming all complexity is essential because it has been there a long time. The second mistake is trying to eliminate essential complexity through abstraction, which merely hides it and creates new accidental complexity.

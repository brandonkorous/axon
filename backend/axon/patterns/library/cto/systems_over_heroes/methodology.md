# Systems Over Heroes

A healthy engineering organization does not depend on heroics. If your system requires a specific person to wake up at 3am and make the right judgment call under pressure, your system is broken. Reliability comes from designing for the worst case — a tired, stressed, on-call engineer who has never seen this failure before.

Apply this pattern when reviewing incident response, deployment processes, and operational runbooks. Every critical process should be executable by any trained team member, not just the person who built it. If knowledge is concentrated in one person, that is a single point of failure no different from a server with no redundancy.

**Steps:** (1) Identify processes that depend on specific individuals. (2) Document those processes as runbooks with explicit steps. (3) Automate what can be automated — rollbacks, failovers, alerts. (4) Ensure at least two people can perform every critical operation. (5) Test your runbooks by having someone unfamiliar execute them. (6) Design alerts and dashboards that make the correct action obvious.

The most common mistake is rewarding heroics instead of preventing the conditions that require them. The second mistake is writing runbooks that assume deep context the reader does not have.

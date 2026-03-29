# Technical Debt Quadrant

Not all technical debt is the same. Fowler's quadrant classifies debt along two axes: reckless vs prudent, and deliberate vs inadvertent. Reckless-deliberate is "we don't have time for design." Prudent-deliberate is "we know this will need refactoring, but shipping now is the right trade-off." Reckless-inadvertent is "what's layering?" Prudent-inadvertent is "now we know how we should have built it."

Apply this pattern when prioritizing technical debt repayment. Not all debt is equal — prudent-deliberate debt taken consciously with a plan to repay is healthy. Reckless debt of either kind is a sign of process failure that needs to be addressed at its root.

**Steps:** (1) Inventory your known technical debt. (2) Classify each item into one of the four quadrants. (3) Prioritize reckless-inadvertent debt first — it indicates a skills or process gap. (4) Schedule repayment of prudent-deliberate debt before its interest compounds. (5) Use the quadrant in retrospectives to ensure new debt is taken deliberately and prudently.

The most common mistake is treating all technical debt as equivalent and either ignoring it all or trying to repay it all at once. The second mistake is never taking deliberate debt — sometimes shipping fast with known trade-offs is the right call.

# Decision Analysis Methodology

## 1. Clarify the Decision

Before evaluating options, make sure the decision itself is well-defined:

- **State the decision as a question.** "Which database should we use for the event store?" is clearer than "database decision."
- **Define the scope.** What is in bounds? What has already been decided and is not up for debate?
- **Identify the decision maker.** Who has final authority? This affects how you frame the recommendation.
- **Determine reversibility.** Is this a one-way door (hard to undo) or a two-way door (easy to change later)? One-way doors deserve more analysis. Two-way doors deserve faster action.

## 2. Identify the Options

List all viable options explicitly. For each option, write a one-sentence description.

Guidelines:

- **Include at least three options.** If you only have two, you probably have not explored the space enough. Consider: "Do nothing" and "Do something completely different" as additional candidates.
- **Include the status quo.** "Keep doing what we are doing" is always an option and serves as the baseline.
- **Exclude non-starters.** If an option violates a hard constraint, note it and remove it from evaluation.

## 3. Define Criteria

Criteria are the dimensions you care about. Split them into two tiers:

### Must-Haves (Dealbreakers)
Hard requirements that an option must satisfy to be considered. These are binary — pass or fail. Any option that fails a must-have is eliminated.

Examples: "Must support PostgreSQL", "Must cost under $10k/month", "Must be SOC 2 compliant."

### Nice-to-Haves (Weighted Criteria)
Qualities that matter but are negotiable. Assign each a weight from 1 (minor preference) to 5 (critical factor).

Examples:
- Performance (weight: 4)
- Team familiarity (weight: 3)
- Community ecosystem (weight: 2)
- Migration effort (weight: 5)

Aim for 4-8 weighted criteria. Fewer than 4 means you are oversimplifying. More than 8 means you are overcomplicating.

## 4. Evaluate Each Option Against Criteria

### Must-Have Check
Run each option through the must-have filters first. Eliminate any that fail.

### Weighted Scoring
For each surviving option, score it 1-5 on every weighted criterion:

- 5 = Excellent fit, clear advantage
- 4 = Good fit, minor gaps
- 3 = Adequate, no strong opinion
- 2 = Weak fit, notable concerns
- 1 = Poor fit, significant drawback

Compute weighted scores: (score x weight) for each criterion, then sum across all criteria per option.

Present this as a table for easy comparison.

## 5. Identify Risks and Mitigations

For each top-scoring option, ask:

- **What could go wrong?** List the top 2-3 risks.
- **How likely is each risk?** Low / Medium / High.
- **What is the impact if it happens?** Low / Medium / High.
- **Can we mitigate it?** Describe the mitigation or state that none exists.
- **What would cause us to reverse this decision?** Define the tripwire that signals we chose wrong.

Do not ignore risks for the leading option. Confirmation bias is strongest for the choice you are already leaning toward.

## 6. Make a Recommendation

State the recommendation clearly and support it with an explicit reasoning chain:

1. **State the choice.** "I recommend Option B."
2. **Give the primary reason.** The single strongest argument.
3. **Give supporting reasons.** 2-3 additional factors.
4. **Acknowledge the trade-off.** What are you giving up by not choosing the runner-up?
5. **State the assumptions.** What must be true for this recommendation to hold?

The reasoning chain must be traceable: anyone reading it should be able to follow the logic from criteria to scores to recommendation without gaps.

## 7. Document for Future Reference

Every decision analysis should capture:

- **Decision date** and decision maker.
- **Options considered** (including those eliminated by must-haves).
- **Criteria and weights used.**
- **The final choice and why.**
- **Assumptions that, if invalidated, should trigger re-evaluation.**

This is not bureaucracy — it is insurance. When someone asks "why did we choose X?" six months from now, the answer is already written.

## Anti-Patterns to Avoid

- **Analysis paralysis**: If options score within 10% of each other, the decision is close enough that speed matters more than precision. Pick one and move.
- **Hidden criteria**: If you feel uneasy about the "winner" but cannot explain why, there is an unstated criterion. Surface it and add it to the evaluation.
- **Sunk cost weighting**: Do not score an option higher because you already invested in it. Evaluate based on future value only.
- **Anchoring on the first option**: The option presented first often gets an unfair advantage. Randomize presentation order if possible.

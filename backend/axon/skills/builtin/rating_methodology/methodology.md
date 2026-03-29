# Rating Methodology (0-10 Rate-Fix-Rerate)

You are performing a structured evaluation using the Rate-Fix-Rerate methodology. This is a disciplined framework for assessing quality across multiple dimensions, identifying what excellence looks like, and iterating toward it.

## Step 1: Identify Dimensions

Choose 4-7 evaluation dimensions appropriate to the subject. Each dimension must be:
- **Observable** — you can point to specific evidence
- **Independent** — improving one doesn't automatically improve another
- **Relevant** — it matters for the subject's purpose

If the user provided dimensions, use those. Otherwise, identify them based on the subject type:

| Subject Type | Suggested Dimensions |
|-------------|---------------------|
| Code/Architecture | Correctness, Readability, Performance, Security, Maintainability, Test Coverage |
| UI/Design | Visual Hierarchy, Consistency, Accessibility, Information Density, Responsiveness, Delight |
| Strategy/Plan | Clarity, Feasibility, Completeness, Risk Awareness, Alignment, Measurability |
| Writing/Content | Clarity, Accuracy, Structure, Audience Fit, Conciseness, Actionability |
| Product | User Value, Simplicity, Differentiation, Scalability, Time-to-Value |

## Step 2: Initial Rating

For each dimension, assign a score from 0-10 with a specific justification:

| Score | Meaning |
|-------|---------|
| 0-2 | Fundamentally broken. Needs complete rework. |
| 3-4 | Significant problems. Major effort required. |
| 5-6 | Functional but mediocre. Noticeable gaps. |
| 7-8 | Good. Minor issues. Meets expectations. |
| 9 | Excellent. Exceeds expectations. Small polish items only. |
| 10 | Exceptional. Best-in-class for this context. |

**Rules for honest rating:**
- A score of 7 is not "average" — it means genuinely good. Most things start at 4-6.
- Never give a 10 on initial rating. If you think it's a 10, you haven't looked hard enough.
- Every score must cite specific evidence. "Looks good" is not a justification.

Format:
```
### [Dimension Name]: [Score]/10
**Evidence:** [What you observed]
**Gap:** [What's missing or weak]
```

## Step 3: Define the 10

For each dimension, describe what a 10 would look like **for this specific subject**. Not abstract perfection — concrete, achievable excellence given the context.

This is the most important step. A vague "10" ("it would be really good") is worthless. A specific "10" ("the error messages would include the exact field name, the constraint violated, and a suggested fix") is actionable.

Format:
```
### [Dimension Name]: What 10 Looks Like
[2-3 sentences describing concrete excellence for THIS subject]
```

## Step 4: Propose Improvements

For each dimension scoring below the target (default 8), propose specific changes that would raise the score. Each improvement must:
- Be **actionable** — not "make it better" but "extract the validation logic into a shared module"
- Have an **expected impact** — "+1" or "+2" on the dimension score
- Be **proportional** — the effort should match the score improvement

Prioritize improvements by:
1. Highest impact per effort
2. Dimensions furthest from target
3. Improvements that lift multiple dimensions

## Step 5: Re-Rate

After proposing improvements, re-rate each dimension assuming the improvements are applied:

| Dimension | Initial | After Improvements | Delta |
|-----------|---------|-------------------|-------|
| [name] | [N]/10 | [M]/10 | +[D] |

If any dimension is still below target after improvements, either:
- Propose additional improvements, or
- Flag it as a known limitation with a reason ("achieving 8+ on performance requires infrastructure changes outside this scope")

## Step 6: Synthesize

Produce a summary:
1. **Overall score** — weighted average (weight dimensions by importance to the subject's purpose)
2. **Strongest dimension** — what's working well and why
3. **Weakest dimension** — the biggest opportunity for improvement
4. **Top 3 actions** — the three most impactful improvements, in priority order
5. **Verdict** — one sentence: is this ready, needs work, or needs rethinking?

## Rules

- Be honest. Generous ratings help nobody. The value is in the gaps.
- Be specific. Every claim must point to evidence.
- A re-rated score can never be lower than the initial score (improvements don't make things worse).
- If the user asks to iterate, repeat Steps 4-6 with the re-rated scores as the new baseline.
- Don't rate dimensions you can't observe. If you need more information to rate a dimension, say so.

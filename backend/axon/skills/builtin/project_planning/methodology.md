# Project Planning Methodology

You are creating a structured project plan. Follow this decomposition framework to produce a plan that a team can actually execute against.

## Phase 1: Objective Clarification

Do not plan until the goal is sharp:

- **Outcome statement**: Write a single sentence describing what "done" looks like. Use measurable terms where possible.
- **Success criteria**: List 2-5 specific, observable conditions that must be true when the project is complete.
- **Non-goals**: Explicitly state what this project will NOT do. This prevents scope creep during execution.
- **Stakeholders**: Who cares about this project? Who approves it? Who is blocked by it?

If the objective is vague, push back and ask clarifying questions before proceeding.

## Phase 2: Constraint Identification

Map the boundaries of the solution space:

- **Time**: Hard deadlines, soft targets, external dependencies with dates.
- **Resources**: Team size, skill availability, budget, infrastructure.
- **Technical**: Platform constraints, compatibility requirements, performance thresholds.
- **Organizational**: Approval processes, compliance requirements, cross-team dependencies.

For each constraint, note whether it is **hard** (non-negotiable) or **soft** (preferred but flexible). This distinction matters when trade-offs arise later.

## Phase 3: Work Breakdown

Decompose the objective into workstreams, then tasks:

1. **Identify workstreams**: 3-7 parallel tracks of related work. Each workstream should be ownable by one person or small team.
2. **Decompose into tasks**: Each workstream breaks into concrete tasks. A good task is:
   - Completable in 1-5 days by one person
   - Has a clear definition of done
   - Produces a verifiable output
3. **Tag each task** with: estimated effort (hours or days), required skills, and priority (P0 critical path / P1 important / P2 nice-to-have).

If a task is larger than 5 days, it is not a task — decompose it further.

## Phase 4: Dependency Mapping

Dependencies are where plans die. Map them explicitly:

1. **Internal dependencies**: Which tasks block which other tasks? Draw the directed graph.
2. **External dependencies**: APIs, approvals, deliverables from other teams, vendor timelines.
3. **Critical path**: Identify the longest chain of dependent tasks. This is your minimum project duration regardless of team size.
4. **Parallelization opportunities**: Which workstreams can run simultaneously? Where can you add people to compress the timeline?

Present dependencies as a list of "X blocks Y" relationships. Flag any task that has 3+ dependencies — it is a coordination bottleneck and a risk.

## Phase 5: Milestone Definition

Milestones are checkpoints, not tasks. Define 3-6 milestones:

- **What**: A clear deliverable or state (not "50% complete" — that is meaningless).
- **When**: Target date based on dependency graph and effort estimates.
- **Verification**: How do you confirm this milestone is actually reached?
- **Go/no-go criteria**: What must be true to proceed past this milestone?

Space milestones so that no gap exceeds 2-3 weeks. Long gaps without checkpoints hide schedule slippage.

## Phase 6: Risk Analysis

For each identified risk:

| Field        | Description                                              |
|--------------|----------------------------------------------------------|
| Risk         | What could go wrong?                                     |
| Likelihood   | High / Medium / Low                                      |
| Impact       | High / Medium / Low                                      |
| Trigger      | How will you know this risk is materializing?            |
| Mitigation   | What can you do now to reduce likelihood or impact?      |
| Contingency  | What will you do if it happens despite mitigation?       |

Focus on the top 3-5 risks. Every project has risks — a plan that lists none is a plan that has not been thought through.

## Output Structure

Deliver the plan in this format:

1. **Objective and success criteria**
2. **Constraints summary**
3. **Workstream overview** (table: workstream, owner, estimated duration, priority)
4. **Detailed task breakdown** (grouped by workstream, with effort and dependencies)
5. **Milestone timeline** (table or visual timeline)
6. **Risk register** (table format from Phase 6)
7. **Open questions** — anything that must be resolved before execution begins

## Quality Checklist

- [ ] Objective is specific and measurable
- [ ] Every task has a clear definition of done
- [ ] No task exceeds 5 days of estimated effort
- [ ] Critical path is identified and its duration stated
- [ ] External dependencies have owners and expected dates
- [ ] At least 3 risks are identified with mitigations
- [ ] Milestones are spaced no more than 2-3 weeks apart

# Completeness Analysis Methodology

You are performing a structured completeness analysis. The core insight: AI has fundamentally changed the effort calculus for thoroughness. The "last 10%" that teams historically skip now costs minutes, not days. Your job is to make this concrete.

## Step 1: Decompose the Work

Break the task into discrete work items. For each item, classify it:

| Type | Description | Examples |
|------|-------------|---------|
| **Boilerplate** | Repetitive, pattern-based work | Config files, CRUD endpoints, test scaffolding, documentation templates |
| **Mechanical** | Rule-following work with clear specs | Data migration, API wrapper, format conversion, schema validation |
| **Creative** | Requires judgment, taste, or domain insight | Architecture decisions, UX flows, naming conventions, error messages |
| **Research** | Requires investigation or learning | Library evaluation, performance profiling, competitive analysis |

## Step 2: Estimate Effort

For each work item, estimate three effort levels:

| Item | Human-Only | AI-Assisted | AI-Automated | Compression |
|------|-----------|-------------|--------------|-------------|
| [item] | [hours] | [hours] | [hours or N/A] | [ratio]x |

**Estimation rules:**
- **Human-Only**: How long would a competent developer take without AI tools?
- **AI-Assisted**: Human + AI pair programming (Claude, Copilot). Human drives, AI accelerates.
- **AI-Automated**: AI does the work, human reviews. Only applicable for Boilerplate and some Mechanical tasks.
- **Compression**: Human-Only / AI-Assisted ratio

Typical compression ratios by type:
- Boilerplate: 50-100x (minutes vs. days)
- Mechanical: 20-50x
- Creative: 3-10x (AI helps explore, human decides)
- Research: 5-20x (AI synthesizes faster, but judgment still needed)

## Step 3: Define Completeness Levels

Define three levels of completeness for the overall task:

### Minimal (Ship the core)
- Only the explicitly requested items
- Happy path only, no edge cases
- No tests beyond basic smoke tests
- No documentation updates

### Standard (Professional quality)
- All requested items plus obvious dependencies
- Common edge cases handled
- Meaningful test coverage
- Documentation for public interfaces

### Comprehensive (Best-in-class)
- Everything in Standard
- Full edge case handling
- Performance optimization
- Comprehensive tests including error scenarios
- Updated documentation, changelogs, migration guides
- Accessibility, i18n considerations

## Step 4: Calculate the Delta

The key question: **What does the jump from Minimal to Comprehensive cost?**

| Level | Human-Only Total | AI-Assisted Total | Delta from Minimal |
|-------|-----------------|-------------------|-------------------|
| Minimal | [hours] | [hours] | — |
| Standard | [hours] | [hours] | +[hours] |
| Comprehensive | [hours] | [hours] | +[hours] |

Highlight the AI-assisted delta. If going from Minimal to Comprehensive costs 2 extra hours with AI but would have cost 2 extra days without it, that changes the decision.

## Step 5: Recommend

Based on the effort analysis:

1. **If Comprehensive AI-assisted effort < Minimal Human-only effort**: Always do Comprehensive. There's no excuse not to.
2. **If Standard is significantly cheaper than Comprehensive**: Recommend Standard unless the task is high-stakes or customer-facing.
3. **If even Minimal is expensive with AI**: Flag it — this task may need a different approach entirely.

State your recommendation clearly:
- Which level to target
- What the total AI-assisted effort would be
- What would be skipped (and the risk of skipping it)
- The one item from Comprehensive that's worth adding even to a Minimal approach

## Rules

- Be honest about estimates. Rounding to nice numbers is fine; being off by 5x is not.
- AI compression doesn't apply equally to everything. Creative work compresses less. Say so.
- "It depends" is not an estimate. Give a range if uncertain.
- Include review time. AI-generated code still needs human review.
- The goal is not to always choose Comprehensive — it's to make an informed choice with real numbers instead of gut feelings.

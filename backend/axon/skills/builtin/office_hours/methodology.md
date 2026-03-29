# Office Hours Methodology

You are performing a YC-style product validation session, stress-testing product assumptions through six forcing questions before any code is written.

## Step 1: Mode Selection

Determine the validation mode based on input or context:

- **Startup mode**: Full rigor. All forcing questions apply. Includes market sizing, fundraising readiness, competitive moat analysis. Appropriate for founders building a business.
- **Builder mode**: Lighter touch. Skip fundraising and market sizing. Focus on user need, specificity, and fit. Appropriate for side projects, hackathons, internal tools, and open-source.

If mode is not specified, infer from context. A solo developer building a tool = builder mode. A team with a pitch deck = startup mode.

## Step 2: Stage Detection

Determine the product stage and route to appropriate questions:

| Stage | Description | Primary Questions |
|-------|-------------|-------------------|
| Pre-product | Idea or concept, no users yet | Q1 (Demand Reality), Q2 (Status Quo), Q3 (Desperate Specificity) |
| Has-users | Product exists, people use it | Q2 (Status Quo), Q4 (Narrowest Wedge), Q5 (Observation & Surprise) |
| Has-revenue | People pay for it | Q4 (Narrowest Wedge), Q5 (Observation & Surprise), Q6 (Future-Fit) |

If stage is not specified, ask clarifying questions or infer from the product description. All six questions may be addressed regardless of stage, but the primary questions receive deeper analysis.

## Step 3: Forcing Question Analysis

### Q1 — Demand Reality

**Core question**: What evidence exists that someone actually needs this?

Not "would they use it" but "are they actively suffering without it?" Evaluate:

- **Search evidence**: Are people googling for solutions to this problem?
- **Forum evidence**: Are people complaining about this pain in communities, Reddit, Twitter, Stack Overflow?
- **Spend evidence**: Are people already paying for inferior alternatives?
- **Workaround evidence**: Are people building hacky solutions themselves?
- **Frequency evidence**: How often does this pain occur — daily, weekly, yearly?

Score the demand signal:

| Score | Level | Description |
|-------|-------|-------------|
| 0 | No signal | No evidence anyone needs this. Founder intuition only. |
| 1 | Weak signal | A few forum posts or anecdotal mentions. Could be noise. |
| 2 | Moderate signal | Clear complaints in multiple channels. People describe the pain. |
| 3 | Strong signal | Active workarounds exist. People spend time/money on alternatives. |
| 4 | Hair-on-fire | People are desperately cobbling solutions. Money is being thrown at the problem. |

### Q2 — Status Quo

**Core question**: What is the current workaround, and what does it cost?

Map the existing solution landscape:

1. **Direct competitors** — products that solve this exact problem
2. **Adjacent tools** — products people misuse to approximate a solution
3. **Manual workarounds** — spreadsheets, sticky notes, email chains, hiring someone
4. **Ignoring it** — people who just live with the pain

For each alternative, document:
- Time cost (hours per week/month)
- Money cost (subscription, headcount, opportunity cost)
- Frustration cost (error rate, learning curve, reliability)
- Switching cost (what it takes to move away from current solution)

**Red flag**: If the status quo is "nothing — nobody does this today," the demand signal is likely weak unless you can explain why the timing is now right.

### Q3 — Desperate Specificity

**Core question**: Name the actual person who needs this most.

Vague personas kill products. Get specific:

- **Job title**: Not "developers" — what kind? Backend? Frontend? DevOps? At what company size?
- **Daily frustration**: What specific moment in their day triggers the pain?
- **Failed alternatives**: What have they already tried and abandoned? Why did each fail?
- **Willingness to act**: Would they take a meeting about this? Sign up for a beta? Pay today?
- **Access**: Can you actually reach this person? Do you have a channel to them?

**Startup mode addition**: How many of this exact person exist? Is the market 500 people or 500,000?

**Builder mode adjustment**: "Name the person" can be yourself. Side projects solving your own pain are valid — but be honest about whether others share it.

### Q4 — Narrowest Wedge

**Core question**: What is the smallest version someone would pay for?

Not MVP — MVPs are still too big. The narrowest wedge is:

- **One user type** (not "developers and designers and PMs")
- **One workflow** (not "project management" — one specific action)
- **One pain point** (the single most acute frustration)
- **One outcome** (what changes after they use it once)

Evaluate the proposed wedge:

| Score | Level | Description |
|-------|-------|-------------|
| 0 | Platform | "We're building a platform for X" — too broad, no wedge |
| 1 | Multi-feature | Several features bundled. Still too much. |
| 2 | Single feature | One clear feature but serving multiple user types |
| 3 | Narrow wedge | One feature, one user type, one workflow |
| 4 | Razor wedge | So specific it feels too small — but someone would pay today |

**Startup mode addition**: Does the wedge have natural expansion paths? Can you land-and-expand?

### Q5 — Observation & Surprise

**Core question**: What happened when you watched a real person use it?

This question only applies if the product exists in some form. Evaluate:

- **Has observation happened?** Did the founder actually watch someone use the product?
- **Unscripted usage**: What did the user do that was unexpected?
- **Confusion points**: Where did the user get stuck or hesitate?
- **Delight points**: What made them say "oh, that's nice" or lean forward?
- **Abandonment risk**: At what point did they almost give up?

**Red flag**: If the answer is "we haven't watched anyone use it yet" — this is the single most important next step. Stop everything else.

**Surprise taxonomy**:
- **Good surprise**: User found value you didn't design for → potential pivot signal
- **Bad surprise**: User couldn't complete the core task → critical UX failure
- **Neutral surprise**: User used it differently than expected → redesign opportunity

### Q6 — Future-Fit

**Core question**: Does this become more essential as the world changes?

Evaluate against macro trends:

- **AI displacement**: Will AI make this unnecessary in 2 years?
- **Market consolidation**: Will a big player bundle this into their existing product?
- **Regulatory shifts**: Do upcoming regulations help or hurt?
- **Behavioral shifts**: Is the underlying user behavior growing or shrinking?
- **Technology shifts**: Does emerging tech (AI, AR, blockchain, etc.) amplify or replace this?

| Score | Level | Description |
|-------|-------|-------------|
| 0 | Doomed | Actively being disrupted. The window is closing. |
| 1 | At risk | Major threats on the horizon. Defensibility is weak. |
| 2 | Neutral | Stable but not growing. Could go either way. |
| 3 | Tailwind | Macro trends favor this. Growing market or regulatory push. |
| 4 | Inevitable | This becomes more essential every year. Strong structural tailwinds. |

**Startup mode addition**: What is the moat? Network effects, data advantages, switching costs, or brand?

## Step 4: Gap Identification

After analyzing all applicable forcing questions, identify critical gaps:

1. **Evidence gaps** — claims made without supporting data
2. **Specificity gaps** — vague answers that need sharpening ("our users" instead of a named person)
3. **Assumption gaps** — unstated assumptions that could invalidate the product
4. **Execution gaps** — the team lacks a clear path from here to the narrowest wedge

Rank gaps by severity:

| Severity | Description |
|----------|-------------|
| Blocking | Cannot proceed until resolved. Product direction may be wrong. |
| Critical | Must resolve before building. High risk of wasted effort. |
| Important | Should resolve soon. Will cause problems if ignored. |
| Minor | Nice to resolve. Won't derail the product. |

## Step 5: Recommendation Synthesis

Produce a clear go/no-go recommendation:

- **Strong go**: Demand is validated, specificity is high, wedge is clear, future-fit is strong. Build it.
- **Conditional go**: Core idea is sound but gaps exist. Resolve [specific gaps] before building.
- **Pivot suggested**: The forcing questions reveal a different, stronger opportunity. Consider pivoting to [specific alternative].
- **No-go**: Multiple blocking gaps. Demand signal is absent or the future-fit is poor. Do not build this yet.

Include specific next actions — not vague advice. "Interview 5 DevOps engineers at Series B startups about their deployment pain" is actionable. "Do more research" is not.

## Output Structure

```markdown
## Product Validation: {Product Name}

**Mode**: {Startup | Builder}
**Stage**: {Pre-product | Has-users | Has-revenue}

### Forcing Question Analysis

#### Q1: Demand Reality
- **Demand score**: {0-4}
- **Evidence**: {what exists}
- **Gaps**: {what's missing}

#### Q2: Status Quo
- **Current alternatives**: {list}
- **Cost of status quo**: {time/money/frustration}
- **Switching analysis**: {barriers}

#### Q3: Desperate Specificity
- **Target person**: {specific description}
- **Daily frustration**: {specific moment}
- **Reach**: {can you access this person}

#### Q4: Narrowest Wedge
- **Wedge score**: {0-4}
- **Proposed wedge**: {description}
- **Refinement**: {how to narrow further}

#### Q5: Observation & Surprise
- **Observation status**: {done/not done}
- **Key surprises**: {list}
- **Critical insight**: {what this reveals}

#### Q6: Future-Fit
- **Future-fit score**: {0-4}
- **Trend analysis**: {key trends}
- **Moat assessment**: {defensibility}

### Critical Gaps
| Gap | Severity | What to Do |
|-----|----------|------------|
| {gap} | {blocking/critical/important/minor} | {specific action} |

### Recommendation
**Verdict**: {Strong go / Conditional go / Pivot suggested / No-go}
{Rationale and specific next actions}
```

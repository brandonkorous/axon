# Retrospective Methodology

You are performing an engineering retrospective that analyzes development activity to surface metrics, patterns, hotspots, and actionable recommendations.

## Phase 1: Data Collection

Gather raw data from the repository for the specified time range:

1. **Commit log** — all commits with author, timestamp, message, files changed, lines added/removed
2. **PR/MR history** — opened, merged, closed, review comments, time-to-merge
3. **Branch activity** — branches created, merged, abandoned
4. **Tag/release history** — releases within the time range

Default time range is "last 2 weeks" if not specified. Normalize all timestamps to the repository's primary timezone.

## Phase 2: Metrics Dashboard

Calculate top-level metrics:

| Metric | Calculation |
|--------|-------------|
| Total commits | Count of all commits in range |
| Contributors | Unique commit authors |
| PRs opened | PRs created in range |
| PRs merged | PRs merged in range |
| PRs closed (unmerged) | PRs closed without merge |
| Lines added | Sum of insertions |
| Lines removed | Sum of deletions |
| Net lines | Added minus removed |
| Test coverage ratio | Test file changes / total file changes |
| Active development days | Days with at least 1 commit |
| Shipping days | Days with at least 1 PR merged |

## Phase 3: Per-author Analysis

For each contributor, calculate:

1. **Commit volume** — total commits, rank among contributors
2. **Code volume** — lines added, lines removed, net change
3. **Focus areas** — top 3 directories or modules by commit count
4. **Commit patterns** — average commits per active day, preferred commit times
5. **PR behavior** — PRs opened, average PR size, average time-to-merge
6. **Review quality** — if review data available: reviews given, average comments per review

Rank contributors by commit volume but note that volume alone is not a quality indicator.

## Phase 4: Time Analysis

### Hourly Distribution

Build an hourly histogram of commit activity (0-23h):

```
Hour  | Activity
00-05 | ░░ (low)
06-08 | ████ (ramp-up)
09-11 | ████████ (peak)
12-13 | ████ (lunch dip)
14-17 | ███████ (afternoon peak)
18-20 | ████ (wind-down)
21-23 | ░░ (low)
```

### Work Session Detection

Identify work sessions using a 45-minute gap threshold — any gap longer than 45 minutes between commits marks a session boundary.

Classify sessions:

| Session Type | Duration | Interpretation |
|-------------|----------|----------------|
| Deep | 50+ minutes | Sustained focused work |
| Medium | 20-50 minutes | Task completion or review |
| Micro | <20 minutes | Quick fix or config change |

Calculate:
- Average session duration
- Deep session ratio (% of sessions that are deep)
- Flow state estimate: deep sessions with 3+ commits

### Daily Patterns
- Most productive day of week
- Weekend work ratio
- Consecutive shipping day streaks

## Phase 5: Commit Categorization

Parse conventional commit prefixes:

| Prefix | Category | Example |
|--------|----------|---------|
| feat: | Feature | New capability added |
| fix: | Bug fix | Defect corrected |
| refactor: | Refactoring | Code improved without behavior change |
| test: | Testing | Test added or modified |
| chore: | Maintenance | Dependencies, config, tooling |
| docs: | Documentation | Docs added or updated |
| style: | Formatting | Whitespace, formatting only |
| perf: | Performance | Performance improvement |
| ci: | CI/CD | Build or deploy pipeline changes |

Calculate percentage distribution across categories. Flag repositories where >50% of commits lack conventional prefixes.

Trend analysis: compare category distributions across weeks to detect shifts (e.g., increasing fix ratio may signal quality issues).

## Phase 6: Hotspot Identification

### Churn Hotspots
Files changed 5 or more times in the time range. High churn signals instability, active development, or poor abstraction.

| File | Changes | Authors | Category Breakdown |
|------|---------|---------|-------------------|
| path/to/file | N | A, B | 3 fix, 2 feat |

### Coupling Hotspots
Files that are frequently changed together (co-changed in the same commit or PR). Strong coupling may indicate:
- Hidden dependencies
- Missing abstractions
- Files that should be merged or split

### Bug-fix Hotspots
Files with a high ratio of fix: commits to total commits. A file with 80% fix commits is a reliability concern.

Severity classification:

| Bug-fix Ratio | Signal |
|---------------|--------|
| <20% | Normal — healthy development |
| 20-40% | Elevated — monitor for patterns |
| 40-60% | High — consider refactoring |
| >60% | Critical — stability risk |

## Phase 7: PR Size Distribution

Categorize PRs by total lines changed:

| Size | Lines Changed | Target % |
|------|--------------|----------|
| Small | <50 | 40%+ ideal |
| Medium | 50-200 | 30-40% |
| Large | 200-500 | 15-20% |
| XL | 500+ | <10% ideal |

Smaller PRs correlate with:
- Faster review turnaround
- Fewer bugs introduced
- Higher review quality
- Easier rollback if issues arise

Flag if XL PRs exceed 20% of total — recommend breaking into smaller changes.

## Phase 8: Historical Tracking

### Week-over-week Trends

Calculate deltas for key metrics:

| Metric | This Period | Last Period | Delta | Direction |
|--------|------------|-------------|-------|-----------|
| Commits | N | M | ±X | ↑/↓/→ |
| PRs merged | N | M | ±X | ↑/↓/→ |
| Contributors | N | M | ±X | ↑/↓/→ |
| Net lines | N | M | ±X | ↑/↓/→ |

### Velocity Classification

| Pattern | Signal | Recommendation |
|---------|--------|----------------|
| Accelerating | Commits and PRs trending up for 3+ periods | Sustain pace, watch for burnout |
| Steady | Metrics within ±15% across periods | Healthy — maintain current practices |
| Decelerating | Commits and PRs trending down for 3+ periods | Investigate blockers, team capacity |
| Spiking | >50% increase followed by decrease | One-time push — not sustainable |

### Shipping Streaks
- Current consecutive days with at least 1 PR merged
- Longest streak in the time range
- Streak breaks — what caused gaps

## Phase 9: Recommendations

Based on all collected data, generate actionable recommendations:

1. **Process improvements** — based on PR size distribution, review patterns, merge times
2. **Code health** — based on hotspots, bug-fix ratios, churn patterns
3. **Team dynamics** — based on contribution distribution, review load balancing
4. **Velocity insights** — based on trends, session patterns, shipping consistency

Each recommendation must include:
- **Observation**: the data point that triggered this recommendation
- **Impact**: why this matters
- **Action**: specific, concrete step to take

Limit to 5 most impactful recommendations — do not overwhelm with minor observations.

## Rules

- Never interpret metrics as individual performance evaluations — present data without judgment
- Always compare against the team's own baseline, not industry benchmarks
- Flag insufficient data — if the time range has fewer than 10 commits, note that trends are unreliable
- Round percentages to whole numbers for readability
- Use relative comparisons ("2x more than last period") alongside absolute numbers
- Conventional commit parsing should be lenient — accept variations in formatting

## Output Structure

Produce a structured report with these sections:

1. **Metrics dashboard**: table of top-level metrics with comparisons to previous period
2. **Author analysis**: per-contributor breakdown ranked by commit volume
3. **Time patterns**: hourly histogram, session analysis, daily patterns
4. **Commit categories**: prefix distribution table with trend indicators
5. **Hotspots**: churn, coupling, and bug-fix hotspot tables
6. **PR distribution**: size category breakdown with health assessment
7. **Trends**: week-over-week deltas and velocity classification
8. **Shipping streaks**: current and longest streaks with gap analysis
9. **Recommendations**: top 5 actionable insights with observation/impact/action format

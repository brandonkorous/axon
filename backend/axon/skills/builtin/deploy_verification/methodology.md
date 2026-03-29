# Deploy Verification Methodology

You are performing a merge and production verification process that safely lands code changes and confirms they work correctly in the deployed environment.

## Phase 1: Pre-merge Safety

Validate that the code is ready to merge:

### Review Currency
- Check when the last approval was given
- Compare the approval timestamp against the last code push timestamp
- If code changed after the last approval, flag as **stale review** — the reviewer approved different code than what will merge

| Review Status | Condition | Action |
|---------------|-----------|--------|
| Current | Approved after last push | Proceed |
| Stale | Code pushed after approval | Flag — request re-review |
| Missing | No approvals | Block — review required |
| Dismissed | Review dismissed by push | Block — new review required |

### CI Check Validation
- Enumerate all required CI checks from branch protection rules
- Verify each check has passed on the current HEAD
- For failed checks, report the failure reason and whether it's flaky or real
- For pending checks, wait or flag depending on timeout threshold (5 minutes)

### Test Suite Confirmation
- Verify tests passed in CI (not just locally)
- Check that test count hasn't decreased (no deleted tests to make suite pass)
- Flag any skipped tests that were previously active

### Documentation Check
- Verify CHANGELOG is updated if changes are user-facing
- Check that API documentation reflects endpoint changes
- Flag README updates needed for new setup steps or configuration

### PR Description Accuracy
- Compare the PR description against the actual diff
- Flag descriptions that don't mention significant changes
- Flag descriptions that mention changes not in the diff

## Phase 2: Merge Operations

Execute the merge safely:

1. **Strategy selection** — use the provided strategy input, or auto-detect from repository settings:
   - **Squash**: multiple small commits → single clean commit (default for feature branches)
   - **Rebase**: linear history preferred, commits are well-organized
   - **Merge commit**: preserving branch history is important

2. **Merge queue respect** — if the repository uses a merge queue, submit to the queue rather than merging directly

3. **Conflict detection** — if merge conflicts exist, report them with file-level detail and abort

4. **Post-merge verification** — confirm the merge completed successfully by checking:
   - Merge commit exists on the target branch
   - Branch protection rules were satisfied
   - No force-push was required

## Phase 3: Deployment

Monitor the deployment process:

### Infrastructure Auto-detection

Identify the deployment platform by checking for configuration files:

| Platform | Detection Signal |
|----------|-----------------|
| Fly.io | fly.toml |
| Render | render.yaml |
| Vercel | vercel.json or .vercel/ |
| Netlify | netlify.toml or _redirects |
| Heroku | Procfile + heroku remote |
| Railway | railway.json or railway.toml |
| GitHub Actions | .github/workflows/ with deploy job |
| Custom | Dockerfile + custom CI deploy step |

### Deploy Monitoring
1. **Trigger identification** — determine if deploy is automatic (on merge) or manual (requires action)
2. **Status polling** — check deploy status at 15-second intervals, up to 10-minute timeout
3. **Log streaming** — capture deploy logs for diagnosis if the deploy fails
4. **Health check** — after deploy completes, verify the application is responding

### Staging-first Option
If target is "production" and a staging environment exists:
1. Deploy to staging first
2. Run full verification against staging
3. Only proceed to production if staging verification passes
4. Report staging results before promoting

## Phase 4: Production Verification

Verify the deployment is healthy:

### Verification Depth by Change Type

| Change Type | Verification Level |
|-------------|-------------------|
| Frontend (UI/CSS/components) | Visual checks + console monitoring + performance |
| Backend (API/logic/data) | API health + endpoint verification + data integrity |
| Configuration (env/infra/config) | Environment checks + service connectivity |
| Documentation only | Minimal — confirm deploy succeeded |
| Full-stack | All verification types |

### Page Load Checks
- Load each critical path URL
- Verify HTTP 200 response
- Check page load time against baseline (flag if >20% slower)
- Verify no redirect loops

### Console Error Monitoring
- Check browser console for JavaScript errors on critical pages
- Distinguish between pre-existing errors and new errors introduced by this deploy
- Flag any new errors as verification failures

### Performance Comparison
- Compare response times against the pre-deploy baseline
- Flag endpoints that are >20% slower
- Check memory and CPU usage if monitoring is available

| Performance Delta | Status |
|-------------------|--------|
| Within 10% | Normal — no action |
| 10-20% slower | Warning — investigate |
| >20% slower | Alert — potential regression |
| Faster | Note — positive change |

### API Health Checks
- Hit health/status endpoints
- Verify all dependent services are connected (database, cache, external APIs)
- Check that new endpoints respond correctly
- Verify existing endpoints still work (no regressions)

### Screenshot Evidence
- Capture screenshots of critical pages post-deploy
- Note any visual differences from the expected state
- Store as verification evidence

## Phase 5: Rollback Capability

If verification fails, provide a rollback path:

1. **Rollback procedure** — document the exact steps to revert:
   - For Fly.io: `fly releases` to identify previous release, `fly deploy --image` to roll back
   - For Vercel/Netlify: redeploy previous production deployment from dashboard
   - For container-based: redeploy previous image tag
   - For git-based: revert merge commit and push

2. **Auto-revert threshold** — if any of these conditions are met, recommend immediate rollback:
   - Health endpoint returns non-200
   - Error rate increases by >5x compared to pre-deploy
   - Response time increases by >3x
   - Critical user-facing page returns 500

3. **Partial rollback** — if the deploy includes multiple services, identify which service is failing and recommend rolling back only that service

4. **Post-rollback verification** — after rollback, run the same verification checks to confirm the system is back to its previous state

## Rules

- Never merge without confirming all required checks pass
- Never skip staging if the repository has a staging environment and the target is production
- Always capture verification evidence — screenshots, response times, health check results
- If any verification step fails, stop and report before proceeding to the next step
- Treat stale reviews as seriously as missing reviews — the reviewer needs to see the final code
- Deploy monitoring timeout of 10 minutes — if the deploy hasn't completed, flag as stuck

## Output Structure

Produce a structured report with these sections:

1. **Pre-merge checks**: table of each check (review, CI, tests, docs, PR accuracy) with pass/fail and detail
2. **Merge result**: strategy used, merge commit SHA, any complications
3. **Deploy status**: platform detected, deploy duration, final status, log excerpts if failed
4. **Verification results**: table of each check type with status, measurements, and evidence
5. **Performance comparison**: before/after metrics for response times and error rates
6. **Rollback plan**: documented procedure specific to the detected platform, with exact commands
7. **Overall status**: PASSED (safe to leave), WARNING (monitor closely), or FAILED (rollback recommended)

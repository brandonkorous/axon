# GitHub Open-Source Setup Guide

A step-by-step checklist for configuring the Axon repository on GitHub as a professional open-source project. Assumes you're starting from a fresh GitHub repo or converting an existing private repo.

---

## Phase 1: Create the GitHub Organization

You want an org (like `brandonkorous`) rather than hosting under your personal account. This looks more professional and lets you add collaborators with granular permissions later.

1. Go to https://github.com/organizations/plan
2. Choose the **Free** plan (plenty for open source)
3. Organization name: `brandonkorous` (or whatever you want — this becomes `github.com/brandonkorous/axon`)
4. Contact email: your email
5. Select "My personal account" as the owner
6. Skip the "add members" step for now

### Transfer or Create the Repo

**Option A — New repo under the org:**
1. Go to https://github.com/organizations/brandonkorous/repositories/new
2. Name: `axon`
3. Description: "Self-hosted AI command center. Orchestrate AI advisors with persistent memory, voice, and a real-time boardroom."
4. Set to **Public**
5. Don't initialize with README (you already have one)
6. Push your local repo:
   ```bash
   cd d:/corp/axon
   git remote add origin https://github.com/brandonkorous/axon.git
   git push -u origin main
   ```

**Option B — Transfer existing repo:**
1. Go to your existing repo → Settings → Danger Zone → Transfer repository
2. Transfer to the `brandonkorous` organization
3. GitHub will set up redirects from the old URL automatically

---

## Phase 2: Repository Settings

Go to your repo → **Settings** tab.

### General Settings
`Settings → General`

1. **Repository name:** `axon`
2. **Description:** "Self-hosted AI command center. Orchestrate AI advisors with persistent memory, voice, and a real-time boardroom."
3. **Website:** Leave blank for now (or add your docs URL later)
4. **Topics/Tags:** Click "Add topics" and add these (they help discoverability):
   - `ai`, `ai-agents`, `self-hosted`, `command-center`, `llm`, `voice-ai`, `multi-agent`, `ollama`, `claude`, `docker`, `open-source`, `developer-tools`
5. **Social preview image:** Upload your banner or a 1280x640 social card
   - Settings → scroll to "Social preview" → Upload image
   - You can use the axon-banner.svg converted to PNG, or create a dedicated social card

### Features (same page, scroll down)
- [x] **Issues** — enabled
- [x] **Sponsorships** — enabled (this activates the "Sponsor" button using your FUNDING.yml)
- [ ] **Projects** — optional, enable if you want a project board
- [x] **Discussions** — **ENABLE THIS** (critical for community)
- [ ] **Wiki** — leave disabled (use docs/ folder instead)

### Pull Requests (same page, scroll down)
- [x] Allow merge commits
- [x] Allow squash merging ← **set as default** (keeps history clean)
- [ ] Allow rebase merging — optional
- [x] Always suggest updating pull request branches
- [x] Automatically delete head branches ← **enable this** (cleans up merged branches)

### Danger Zone (same page, bottom)
- Make sure visibility is **Public**

---

## Phase 3: Branch Protection Rules

This prevents accidental pushes to main and enforces code review.

`Settings → Branches → Add branch ruleset`

Or use the classic method: `Settings → Branches → Add rule`

1. **Branch name pattern:** `main`
2. Enable these protections:
   - [x] **Require a pull request before merging**
     - Required approving reviews: `1` (increase later when you have more maintainers)
     - [x] Dismiss stale reviews when new commits are pushed
   - [x] **Require status checks to pass before merging**
     - Add these required checks (after CI runs once):
       - `frontend`
       - `backend`
       - `docker`
   - [x] **Require conversation resolution before merging**
   - [x] **Require linear history** (enforces squash/rebase, no merge commits on main)
   - [ ] **Include administrators** — leave unchecked for now so you can push directly while setting up. **Enable this later** when you have contributors.

> **Note:** You need to push and have CI run at least once before you can select the status checks by name. Push your code first, let the workflow run, then come back and configure this.

---

## Phase 4: Enable GitHub Discussions

`Settings → General → Features → Discussions → check the box`

Then go to the **Discussions** tab and set up categories:

1. Click **Categories** (pencil icon)
2. Keep the defaults, but make sure you have:
   - **Announcements** (only maintainers can post) — for releases, roadmap updates
   - **Q&A** (question/answer format) — for support questions
   - **Ideas** (open-ended) — for feature brainstorming
   - **Show and Tell** (open-ended) — for people to share what they built with Axon
3. Pin a welcome post in Announcements introducing the project

---

## Phase 5: Labels

Good labels make issue triage fast. Go to **Issues → Labels** and set up:

Delete the defaults and create these (or edit existing ones):

### Priority
| Label | Color | Description |
|-------|-------|-------------|
| `P0: critical` | `#d73a4a` (red) | Broken for everyone, needs immediate fix |
| `P1: important` | `#e4e669` (yellow) | Important but not blocking |
| `P2: nice-to-have` | `#0e8a16` (green) | Would be nice, no rush |

### Type
| Label | Color | Description |
|-------|-------|-------------|
| `bug` | `#d73a4a` | Something isn't working |
| `feature` | `#a2eeef` | New feature request |
| `enhancement` | `#7057ff` | Improvement to existing feature |
| `documentation` | `#0075ca` | Documentation only |
| `refactor` | `#e4e669` | Code improvement, no behavior change |
| `security` | `#d73a4a` | Security-related |

### Area
| Label | Color | Description |
|-------|-------|-------------|
| `frontend` | `#1d76db` | React/UI related |
| `backend` | `#5319e7` | Python/API related |
| `voice` | `#f9d0c4` | Voice interface related |
| `memory` | `#c5def5` | Memory/vault system |
| `agents` | `#bfdadc` | Agent orchestration |
| `infra` | `#d4c5f9` | Docker, CI, deployment |

### Status
| Label | Color | Description |
|-------|-------|-------------|
| `good first issue` | `#7057ff` | Good for newcomers |
| `help wanted` | `#008672` | Extra attention needed |
| `wontfix` | `#ffffff` | This will not be worked on |
| `duplicate` | `#cfd3d7` | Already tracked |

> **Tip:** The `good first issue` and `help wanted` labels are special — GitHub surfaces these in the [contributor discovery page](https://github.com/topics/good-first-issue). Always keep a few issues with these labels open to attract contributors.

You can bulk-create labels with the GitHub CLI:
```bash
# Example (run for each label)
gh label create "P0: critical" --color "d73a4a" --description "Broken for everyone, needs immediate fix" --repo brandonkorous/axon
gh label create "feature" --color "a2eeef" --description "New feature request" --repo brandonkorous/axon
gh label create "frontend" --color "1d76db" --description "React/UI related" --repo brandonkorous/axon
gh label create "good first issue" --color "7057ff" --description "Good for newcomers" --repo brandonkorous/axon
# ... repeat for all labels
```

---

## Phase 6: Releases & Tags

When you're ready to publish your first release:

1. Tag your code:
   ```bash
   git tag -a v0.1.0 -m "Initial public release"
   git push origin v0.1.0
   ```
2. Go to **Releases** → **Draft a new release**
3. Choose the `v0.1.0` tag
4. Title: `v0.1.0 — Initial Release`
5. Description: Copy from CHANGELOG.md or write release notes
6. Check **Set as the latest release**
7. Publish

> **Tip:** Consider setting up automated releases later with a GitHub Action that creates releases from tags and auto-generates changelogs.

---

## Phase 7: Security Settings

`Settings → Code security and analysis`

Enable these (all free for public repos):

- [x] **Dependency graph** — shows your dependency tree
- [x] **Dependabot alerts** — notifies you of known vulnerabilities in dependencies
- [x] **Dependabot security updates** — auto-creates PRs to fix vulnerable deps
- [x] **Secret scanning** — detects accidentally committed API keys/tokens
- [x] **Secret scanning push protection** — **blocks pushes** that contain secrets (prevents accidents)

These are critical. They cost nothing and prevent embarrassing security incidents.

---

## Phase 8: GitHub Actions Permissions

`Settings → Actions → General`

1. **Actions permissions:** Allow all actions and reusable workflows
2. **Workflow permissions:** Read repository contents and packages permissions
   - [x] Allow GitHub Actions to create and approve pull requests (needed for Dependabot)

---

## Phase 9: Environments (Optional but Recommended)

If you plan to publish Docker images or deploy docs:

`Settings → Environments → New environment`

Create a `production` environment with:
- Required reviewers (yourself)
- This protects deployment workflows from running without approval

---

## Phase 10: Community Profile Check

GitHub has a built-in community health checker:

1. Go to `https://github.com/brandonkorous/axon/community`
2. This page shows you a checklist of community files
3. Everything should be green after your setup:
   - [x] Description
   - [x] README
   - [x] Code of conduct
   - [x] Contributing
   - [x] License
   - [x] Security policy
   - [x] Issue templates
   - [x] Pull request template

If anything is yellow/red, click through to fix it.

---

## Phase 11: Social & Discovery

### Make your repo discoverable

1. **Topics:** Already done in Phase 2, but review them periodically
2. **"Used by" badge:** This appears automatically when other repos depend on yours via package managers
3. **Pin the repo:** Go to your org profile → Customize pins → Pin the axon repo

### Set up social links

1. **Organization profile:** Go to `github.com/brandonkorous` → Edit profile
   - Avatar: Upload the axon-logo.svg (convert to PNG first)
   - Bio: "Building the open-source AI command center"
   - Location, website, Twitter/X, etc.
2. **Create an org README:** Create a repo called `.github` under the org with a `profile/README.md` — this shows on the org's GitHub page

### README profile for the org

Create `brandonkorous/.github` repo with `profile/README.md`:
```markdown
## Axon

Self-hosted AI command center. Orchestrate AI advisors with persistent memory, voice interfaces, and a real-time boardroom.

- [Main Repository](https://github.com/brandonkorous/axon)
- [Documentation](https://github.com/brandonkorous/axon/tree/main/docs)
- [Contributing](https://github.com/brandonkorous/axon/blob/main/CONTRIBUTING.md)
```

---

## Phase 12: External Integrations (When Ready)

These are optional but help build momentum:

### Discord Server
1. Create a Discord server for the project
2. Channels: `#general`, `#help`, `#feature-requests`, `#show-and-tell`, `#contributors`, `#announcements`
3. Add a GitHub webhook to post new issues/PRs/releases to a `#github-feed` channel
   - Discord channel settings → Integrations → Webhooks → Copy URL
   - GitHub repo → Settings → Webhooks → Add webhook → paste Discord URL + `/github` at the end
   - Select events: Issues, Pull requests, Releases

### Docker Hub (or GitHub Container Registry)
1. Publish official images so users can `docker pull brandonkorous/axon`
2. Add a GitHub Action to auto-build and push images on release tags
3. GitHub Container Registry (ghcr.io) is free for public repos and integrates nicely

### Awesome Lists & Directories
Once you have a stable release:
- Submit to awesome-selfhosted: https://github.com/awesome-selfhosted/awesome-selfhosted
- Submit to awesome-ai-agents lists
- Post on Hacker News (Show HN), Reddit r/selfhosted, r/LocalLLaMA, r/artificial
- Product Hunt launch (time this deliberately)

---

## Quick Reference: Settings Checklist

Copy this into an issue to track your progress:

```markdown
## GitHub Repo Setup Checklist

### Organization
- [ ] Create GitHub org (brandonkorous)
- [ ] Upload org avatar
- [ ] Write org profile README

### Repository Settings
- [ ] Set description and topics
- [ ] Upload social preview image
- [ ] Enable Discussions
- [ ] Enable Sponsorships
- [ ] Set squash merge as default
- [ ] Enable auto-delete head branches
- [ ] Make repo public

### Branch Protection
- [ ] Protect main branch
- [ ] Require PR reviews
- [ ] Require CI status checks (after first CI run)

### Security
- [ ] Enable Dependabot alerts
- [ ] Enable Dependabot security updates
- [ ] Enable secret scanning
- [ ] Enable push protection

### Community
- [ ] Verify community profile is 100% (github.com/brandonkorous/axon/community)
- [ ] Set up Discussion categories
- [ ] Create initial labels
- [ ] Pin welcome discussion post

### Launch
- [ ] Create v0.1.0 tag and release
- [ ] Set up Discord server
- [ ] Publish Docker images
- [ ] Submit to awesome-selfhosted
- [ ] Write Show HN post
```

---

## Things People Forget

1. **Add a `.gitignore` for secrets** — double-check that `.env`, `*.key`, and credential files are in `.gitignore` before going public. Run `git log --all --full-history -- "*.env" "*.key" "*.pem"` to check if any were ever committed.

2. **Scrub git history** — if you ever committed API keys, passwords, or secrets, they're still in the git history even if you deleted the file. Use [BFG Repo Cleaner](https://rtyley.github.io/bfg-repo-cleaner/) or `git filter-repo` to purge them before going public.

3. **License compatibility** — AGPL-3.0 is a strong copyleft license. This means anyone who modifies and deploys Axon as a network service must share their changes. This is intentional and good for your project, but be aware some companies avoid AGPL. If you want broader adoption, consider offering dual licensing later.

4. **Don't go public until CI is green** — first impressions matter. If someone clones and the build is broken, they won't come back.

5. **Have at least 3-5 "good first issue" tickets ready** — this is how new contributors find your project. Make these genuinely approachable (typo fixes, small UI tweaks, adding tests).

6. **README screenshots** — once the UI is stable, add real screenshots or a GIF demo to the README. This is the single highest-impact thing for GitHub star conversion. The SVG banner is great, but people want to see the actual product.

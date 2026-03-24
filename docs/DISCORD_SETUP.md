# Discord Setup Guide

## Welcome Screen

**Server Settings → Welcome Screen → Enable**

**Server Description:**
```
The official community for Axon — the open-source, self-hosted AI command center. Get help, share what you've built, and shape the roadmap.
```

**Recommended Channels (add these to the welcome screen):**

| Channel | Emoji | Description |
|---------|-------|-------------|
| #general | 👋 | Introduce yourself and chat with the community |
| #help | ❓ | Get help with setup, configuration, and troubleshooting |
| #announcements | 📢 | Stay up to date with releases and project news |
| #show-and-tell | 🚀 | See what others are building with Axon |
| #feature-requests | 💡 | Propose ideas and vote on what gets built next |

---

## Channel Descriptions

Paste these into each channel's **Edit Channel → Topic** field.

**#general**
```
General discussion about Axon. Introductions welcome — tell us what you're building.
```

**#help**
```
Need help with setup, configuration, or troubleshooting? Post here. Include your OS, Docker version, and logs when possible.
```

**#announcements** (admin-only posting)
```
Official updates, releases, and breaking changes. Watch this channel to stay current.
```

**#feature-requests**
```
Propose features and discuss ideas. One idea per thread. Upvote what you want to see built.
```

**#show-and-tell**
```
Share your custom agents, workflows, integrations, or anything cool you've done with Axon.
```

**#contributors**
```
Coordination for active contributors. PRs, architecture discussions, and dev talk.
```

**#github-feed** (read-only, webhook-powered)
```
Automated feed of GitHub activity — issues, pull requests, and releases.
```

**#off-topic**
```
Not everything has to be about AI agents.
```

---

## Welcome Message

Post this as the first message in **#general**, then pin it.

---

**Welcome to the Axon community!**

Axon is an open-source, self-hosted AI command center. Run persistent AI advisors on your own infrastructure with memory that lasts, voice interfaces, and multi-agent collaboration — no cloud dependency required.

**Quick links:**
- 📖 [GitHub](https://github.com/brandonkorous/axon) — source code, issues, and docs
- 🚀 [Quick Start](https://github.com/brandonkorous/axon#quick-start) — get running in 3 commands
- 🤝 [Contributing](https://github.com/brandonkorous/axon/blob/main/CONTRIBUTING.md) — want to help build Axon?
- 💬 [Discussions](https://github.com/brandonkorous/axon/discussions) — longer-form Q&A and ideas

**New here?** Drop an intro — what are you building, what brought you to Axon?

---

## Roles (Optional)

| Role | Color | Purpose |
|------|-------|---------|
| **Maintainer** | Violet (#7c3aed) | Core team |
| **Contributor** | Green (#10b981) | Has merged a PR |
| **Early Adopter** | Blue (#3b82f6) | Joined before v1.0 |

---

## Server Settings Checklist

- [ ] Enable Welcome Screen with description and channels above
- [ ] Set server icon (use axon-logo.svg converted to PNG)
- [ ] Set server banner (use axon-banner.svg converted to PNG)
- [ ] Create channels listed above
- [ ] Set #announcements and #github-feed to admin/webhook-only posting
- [ ] Add GitHub webhook to #github-feed (webhook URL + `/github`)
- [ ] Post and pin the welcome message in #general
- [ ] Enable Community features (Server Settings → Enable Community) for announcement channels

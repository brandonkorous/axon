# Project Jarvis — Bootstrap Prompt

Copy everything below the line into your first Claude Code conversation in this directory.

---

## Context

I'm building a self-hosted AI command center — codename **Jarvis**. This is a Dockerized application that runs locally on my machine and serves as my central intelligence hub for running a startup.

### What Already Exists

I have four AI advisor personas built as Claude Desktop projects with Obsidian-backed memory systems. They work, but they're limited by Claude Desktop's lack of filesystem access and inability to run as persistent agents. I want to evolve this into a real application.

#### The Advisors

| Persona | Name | Role | Vault Path |
|---------|------|------|------------|
| CEO Advisor | **Marcus** | Board chair archetype — strategy, fundraising, financials, hiring, vision. Blunt, numbers-first, pattern matcher, urgency-obsessed. | `D:\corp\orgs\employment-networks\vaults\marcus` |
| CTO Advisor | **Raj** | Architect emeritus — architecture, infrastructure, vendors, tech debt, security, scaling. Thinks in failure modes, allergic to complexity, vendor-skeptical. | `D:\corp\orgs\employment-networks\vaults\raj` |
| COO Advisor | **Diana** | Growth operator — GTM, marketing, BD pipeline, campaigns, channels. Execution-obsessed, recruiting industry native, thinks in funnels. | `D:\corp\orgs\employment-networks\vaults\diana` |
| **Huddle** | All three | Group advisory session — advisors debate, disagree, challenge each other, and converge on recommendations. Has conversation modes: vote, devil's advocate, pressure test, quick take. | `D:\corp\orgs\employment-networks\vaults\huddle` |

Each persona has:
- A detailed backstory, personality, communication style, and acknowledged blind spots
- An Obsidian vault with structured memory (decisions, contacts, strategies, etc.)
- Automatic save triggers (saves knowledge without being asked)
- First-message behavior (reads vault, greets in character, references past conversations)

#### The Enterprise Architect Channel

Raj (CTO) has read access to the codebase's enterprise architect memory at `G:\code\splits.network\.memory\claude` and can send tasks to an inbox at `G:\code\splits.network\.memory\claude\inbox\`. The enterprise architect (Claude Code in the dev repo) picks up tasks, does codebase work, and leaves results in `inbox\completed\`.

#### Full Persona Instructions

The complete persona definitions are in the persona YAML configs and system prompt files:
- `D:\corp\axon\backend\axon\personas\marcus.yaml` — CEO advisor config
- `D:\corp\axon\backend\axon\personas\raj.yaml` — CTO advisor config
- `D:\corp\axon\backend\axon\personas\diana.yaml` — COO advisor config
- `D:\corp\axon\backend\axon\personas\huddle.yaml` — Group session config

### The Company

**Employment Networks** — a split-fee recruiting marketplace ecosystem:
- **Splits Network** (splits.network) — Recruiter-facing marketplace for split-fee placements
- **Applicant Network** (applicant.network) — Candidate-facing platform matching job seekers with recruiters
- **Employment Networks** (employment-networks.com) — Parent brand and ecosystem hub

Two-person founding team. I'm the CEO/CTO/majority shareholder (sole technical founder). My co-founder is COO handling marketing, BD, and operations.

The platform is a TypeScript monorepo: 28 Fastify microservices, 6 Next.js 16 frontends, Supabase Postgres, RabbitMQ, Redis, LiveKit, Stripe, Clerk, OpenAI. Deployed on Azure AKS.

### What I Want to Build

A self-hosted application (Docker Desktop or similar) that evolves the Claude Desktop personas into a real interactive command center. Think Jarvis — not a chatbot, a persistent AI-powered operations layer.

#### Core Vision

1. **Persistent advisor personas** — Marcus, Raj, Diana, and the Boardroom running as always-available agents, not ephemeral chat sessions. They maintain their memory across sessions and proactively surface things.

2. **Real filesystem access** — Read/write to their Obsidian vaults natively. No copy-pasting instructions. The memory system works automatically.

3. **The Boardroom as a live experience** — A UI where I can see the advisors discussing in real-time, not just formatted markdown. Visual distinction between speakers. The ability to direct the conversation ("Marcus, respond to that" or "Let's vote").

4. **Cross-agent communication** — Raj can talk to the enterprise architect. Diana can check if a feature she's planning a campaign for is actually built. Marcus can pull financial data. Agents can message each other.

5. **Proactive intelligence** — Agents that don't just wait for questions. Raj notices a vendor contract is expiring and flags it. Diana sees a campaign deadline approaching. Marcus notices burn rate trends.

6. **Central dashboard** — One screen showing: active advisors, recent decisions, pending action items, inbox status, vault health, and quick-launch into any conversation.

7. **Voice interface** (stretch goal) — Talk to advisors instead of typing. Each persona could have a distinct voice.

#### Technical Preferences

- Docker Desktop for local deployment
- The existing Obsidian vaults should be mounted as volumes (not migrated to a database)
- Claude API (Anthropic SDK) for the AI layer — I have API access
- Web-based UI accessible at localhost
- The system should be extensible — adding a new advisor should be straightforward

#### What I DON'T Want

- A SaaS dependency — this runs on my machine
- Electron app — web UI served from Docker
- Rebuilding what exists — the persona definitions, vault structures, and memory systems are already designed and working. Build on top of them.

### My Technical Profile

I'm a senior full-stack TypeScript developer. I built the entire Employment Networks platform solo. Don't dumb things down. I can handle complex architecture, but I value simplicity — do the simplest thing that works.

### First Steps

Start by understanding the full scope of what exists (read the persona instruction files) and then propose an architecture. I want to talk through the approach before writing code. Key questions to answer:

1. What's the tech stack for Jarvis itself?
2. How do we structure the agent runtime?
3. How does the UI work?
4. How do we handle persistent memory with the existing Obsidian vaults?
5. What's the MVP vs. the full vision?
6. How do we handle the Claude API costs of running multiple agents?
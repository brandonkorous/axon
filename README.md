<p align="center">
  <img src=".github/assets/axon-banner.svg" width="700" alt="Axon — Self-hosted AI Command Center" />
</p>

<p align="center">
  <strong>Your self-hosted AI command center.</strong><br />
  Orchestrate AI advisors with persistent memory, voice interfaces, and a real-time boardroom — entirely on your infrastructure.
</p>

<p align="center">
  <a href="https://github.com/brandonkorous/axon/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-AGPL--3.0-violet" alt="License" /></a>
  <a href="https://github.com/brandonkorous/axon/stargazers"><img src="https://img.shields.io/github/stars/brandonkorous/axon?style=flat&color=yellow" alt="GitHub Stars" /></a>
  <a href="https://hub.docker.com/r/brandonkorous/axon"><img src="https://img.shields.io/docker/pulls/brandonkorous/axon?color=blue" alt="Docker Pulls" /></a>
  <a href="https://discord.gg/axon"><img src="https://img.shields.io/badge/discord-join%20chat-5865F2" alt="Discord" /></a>
  <a href="https://github.com/brandonkorous/axon/actions"><img src="https://img.shields.io/github/actions/workflow/status/brandonkorous/axon/ci.yml?label=CI" alt="CI Status" /></a>
  <a href="https://useaxon.dev"><img src="https://img.shields.io/badge/website-useaxon.dev-teal" alt="Website" /></a>
</p>

---

<p align="center">
  <img src=".github/assets/axon-demo.gif" width="700" alt="Axon Demo" />
</p>

---

## Why Axon?

Most AI tools give you a chatbot. Axon gives you a **boardroom**.

Run multiple AI advisors — CEO, CTO, COO, and any custom persona you define — that maintain persistent memory across sessions, debate each other in real-time, and proactively surface insights you didn't think to ask for. Everything runs on your machine. Your data never leaves your infrastructure.
![axon Dashboard screenshot](.github/assets/axon-dashboard.png)
![axon Huddle screenshot](.github/assets/axon-huddle.png)

---

## Features

### Intelligence

|               | Feature                   | Description                                                                       |
| ------------- | ------------------------- | --------------------------------------------------------------------------------- |
| **Agents**    | Specialist Advisors       | A team of domain experts with distinct personas, vaults, voices, and delegation rules — not one generic chatbot |
| **Boardroom** | Real-Time Huddles         | Group discussions with multiple AI specialists. Six modes: standard, vote, devil's advocate, pressure test, quick take, decision |
| **Brain**     | Structured Reasoning      | Graph-based reasoning engine with multi-strategy evaluation, confidence scoring, contradiction detection, and full decision traceability |
| **Delegate**  | Task Delegation           | Advisors delegate work to each other autonomously (sync or async) across research, audit, implementation, and investigation tasks |
| **Recruit**   | Agent Recruitment         | Request new specialist agents on the fly with user approval workflows |

### Memory

|               | Feature                   | Description                                                                       |
| ------------- | ------------------------- | --------------------------------------------------------------------------------- |
| **Vault**     | Neural Memory Trees       | Obsidian-compatible markdown vaults with YAML frontmatter, wikilinks, full-text search, and graph-based relationship tracking |
| **Consolidate** | Memory Consolidation   | LLM-driven vault maintenance — duplicate merging, stale archiving, contradiction detection, orphan adoption, and confidence scoring |
| **Recall**    | Intelligent Recall        | Context-aware retrieval that surfaces relevant vault entries during conversations. Outcome linking lets advisors learn from experience |
| **Watch**     | Vault Sync                | File watcher for external changes — edit vaults in Obsidian and they sync automatically |

### Interaction

|               | Feature                   | Description                                                                       |
| ------------- | ------------------------- | --------------------------------------------------------------------------------- |
| **Voice**     | Voice-First Interface     | Whisper STT, Piper/ElevenLabs/Azure TTS, per-advisor voice catalog, adjustable speed, continuous voice mode |
| **Connect**   | Platform Integrations     | Slack (Socket Mode), Microsoft Teams (Bot Framework), Zoom (meetings + transcription), Discord (server deployment) |
| **Dashboard** | Command Center            | Unified view: active agents, kanban task board, issues, approvals, vault health, and per-agent cost tracking |
| **Commands**  | Slash Commands            | Direct memory operations: `/sleep`, `/remember`, `/recall`, `/forget`, `/tasks`, `/status` |

### Autonomy

|               | Feature                   | Description                                                                       |
| ------------- | ------------------------- | --------------------------------------------------------------------------------- |
| **Runner**    | Autonomous Runners        | Agent-spawned worker processes via Claude CLI with Docker sandbox, lifecycle management, and real-time monitoring |
| **Schedule**  | Proactive Scheduling      | Background heartbeat for inbox checks, task execution, and knowledge review at configurable intervals |
| **Research**  | Deep Research             | Two-tier LLM strategy (local compression + reasoning analysis), web scraping, YouTube transcript extraction, multi-source synthesis |
| **Media**     | Media Processing          | YouTube transcript extraction and analysis with two-tier compression for cost-effective processing |

### Infrastructure

|               | Feature                   | Description                                                                       |
| ------------- | ------------------------- | --------------------------------------------------------------------------------- |
| **Models**    | Multi-LLM Support         | Anthropic Claude, OpenAI, or fully local via Ollama — no API keys required for local operation |
| **Orgs**      | Multi-Organization        | Isolated vaults, agents, and settings per organization with pre-built templates (Startup, Student, Job Hunt, Family, Creator) |
| **Shield**    | Full Audit Trail          | Append-only, immutable audit logs filterable by date, agent, action, or tool — complete transparency |
| **Extend**    | Plugins & Skills          | Plugin architecture with registry and 10 built-in skills (brainstorming, code review, debugging, decision analysis, etc.) |
| **Secure**    | Encryption & Isolation    | AES encryption for stored credentials, Docker sandboxing for workers, network isolation |
| **Work**      | Task & Issue Management   | Tasks (P0-P3 priority), issues, threaded comments, approval workflows, and achievement tracking |

---

## Quick Start

Get Axon running in under two minutes.

```bash
# 1. Clone the repository
git clone https://github.com/brandonkorous/axon.git && cd axon

# 2. Configure your environment
cp .env.example .env
# Edit .env — add your API keys (Anthropic, OpenAI, or use Ollama for fully local)

# 3. Launch
docker compose up
```

Open **[http://localhost:3000](http://localhost:3000)** and meet your advisors.

> **Want fully local LLMs?** See [Local LLM Support](#local-llm-support) below.

---

## Architecture

Axon runs three services via Docker Compose:

```
┌─────────────────────────────────────────────┐
│                  Frontend                    │
│        React 19 · Vite · TailwindCSS        │
│           DaisyUI · Framer Motion            │
│                 :3000                        │
└──────────────────┬──────────────────────────┘
                   │ REST / WebSocket
┌──────────────────▼──────────────────────────┐
│                  Backend                     │
│      FastAPI · SQLAlchemy · LiteLLM          │
│        SQLite (default) or Postgres          │
│                 :8000                        │
└──────────┬───────────────────┬──────────────┘
           │                   │
   ┌───────▼───────┐   ┌──────▼──────┐
   │  LLM Providers │   │   Ollama    │
   │ Claude, OpenAI │   │ Local LLMs  │
   └───────────────┘   │   :11434    │
                        └─────────────┘
```

- **Frontend** — React SPA with real-time agent activity, boardroom view, and vault management
- **Backend** — FastAPI server handling agent orchestration, memory persistence, and multi-provider LLM routing via LiteLLM
- **Ollama** (optional) — Run models like `llama3`, `qwen2.5`, and others entirely on your hardware

---

<details>
<summary><strong>Configuration</strong></summary>

### Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable            | Description                                      | Required            |
| ------------------- | ------------------------------------------------ | ------------------- |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude models              | If using Claude     |
| `OPENAI_API_KEY`    | OpenAI API key                                   | If using OpenAI     |
| `DEFAULT_MODEL`     | Default LLM model identifier                     | Yes                 |
| `OLLAMA_BASE_URL`   | Ollama endpoint (default: `http://ollama:11434`) | If using local LLMs |
| `DATABASE_URL`      | Database connection string (default: SQLite)     | No                  |
| `VAULT_PATH`        | Path to the memory vault directory               | No                  |

For a full list of options, see [`.env.example`](.env.example).

</details>

<details>
<summary><strong>Adding Custom Agents</strong></summary>

### Create a New Advisor

Define a new advisor by adding a YAML file to the personas directory:

```yaml
# personas/cfo-advisor.yaml
name: CFO Advisor
role: Chief Financial Officer
description: Financial strategy, fundraising, unit economics, and fiscal discipline.
model: claude-sonnet-4-20250514
voice: onyx
system_prompt: |
    You are a seasoned CFO advising a startup. You focus on burn rate,
    runway, unit economics, and fundraising strategy. Be direct and
    data-driven. Flag financial risks early.
```

Restart the backend and your new advisor appears in the dashboard. No code changes required.

</details>

<details>
<summary><strong>Local LLM Support</strong></summary>

### Run Fully Local with Ollama

No API keys needed. Run everything on your machine:

```bash
docker compose --profile local-llm up
```

This starts Ollama alongside the frontend and backend. Models are pulled automatically on first use.

Set your default model in `.env`:

```env
DEFAULT_MODEL=ollama/llama3
OLLAMA_BASE_URL=http://ollama:11434
```

Supported local models include `llama3`, `qwen2.5`, `mistral`, `codellama`, and any model available in the [Ollama library](https://ollama.com/library).

</details>

---

## Roadmap

- [x] Multi-agent orchestration with persistent memory
- [x] Voice-first interface with per-persona voices
- [x] Real-time boardroom / Huddle sessions (6 modes)
- [x] Docker Compose deployment
- [x] Multi-LLM support (Claude, OpenAI, Ollama)
- [x] Achievement system and audit logging
- [x] Slack, Teams, Zoom, and Discord integrations
- [x] Plugin system with registry and built-in web research
- [x] Agent-to-agent delegation chains (sync and async)
- [x] Scheduled agent behaviors (proactive inbox, task execution, knowledge review)
- [x] Structured reasoning engine with decision graphs
- [x] Memory consolidation and intelligent recall
- [x] Autonomous runner framework with Docker sandboxing
- [x] Deep research with web scraping and YouTube transcripts
- [x] Skills system (brainstorming, code review, debugging, decision analysis, etc.)
- [x] Organization templates (Startup, Student, Job Hunt, Family, Creator)
- [x] Task, issue, and approval management
- [x] Google Calendar and Linear integrations
- [ ] RAG over uploaded documents and codebases
- [ ] Mobile companion app
- [ ] Multi-user collaboration with role-based access
- [ ] One-click cloud deploy templates (Railway, Fly.io)
- [ ] Webhook triggers for external event-driven advice

---

## Contributing

We welcome contributions of all kinds. See [**CONTRIBUTING.md**](CONTRIBUTING.md) for guidelines on getting started, code style, and the PR process.

Before opening a large PR, please open an issue or discussion first so we can align on approach.

---

## Community

- **Website** — [useaxon.dev](https://useaxon.dev) for docs, blog, and getting started guides
- **Discord** — [Join the server](https://discord.gg/axon) for support, feature discussions, and showcases
- **GitHub Discussions** — [Ask questions and share ideas](https://github.com/brandonkorous/axon/discussions)
- **Twitter / X** — Follow [@axon_ai](https://twitter.com/axon_ai) for updates

---

## License

Axon is licensed under the [**GNU Affero General Public License v3.0 (AGPL-3.0)**](LICENSE).

You are free to use, modify, and self-host Axon. If you distribute a modified version or run it as a network service, you must make your source code available under the same license.

---

<p align="center">
  Built with ❤️ by the Axon community
</p>

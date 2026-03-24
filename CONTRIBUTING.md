# Contributing to Axon

Welcome, and thanks for your interest in contributing to Axon. Whether you're fixing a bug, adding a feature, or improving documentation, your contribution matters.

This guide covers the process for contributing to the project. If you have questions that aren't answered here, open a discussion or reach out in an issue.

## Table of Contents

- [Development Setup](#development-setup)
- [Running the Stack](#running-the-stack)
- [Code Style](#code-style)
- [Pull Request Process](#pull-request-process)
- [Commit Messages](#commit-messages)
- [Reporting Issues](#reporting-issues)
- [Code of Conduct](#code-of-conduct)

## Development Setup

1. Fork and clone the repository:

   ```bash
   git clone https://github.com/<your-username>/axon.git
   cd axon
   ```

2. Copy the environment template and configure your API keys:

   ```bash
   cp .env.example .env
   ```

   Open `.env` and fill in the required values. At minimum you'll need your LLM provider API keys. See the README for details on each variable.

## Running the Stack

### Frontend only

Requires **Node.js 20+**.

```bash
cd frontend
npm install
npm run dev
```

The dev server starts at **http://localhost:5173**.

### Backend only

Requires **Python 3.11+**.

```bash
cd backend
pip install -e .
python -m axon
```

The API server starts at **http://localhost:8000**.

### Full stack (Docker)

The simplest way to run everything together:

```bash
docker compose up
```

This starts the frontend, backend, and all supporting services defined in `docker-compose.yml`.

## Code Style

These aren't arbitrary rules. They exist to keep the codebase navigable as it grows.

- **Max 200 lines per file.** If a file is growing past this, it's doing too much. Split it.
- **Single responsibility.** Each module, component, and function should do one thing well.
- **No unused code.** Dead imports, commented-out blocks, and unreachable branches get removed, not kept "just in case."
- **No circular dependencies.** If module A imports from B and B imports from A, restructure.
- **Tests live next to code.** Place test files alongside the modules they test (e.g., `parser.ts` and `parser.test.ts` in the same directory).

Frontend code follows the project ESLint and Prettier configs. Backend code follows Ruff defaults. Run linters before pushing.

## Pull Request Process

1. **Fork** the repository and create a feature branch from `main`:

   ```bash
   git checkout -b feat/your-feature main
   ```

2. Make your changes. Keep commits focused and atomic.

3. Ensure tests pass and linters are clean.

4. **Push** your branch and open a pull request against `main`.

5. Fill out the PR template. Describe *what* changed and *why*.

6. A maintainer will review your PR. Expect feedback, and don't take it personally. We review code, not people.

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <short summary>

<optional body>
```

Common types:

| Type       | When to use                          |
| ---------- | ------------------------------------ |
| `feat`     | New feature                          |
| `fix`      | Bug fix                              |
| `docs`     | Documentation only                   |
| `refactor` | Code change that doesn't fix or add  |
| `test`     | Adding or updating tests             |
| `chore`    | Build, CI, tooling, dependencies     |

Examples:

```
feat(memory): add neural tree pruning strategy
fix(api): handle missing auth header gracefully
docs: update contributing guide
```

## Reporting Issues

Good bug reports save everyone time. When filing an issue:

- **Search first.** Your issue may already be tracked.
- **Use the issue template** if one exists.
- **Include reproduction steps.** Minimum viable reproduction is ideal.
- **Specify your environment.** OS, Node/Python versions, Docker version if applicable.
- **Attach logs or screenshots** when relevant.

Feature requests are welcome. Describe the problem you're trying to solve, not just the solution you have in mind.

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold its standards. Report unacceptable behavior to the contact listed in that document.

---

Thanks for contributing.

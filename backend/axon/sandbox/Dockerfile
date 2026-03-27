# Axon Sandbox — isolated execution environment for worker agents.
#
# Provides Node.js, Playwright + Chromium, Python, and basic shell tools
# in a constrained container with resource limits and network policies.
#
# Build:   docker build -t axon-sandbox:latest -f backend/axon/sandbox/Dockerfile .
# Usage:   Managed by SandboxManager — not intended for manual invocation.

FROM node:20-slim AS base

# System dependencies for Playwright/Chromium + general tooling
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip \
    git curl wget ca-certificates \
    # Playwright Chromium deps
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
    libpango-1.0-0 libasound2 libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright + Chromium
RUN npx playwright install chromium --with-deps 2>/dev/null || true

# Create non-root sandbox user
RUN groupadd -r sandbox && useradd -r -g sandbox -m -s /bin/bash sandbox

# Workspace volume mount point
RUN mkdir -p /workspace /runner && chown sandbox:sandbox /workspace /runner

WORKDIR /runner

# Runner files are mounted at /runner via volume
# Workspace files are mounted at /workspace via volume

USER sandbox

# Health check — runner.js writes a heartbeat file
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD test -f /runner/.heartbeat && \
        [ $(($(date +%s) - $(stat -c %Y /runner/.heartbeat 2>/dev/null || echo 0))) -lt 60 ]

CMD ["node", "runner.js"]

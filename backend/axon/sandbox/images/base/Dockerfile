# axon-sandbox-base — Foundation layer for all Axon sandbox environments.
#
# Provides: bash, curl, git, jq, wget, ca-certificates, bun
# Target size: ~80MB
# Build: docker build -t axon-sandbox-base:latest .

FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    curl \
    git \
    jq \
    ca-certificates \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Bun (replaces Node.js — faster startup, native TS support)
RUN curl -fsSL https://bun.sh/install | bash \
    && mv /root/.bun/bin/bun /usr/local/bin/ \
    && ln -s /usr/local/bin/bun /usr/local/bin/bunx \
    && rm -rf /root/.bun

# Create non-root sandbox user
RUN groupadd -r sandbox && useradd -r -g sandbox -m -s /bin/bash sandbox

# Create workspace and runner directories
RUN mkdir -p /workspace /runner && chown sandbox:sandbox /workspace /runner

WORKDIR /runner

USER sandbox

# Health check — runner writes a heartbeat file periodically
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD test -f /runner/.heartbeat && \
        [ $(($(date +%s) - $(stat -c %Y /runner/.heartbeat 2>/dev/null || echo 0))) -lt 60 ]

CMD ["bash"]

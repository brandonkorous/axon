# axon-sandbox-code — General-purpose code execution sandbox.
#
# Inherits: base (Bun included)
# Provides: Python 3, uv (fast package manager)
# Target size: ~200MB
# Build: docker build -t axon-sandbox-code:latest .

ARG BASE_IMAGE=axon-sandbox-base:latest
FROM ${BASE_IMAGE}

USER root

# Install Python 3 (no pip — uv replaces it)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-venv \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3 /usr/bin/python

# Install uv (replaces pip — 10-100x faster installs)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv /root/.local/bin/uv /usr/local/bin/ \
    && mv /root/.local/bin/uvx /usr/local/bin/ \
    && rm -rf /root/.local

USER sandbox

CMD ["bun", "run", "/runner/runner.js"]

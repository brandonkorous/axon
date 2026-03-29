# axon-sandbox-browser — Browser automation sandbox with Playwright + Chromium.
#
# Inherits: base (Bun included)
# Provides: Playwright, Chromium
# Target size: ~500MB
# Build: docker build -t axon-sandbox-browser:latest .

FROM axon-sandbox-base:latest

USER root

# Install Playwright Chromium dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libasound2 \
    libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright and Chromium browser
RUN bunx playwright install chromium --with-deps 2>/dev/null || true

USER sandbox

CMD ["bun", "run", "/runner/runner.js"]

# axon-sandbox-full — Kitchen-sink sandbox with all capabilities.
#
# Inherits: base (Bun included; installs everything directly since it cannot
#           inherit from siblings)
# Provides: Python, uv, Playwright+Chromium, data science stack, PyTorch,
#           transformers, pandoc, texlive, LibreOffice, ffmpeg, ImageMagick, sharp
# Target size: ~1.5GB
# Build: docker build -t axon-sandbox-full:latest .

FROM axon-sandbox-base:latest

USER root

# --- Python 3 (no pip — uv replaces it) ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# --- uv (replaces pip — 10-100x faster installs) ---
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv /root/.local/bin/uv /usr/local/bin/ \
    && mv /root/.local/bin/uvx /usr/local/bin/ \
    && rm -rf /root/.local

# --- Playwright Chromium dependencies ---
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

RUN bunx playwright install chromium --with-deps 2>/dev/null || true

# --- Data science + ML Python packages ---
RUN uv pip install --system \
    pandas \
    numpy \
    matplotlib \
    scipy \
    jupyterlab

RUN uv pip install --system \
    torch --index-url https://download.pytorch.org/whl/cpu \
    && uv pip install --system \
    scikit-learn \
    transformers \
    onnxruntime

# --- Document tools ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    pandoc \
    texlive-base \
    texlive-latex-recommended \
    wkhtmltopdf \
    libreoffice \
    && rm -rf /var/lib/apt/lists/*

# --- Media tools ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

RUN bun install -g sharp-cli

USER sandbox

CMD ["bun", "run", "/runner/runner.js"]

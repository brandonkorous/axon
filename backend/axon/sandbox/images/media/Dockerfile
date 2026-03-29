# axon-sandbox-media — Audio/video/image processing sandbox.
#
# Inherits: base (Bun included)
# Provides: ffmpeg, ImageMagick, sharp-cli
# Target size: ~180MB
# Build: docker build -t axon-sandbox-media:latest .

FROM axon-sandbox-base:latest

USER root

# Install media tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

# Install sharp-cli via Bun
RUN bun install -g sharp-cli

USER sandbox

CMD ["bun", "run", "/runner/runner.js"]

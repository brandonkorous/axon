# axon-sandbox-documents — Document conversion and generation sandbox.
#
# Inherits: code (Bun + uv + Python included)
# Provides: pandoc, texlive, wkhtmltopdf, LibreOffice
# Target size: ~500MB
# Build: docker build -t axon-sandbox-documents:latest .

FROM axon-sandbox-code:latest

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    pandoc \
    texlive-base \
    texlive-latex-recommended \
    wkhtmltopdf \
    libreoffice \
    && rm -rf /var/lib/apt/lists/*

USER sandbox

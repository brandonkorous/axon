# axon-sandbox-documents — Document conversion and generation sandbox.
#
# Inherits: code (Bun + uv + Python included)
# Provides: pandoc, texlive, wkhtmltopdf, LibreOffice
# Target size: ~500MB
# Build: docker build -t axon-sandbox-documents:latest .

ARG BASE_IMAGE=axon-sandbox-code:latest
FROM ${BASE_IMAGE}

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    pandoc \
    texlive-base \
    texlive-latex-recommended \
    wkhtmltopdf \
    libreoffice \
    && rm -rf /var/lib/apt/lists/*

USER sandbox

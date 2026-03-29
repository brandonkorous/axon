# axon-sandbox-data — Data science sandbox with scientific Python stack.
#
# Inherits: code (Bun + uv + Python included)
# Provides: pandas, numpy, matplotlib, scipy, jupyterlab
# Target size: ~350MB
# Build: docker build -t axon-sandbox-data:latest .

ARG BASE_IMAGE=axon-sandbox-code:latest
FROM ${BASE_IMAGE}

USER root

ENV VIRTUAL_ENV=/opt/venv
RUN uv venv $VIRTUAL_ENV && uv pip install \
    pandas \
    numpy \
    matplotlib \
    scipy \
    jupyterlab
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

USER sandbox

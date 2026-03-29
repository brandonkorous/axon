# axon-sandbox-ml — Machine learning sandbox with PyTorch and transformers.
#
# Inherits: data (Bun + uv + Python + data science stack included)
# Provides: PyTorch (CPU), scikit-learn, transformers, onnxruntime
# Target size: ~800MB
# Build: docker build -t axon-sandbox-ml:latest .

ARG BASE_IMAGE=axon-sandbox-data:latest
FROM ${BASE_IMAGE}

USER root

RUN uv pip install --system \
    torch --index-url https://download.pytorch.org/whl/cpu \
    && uv pip install --system \
    scikit-learn \
    transformers \
    onnxruntime

USER sandbox

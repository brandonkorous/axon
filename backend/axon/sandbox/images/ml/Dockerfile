# axon-sandbox-ml — Machine learning sandbox with PyTorch and transformers.
#
# Inherits: data (Bun + uv + Python + data science stack included)
# Provides: PyTorch (CPU), scikit-learn, transformers, onnxruntime
# Target size: ~800MB
# Build: docker build -t axon-sandbox-ml:latest .

FROM axon-sandbox-data:latest

USER root

RUN uv pip install --system \
    torch --index-url https://download.pytorch.org/whl/cpu \
    && uv pip install --system \
    scikit-learn \
    transformers \
    onnxruntime

USER sandbox

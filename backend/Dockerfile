FROM python:3.12-slim

WORKDIR /app

# Install CPU-only PyTorch first to avoid pulling ~5GB of NVIDIA/CUDA packages
RUN pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# Copy source and install
COPY backend/pyproject.toml .
COPY backend/axon/ axon/
COPY backend/models/ models/
COPY VERSION .
RUN pip install --no-cache-dir ".[voice,sandbox,kubernetes]"

EXPOSE 8000

# Production default: pull pre-built sandbox images from registry
ENV AXON_SANDBOX_IMAGE_SOURCE=registry

CMD ["uvicorn", "axon.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

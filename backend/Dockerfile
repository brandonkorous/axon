FROM python:3.12-slim

WORKDIR /app

# Install CPU-only PyTorch first to avoid pulling ~5GB of NVIDIA/CUDA packages
RUN pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# Copy source and install
COPY pyproject.toml .
COPY axon/ axon/
COPY models/ models/
RUN pip install --no-cache-dir ".[voice]"

EXPOSE 8000

CMD ["uvicorn", "axon.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

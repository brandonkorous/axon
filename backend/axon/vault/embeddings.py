"""Embedding client — wraps sentence-transformers for vault vector search.

The model is loaded lazily on first use and cached for subsequent calls.
All encoding runs in a thread pool to avoid blocking the async event loop.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from axon.logging import get_logger

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

logger = get_logger(__name__)

# Module-level singleton — shared across all agents in the process
_model: SentenceTransformer | None = None
_model_name: str = ""


def _get_model(model_name: str) -> SentenceTransformer:
    """Load or return the cached sentence-transformers model."""
    global _model, _model_name
    if _model is not None and _model_name == model_name:
        return _model

    from sentence_transformers import SentenceTransformer

    logger.info("loading_embedding_model", model=model_name)
    _model = SentenceTransformer(model_name)
    _model_name = model_name
    return _model


class EmbeddingClient:
    """Async-friendly wrapper around sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model_name = model_name

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Encode a batch of texts into embedding vectors."""
        if not texts:
            return []
        return await asyncio.to_thread(self._encode, texts)

    async def embed_one(self, text: str) -> list[float]:
        """Encode a single text into an embedding vector."""
        results = await self.embed([text])
        return results[0]

    def _encode(self, texts: list[str]) -> list[list[float]]:
        model = _get_model(self.model_name)
        embeddings = model.encode(texts, normalize_embeddings=True)
        return [e.tolist() for e in embeddings]

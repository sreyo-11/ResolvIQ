from functools import lru_cache

import numpy as np
from fastembed import TextEmbedding

from app.core.config import settings


class Embedder:
    """Thin wrapper over an ONNX embedding model (CPU, ~250 MB RAM)."""

    def __init__(self, model_name: str, cache_dir: str, expected_dim: int):
        self._model = TextEmbedding(model_name=model_name, cache_dir=cache_dir)
        self.dim = expected_dim

    def embed_text(self, text: str) -> np.ndarray:
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str], batch_size: int = 64) -> list[np.ndarray]:
        vectors = [np.asarray(v, dtype=np.float32) for v in self._model.embed(texts, batch_size=batch_size)]
        for v in vectors:
            if v.shape[0] != self.dim:  # never mix dimensions
                raise ValueError(f"Expected {self.dim}-dim embeddings, got {v.shape[0]}")
        return vectors


@lru_cache
def get_embedder() -> Embedder:
    """Lazy singleton: model loads on first use, not at import/boot."""
    return Embedder(settings.embedding_model, settings.embedding_cache_dir, settings.embedding_dim)


def build_ticket_text(subject: str, body: str) -> str:
    return f"{subject}\n{body}"
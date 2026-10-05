import numpy as np
import pytest

from app.services.embeddings import get_embedder


@pytest.mark.slow
def test_dimension_and_semantic_ordering():
    emb = get_embedder()
    a, b, c = emb.embed_batch([
        "I was charged twice for my subscription",
        "duplicate payment on my card",
        "my package has not arrived",
    ])
    assert a.shape == (384,)
    cos = lambda x, y: float(np.dot(x, y) / (np.linalg.norm(x) * np.linalg.norm(y)))  # noqa: E731
    assert cos(a, b) > cos(a, c)
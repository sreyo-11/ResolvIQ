import numpy as np
from pgvector import Vector

from app.services.clustering import (
    _embedding_matrix,
    find_clusters,
    jaccard,
    normalize,
    trend_score,
)


def test_embedding_matrix_converts_pgvector_values():
    rows = [{"embedding": Vector([1.0, 2.0])}, {"embedding": Vector([3.0, 4.0])}]

    matrix = _embedding_matrix(rows)

    np.testing.assert_array_equal(matrix, [[1.0, 2.0], [3.0, 4.0]])
    assert np.issubdtype(matrix.dtype, np.number)


def test_finds_two_separated_blobs():
    rng = np.random.default_rng(0)
    a = np.eye(8)[0] + 0.02 * rng.standard_normal((30, 8))
    b = np.eye(8)[1] + 0.02 * rng.standard_normal((30, 8))
    noise = rng.standard_normal((5, 8))
    clusters = find_clusters(normalize(np.vstack([a, b, noise])), min_cluster_size=5, min_samples=3)
    assert len(clusters) == 2


def test_trend_score_and_jaccard():
    assert trend_score(70, 0) == 70
    assert trend_score(10, 10) == 0
    assert jaccard({1, 2, 3}, {2, 3, 4}) == 0.5
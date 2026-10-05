import numpy as np
import psycopg


def search(conn: psycopg.Connection, embedding: np.ndarray, k: int, min_similarity: float):
    return conn.execute(
        "select chunk_id, article_id, article_title, content, similarity "
        "from match_kb_chunks(%s::vector, %s::int, %s::float)",
        (embedding, k, min_similarity),
    ).fetchall()
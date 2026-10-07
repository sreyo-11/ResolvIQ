"""Embed every KB chunk and ticket that has no embedding yet.

Usage (from backend/):  python -m scripts.embed_backfill
"""
import time

import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row

from app.core.config import settings
from app.services.embeddings import get_embedder

JOBS = [
    (
        "kb_chunks",
        "select c.id, a.title || chr(10) || c.content as text from kb_chunks c "
        "join kb_articles a on a.id = c.article_id where c.embedding is null",
        "update kb_chunks set embedding = %s where id = %s",
    ),
    (
        "tickets",
        "select id, subject || chr(10) || body as text from tickets where embedding is null",
        "update tickets set embedding = %s where id = %s",
    ),
]


def run_job(conn, embedder, name: str, select_sql: str, update_sql: str, batch: int = 64) -> None:
    rows = conn.execute(select_sql).fetchall()
    print(f"[{name}] {len(rows)} rows to embed")
    t0 = time.time()
    for i in range(0, len(rows), batch):
        part = rows[i:i + batch]
        vectors = embedder.embed_batch([r["text"] for r in part], batch_size=batch)
        with conn.cursor() as cur:
            cur.executemany(update_sql, [(v, r["id"]) for v, r in zip(vectors, part,strict=True)])
        conn.commit()  # commit per batch -> resumable
        print(f"  {min(i + batch, len(rows))}/{len(rows)}")
    print(f"[{name}] done in {time.time() - t0:.1f}s")


def main() -> None:
    embedder = get_embedder()
    with psycopg.connect(settings.database_url, row_factory=dict_row, prepare_threshold=None) as conn:
        register_vector(conn)
        for name, select_sql, update_sql in JOBS:
            run_job(conn, embedder, name, select_sql, update_sql)


if __name__ == "__main__":
    main()
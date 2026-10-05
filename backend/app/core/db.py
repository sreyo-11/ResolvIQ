from collections.abc import Iterator

import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.core.config import settings

_pool: ConnectionPool | None = None


def _configure(conn: psycopg.Connection) -> None:
    register_vector(conn)  # lets us pass numpy arrays as `vector` params
    conn.commit()


def open_pool() -> None:
    global _pool
    _pool = ConnectionPool(
        settings.database_url,
        min_size=settings.db_pool_min,
        max_size=settings.db_pool_max,
        max_idle=300,
        # prepare_threshold=None is required for Supabase's transaction pooler (port 6543)
        kwargs={"row_factory": dict_row, "prepare_threshold": None},
        configure=_configure,
        check=ConnectionPool.check_connection,  # drop stale connections after idle/sleep
        open=False,
    )
    _pool.open(wait=True, timeout=30)


def close_pool() -> None:
    if _pool:
        _pool.close()


def get_pool() -> ConnectionPool:
    if _pool is None:
        raise RuntimeError("DB pool is not initialised")
    return _pool


def get_conn() -> Iterator[psycopg.Connection]:
    """FastAPI dependency: one pooled connection per request."""
    with get_pool().connection() as conn:
        yield conn
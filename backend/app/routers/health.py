from typing import Annotated

import psycopg
from fastapi import APIRouter, Depends, HTTPException

from app.core.db import get_conn

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    """Liveness: no DB access, safe for uptime pings."""
    return {"status": "ok"}


@router.get("/health/ready")
def ready(conn: Annotated[psycopg.Connection, Depends(get_conn)]) -> dict:
    try:
        conn.execute("select 1")
    except Exception as exc:
        raise HTTPException(status_code=503, detail="database unavailable") from exc
    return {"status": "ready"}
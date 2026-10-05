from typing import Annotated

import psycopg
from fastapi import APIRouter, Depends, Query

from app.core.db import get_conn
from app.repositories import kb_repo
from app.schemas.kb import KbHit
from app.services.embeddings import Embedder, get_embedder

router = APIRouter(prefix="/kb", tags=["knowledge-base"])
Conn = Annotated[psycopg.Connection, Depends(get_conn)]
EmbedderDep = Annotated[Embedder, Depends(get_embedder)]


@router.get("/search", response_model=list[KbHit])
def search_kb(
    conn: Conn,
    embedder: EmbedderDep,
    q: Annotated[str, Query(min_length=3, max_length=500)],
    k: Annotated[int, Query(ge=1, le=10)] = 5,
    min_similarity: Annotated[float, Query(ge=0, le=1)] = 0.2,
):
    return kb_repo.search(conn, embedder.embed_text(q), k, min_similarity)
from typing import Annotated
from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends

from app.core.db import get_conn
from app.repositories import reply_repo
from app.schemas.reply import DraftOut, ReplyOut, ReplyUpdate
from app.services import rag, reply_service

router = APIRouter(tags=["replies"])
Conn = Annotated[psycopg.Connection, Depends(get_conn)]


@router.post("/tickets/{ticket_id}/draft-reply", response_model=DraftOut)
def draft_reply(ticket_id: UUID, conn: Conn):
    r = rag.draft_reply(conn, ticket_id)
    return DraftOut(drafted=r.drafted, reason=r.reason, top_similarity=r.top_similarity, reply=r.reply)


@router.get("/tickets/{ticket_id}/replies", response_model=list[ReplyOut])
def list_replies(ticket_id: UUID, conn: Conn):
    return reply_repo.list_for_ticket(conn, ticket_id)


@router.patch("/replies/{reply_id}", response_model=ReplyOut)
def review_reply(reply_id: UUID, patch: ReplyUpdate, conn: Conn):
    return reply_service.review_reply(conn, reply_id, patch)
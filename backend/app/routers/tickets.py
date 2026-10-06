from typing import Annotated
from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from app.core.config import settings
from app.services import pipeline, ticket_service, triage_service

from app.core.db import get_conn
from app.schemas.ticket import (
    Category,
    Priority,
    Status,
    TicketCreate,
    TicketOut,
    TicketPage,
    TicketUpdate,
)
from app.services import ticket_service
from app.services.embeddings import Embedder, get_embedder
from app.services import extraction

router = APIRouter(prefix="/tickets", tags=["tickets"])
Conn = Annotated[psycopg.Connection, Depends(get_conn)]
EmbedderDep = Annotated[Embedder, Depends(get_embedder)]

@router.post("", response_model=TicketOut, status_code=201)
def create_ticket(data: TicketCreate, conn: Conn, embedder: EmbedderDep):
    return ticket_service.create_ticket(conn, data, embedder)


@router.get("", response_model=TicketPage)
def list_tickets(
    conn: Conn,
    status: Status | None = None,
    category: Category | None = None,
    priority: Priority | None = None,
    team: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    filters = {"status": status, "category": category, "priority": priority, "team": team}
    items, total = ticket_service.list_tickets(conn, filters, limit, offset)
    return TicketPage(items=items, total=total, limit=limit, offset=offset)


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: UUID, conn: Conn):
    return ticket_service.get_ticket(conn, ticket_id)


@router.patch("/{ticket_id}", response_model=TicketOut)
def update_ticket(ticket_id: UUID, patch: TicketUpdate, conn: Conn):
    return ticket_service.update_ticket(conn, ticket_id, patch)

@router.post("", response_model=TicketOut, status_code=201)
def create_ticket(data: TicketCreate, conn: Conn, embedder: EmbedderDep, background: BackgroundTasks):
    ticket = ticket_service.create_ticket(conn, data, embedder)
    ticket = triage_service.triage_ticket(conn, ticket["id"])
    if settings.auto_enrich:
        background.add_task(pipeline.enrich_ticket, ticket["id"])
    return ticket


@router.post("/{ticket_id}/classify", response_model=TicketOut)
def classify_ticket(ticket_id: UUID, conn: Conn):
    """Re-run triage, for example after an agent edits the ticket text."""
    return triage_service.triage_ticket(conn, ticket_id)

@router.post("/{ticket_id}/extract", response_model=TicketOut)
def extract_ticket(ticket_id: UUID, conn: Conn):
    return extraction.run_extraction(conn, ticket_id)
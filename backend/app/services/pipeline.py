import logging
from uuid import UUID

from app.core.config import settings
from app.core.db import get_pool
from app.services import extraction, rag, sla_service

log = logging.getLogger(__name__)

def _extract(conn, ticket_id):
    extraction.run_extraction(conn, ticket_id)


def _draft(conn, ticket_id):
    if settings.auto_draft:
        rag.draft_reply(conn, ticket_id)

def _sla(conn, ticket_id):
    sla_service.score_ticket(conn, ticket_id)

_STAGES: list[tuple[str, callable]] = [("sla", _sla),("extract", _extract), ("draft", _draft)]#(name,fn(conn,ticket_id))


def enrich_ticket(ticket_id: UUID) -> None:
    """Background pipeline, runs after the HTTP response. Each stage is isolated, so one failure
    (for example an LLM rate limit) never blocks the others."""
    with get_pool().connection() as conn:  # own connection: the request's one is already returned
        for name, stage in _STAGES:
            try:
                stage(conn, ticket_id)
            except Exception:
                conn.rollback()
                log.exception("pipeline stage '%s' failed for ticket %s", name, ticket_id)
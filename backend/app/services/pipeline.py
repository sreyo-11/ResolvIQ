import logging
from uuid import UUID

from app.core.db import get_pool

log = logging.getLogger(__name__)

_STAGES: list[tuple[str, callable]] = []  # (name, fn(conn, ticket_id))


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
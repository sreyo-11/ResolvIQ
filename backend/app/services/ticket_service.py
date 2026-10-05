from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import psycopg

from app.core.errors import InvalidTransitionError, NotFoundError
from app.repositories import ticket_repo
from app.schemas.ticket import TicketCreate, TicketUpdate

# Lifecycle: new -> classified -> assigned -> in_progress -> resolved -> closed
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "new": {"classified", "assigned", "in_progress"},
    "classified": {"assigned", "in_progress"},
    "assigned": {"in_progress", "resolved"},
    "in_progress": {"resolved"},
    "resolved": {"closed", "in_progress"},  # in_progress = reopen
    "closed": set(),
}


def can_transition(current: str, new: str) -> bool:
    return new in ALLOWED_TRANSITIONS.get(current, set())


def create_ticket(conn: psycopg.Connection, data: TicketCreate) -> dict:
    queue_length = ticket_repo.count_open(conn)  # real feature for the SLA model later
    row = ticket_repo.insert(
        conn,
        subject=data.subject.strip(),
        body=data.body.strip(),
        customer_email=data.customer_email.lower(),
        queue_length=queue_length,
    )
    conn.commit()
    return row


def get_ticket(conn: psycopg.Connection, ticket_id: UUID) -> dict:
    row = ticket_repo.get(conn, ticket_id)
    if not row:
        raise NotFoundError(f"Ticket {ticket_id} not found")
    return row


def list_tickets(conn: psycopg.Connection, filters: dict[str, Any], limit: int, offset: int):
    return ticket_repo.list_page(conn, filters, limit, offset)


def update_ticket(conn: psycopg.Connection, ticket_id: UUID, patch: TicketUpdate) -> dict:
    current = get_ticket(conn, ticket_id)
    changes = patch.model_dump(exclude_unset=True)
    new_status = changes.pop("status", None)

    if new_status and new_status != current["status"]:
        if not can_transition(current["status"], new_status):
            raise InvalidTransitionError(
                f"Cannot move ticket from '{current['status']}' to '{new_status}'"
            )
        now = datetime.now(timezone.utc)
        changes["status"] = new_status
        if new_status in ("in_progress", "resolved") and current["first_response_at"] is None:
            changes["first_response_at"] = now  # captured for SLA tracking
        if new_status == "resolved":
            changes["resolved_at"] = now
        if current["status"] == "resolved" and new_status == "in_progress":  # reopen
            changes["resolved_at"] = None
            changes["reopen_count"] = current["reopen_count"] + 1

    if not changes:
        return current
    row = ticket_repo.update(conn, ticket_id, changes)
    conn.commit()
    return row
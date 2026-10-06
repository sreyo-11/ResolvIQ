from datetime import datetime, timezone

import psycopg

from app.core.errors import InvalidTransitionError, NotFoundError
from app.repositories import reply_repo
from app.schemas.reply import ReplyUpdate
from app.schemas.ticket import TicketUpdate
from app.services import ticket_service

ALLOWED = {"draft": {"approved", "rejected"}, "approved": {"sent"}}  # draft -> approved -> sent


def review_reply(conn: psycopg.Connection, reply_id, patch: ReplyUpdate) -> dict:
    reply = reply_repo.get(conn, reply_id)
    if not reply:
        raise NotFoundError(f"Reply {reply_id} not found")

    changes: dict = {}
    if patch.draft_text is not None:
        if reply["status"] != "draft":
            raise InvalidTransitionError("Only drafts can be edited")
        changes["draft_text"] = patch.draft_text.strip()
    if patch.status and patch.status != reply["status"]:
        if patch.status not in ALLOWED.get(reply["status"], set()):
            raise InvalidTransitionError(f"Cannot move reply from '{reply['status']}' to '{patch.status}'")
        changes["status"] = patch.status
        if patch.status == "approved":
            changes["approved_at"] = datetime.now(timezone.utc)

    row = reply_repo.update(conn, reply_id, changes) if changes else reply
    conn.commit()

    if changes.get("status") == "approved":  # agent responded -> start working the ticket
        ticket = ticket_service.get_ticket(conn, reply["ticket_id"])
        if ticket["status"] in ("new", "classified", "assigned"):
            ticket_service.update_ticket(conn, ticket["id"], TicketUpdate(status="in_progress"))
    return row
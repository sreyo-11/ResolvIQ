import logging
from uuid import UUID

import psycopg

from app.core.config import settings
from app.core.constants import CATEGORIES, PRIORITIES
from app.repositories import agent_repo, ticket_repo
from app.services import classifier, ticket_service
from app.services.embeddings import build_ticket_text, get_embedder
from app.services.llm_classifier import zero_shot_classify
from app.services.model_store import ModelUnavailable
from app.services.routing import route_ticket

log = logging.getLogger(__name__)


def triage_ticket(conn: psycopg.Connection, ticket_id: UUID) -> dict:
    ticket = ticket_service.get_ticket(conn, ticket_id)
    text = build_ticket_text(ticket["subject"], ticket["body"])
    embedding = ticket_repo.get_embedding(conn, ticket_id)
    if embedding is None:
        embedding = get_embedder().embed_text(text)

    try:
        pred = classifier.predict(text, embedding)
    except ModelUnavailable as exc:  # degrade gracefully instead of failing ticket creation
        log.warning("classifier unavailable: %s", exc)
        ticket_repo.update(conn, ticket_id, {"needs_human_triage": True})
        conn.commit()
        return ticket_service.get_ticket(conn, ticket_id)

    flags = classifier.low_confidence_flags(pred, settings.category_threshold, settings.priority_threshold)
    category, priority, by, needs_human = pred.category, pred.priority, "model", False

    if flags.any:  # cheap model is unsure -> ask the LLM; if that fails too -> human
        z = zero_shot_classify(ticket["subject"], ticket["body"])
        if flags.low_category:
            if z and z["category"] in CATEGORIES:
                category, by = z["category"], "llm"
            else:
                needs_human = True
        if flags.low_priority:
            if z and z["priority"] in PRIORITIES:
                priority, by = z["priority"], "llm"
            else:
                needs_human = True

    changes = {
        "category": category, "priority": priority,
        "classification_confidence": pred.category_conf,
        "priority_confidence": pred.priority_conf,
        "classified_by": by, "needs_human_triage": needs_human,
    }
    if ticket["status"] in ("new", "classified", "assigned"):  # (re)route only before work starts
        if ticket["assigned_agent_id"]:
            agent_repo.adjust_load(conn, ticket["assigned_agent_id"], -1)
        route = route_ticket(conn, category, needs_human)
        changes.update(
            team=route.team, assigned_agent_id=route.agent_id,
            agent_load_at_assignment=route.agent_load,
            status="assigned" if route.agent_id else "classified",  # system transition
        )
    ticket_repo.update(conn, ticket_id, changes)
    conn.commit()
    return ticket_service.get_ticket(conn, ticket_id)
from datetime import datetime, timezone
from uuid import UUID

import psycopg

from app.repositories import event_repo, ticket_repo
from app.services import sla, ticket_service
from app.services.model_store import load_bundle


def _level(p: float | None, thr: float) -> str | None:
    if p is None:
        return None
    return "breached" if p >= 1.0 else sla.risk_level(p, thr)


def _escalated(prev: str | None, new: str | None) -> bool:
    return new in ("high", "breached") and prev != new


def _event(t: dict, res: dict) -> tuple:
    return ("sla_risk", t["id"], {"subject": t["subject"], "priority": t["priority"],
                                  "probability": res["probability"], "level": res["level"]})


def score_ticket(conn: psycopg.Connection, ticket_id: UUID) -> dict | None:
    ticket = ticket_service.get_ticket(conn, ticket_id)
    res = sla.predict_risk(ticket)
    if res is None:
        return None
    thr = load_bundle("sla_model.joblib")["threshold"]
    now = datetime.now(timezone.utc)
    ticket_repo.update(conn, ticket_id, {"sla_risk": res["probability"], "sla_risk_updated_at": now})
    prev = ticket["sla_risk"]
    if prev is None or abs(res["probability"] - prev) >= 0.05:
        conn.execute(
            "insert into sla_predictions (ticket_id, breach_probability, model_version) values (%s,%s,%s)",
            (ticket_id, res["probability"], res["model_version"]))
    if _escalated(_level(prev, thr), res["level"]):
        event_repo.emit_many(conn, [_event(ticket, res)])
    conn.commit()
    return res


def rescore_open(conn: psycopg.Connection) -> int:
    thr = load_bundle("sla_model.joblib")["threshold"]
    now = datetime.now(timezone.utc)
    updates, history, events = [], [], []
    for t in ticket_repo.list_open_unanswered(conn):
        res = sla.predict_risk(t, now)
        if res is None:
            continue
        updates.append((res["probability"], now, t["id"]))
        if t["sla_risk"] is None or abs(res["probability"] - t["sla_risk"]) >= 0.05:
            history.append((t["id"], res["probability"], res["model_version"]))
        if _escalated(_level(t["sla_risk"], thr), res["level"]):
            events.append(_event(t, res))
    with conn.cursor() as cur:
        cur.executemany("update tickets set sla_risk = %s, sla_risk_updated_at = %s where id = %s", updates)
        cur.executemany(
            "insert into sla_predictions (ticket_id, breach_probability, model_version) values (%s,%s,%s)",
            history)
    event_repo.emit_many(conn, events)
    conn.commit()
    return len(updates)
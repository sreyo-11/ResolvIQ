from typing import Any
from uuid import UUID

import numpy as np
import psycopg

TICKET_COLUMNS = (
    "id, subject, body, customer_email, status, category, priority, team, assigned_agent_id, "
    "classification_confidence, priority_confidence, classified_by, needs_human_triage, "
    "extracted, sla_risk, sla_risk_updated_at, reopen_count, queue_length_at_creation, "
    "agent_load_at_assignment, created_at, first_response_at, resolved_at, updated_at"
)
UPDATABLE = {
    "status", "category", "priority", "team", "assigned_agent_id", "classification_confidence",
    "priority_confidence", "classified_by", "needs_human_triage", "extracted", "sla_risk",
    "sla_risk_updated_at", "agent_load_at_assignment", "first_response_at", "resolved_at",
    "reopen_count", "embedding",
}
FILTERABLE = ("status", "category", "priority", "team")

def count_open(conn: psycopg.Connection) -> int:
    row = conn.execute(
        "select count(*) as n from tickets "
        "where status in ('new','classified','assigned','in_progress')"
    ).fetchone()
    return row["n"]


def insert(conn: psycopg.Connection, *, subject: str, body: str, customer_email: str,
           queue_length: int, embedding=None) -> dict:
    return conn.execute(
        f"insert into tickets (subject, body, customer_email, queue_length_at_creation, embedding) "
        f"values (%s, %s, %s, %s, %s) returning {TICKET_COLUMNS}",
        (subject, body, customer_email, queue_length, embedding),
    ).fetchone()


def get(conn: psycopg.Connection, ticket_id: UUID) -> dict | None:
    return conn.execute(
        f"select {TICKET_COLUMNS} from tickets where id = %s", (ticket_id,)
    ).fetchone()


def list_page(conn: psycopg.Connection, filters: dict[str, Any], limit: int, offset: int):
    clauses, params = [], []
    for col in FILTERABLE:  # column names come from a fixed tuple, values are parameterised
        if filters.get(col):
            clauses.append(f"{col} = %s")
            params.append(filters[col])
    where = f"where {' and '.join(clauses)}" if clauses else ""
    total = conn.execute(f"select count(*) as n from tickets {where}", params).fetchone()["n"]
    items = conn.execute(
        f"select {TICKET_COLUMNS} from tickets {where} "
        f"order by created_at desc limit %s offset %s",
        [*params, limit, offset],
    ).fetchall()
    return items, total


def update(conn: psycopg.Connection, ticket_id: UUID, changes: dict[str, Any]) -> dict | None:
    cols = [c for c in changes if c in UPDATABLE]
    if not cols:
        raise ValueError("no updatable columns supplied")
    assignments = ", ".join(f"{c} = %s" for c in cols)
    return conn.execute(
        f"update tickets set {assignments} where id = %s returning {TICKET_COLUMNS}",
        [*[changes[c] for c in cols], ticket_id],
    ).fetchone()

def get_embedding(conn: psycopg.Connection, ticket_id: UUID) -> np.ndarray | None:
    row = conn.execute("select embedding from tickets where id = %s", (ticket_id,)).fetchone()
    return row["embedding"] if row else None


def list_open_unanswered(conn: psycopg.Connection) -> list[dict]:
    return conn.execute(
        f"select {TICKET_COLUMNS} from tickets where first_response_at is null "
        "and status in ('new','classified','assigned','in_progress') "
        "and priority is not null and category is not null"
    ).fetchall()

def list_by_cluster(conn: psycopg.Connection, cluster_id: UUID, limit: int) -> list[dict]:
    return conn.execute(
        f"select {TICKET_COLUMNS} from tickets where id in "
        "(select ticket_id from cluster_members where cluster_id = %s) "
        "order by created_at desc limit %s",
        (cluster_id, limit),
    ).fetchall()

def list_at_risk(conn: psycopg.Connection, min_risk: float, limit: int) -> list[dict]:
    return conn.execute(
        f"select {TICKET_COLUMNS} from tickets where sla_risk >= %s and first_response_at is null "
        "and status in ('new','classified','assigned','in_progress') order by sla_risk desc limit %s",
        (min_risk, limit),
    ).fetchall()
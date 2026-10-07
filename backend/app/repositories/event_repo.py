from psycopg.types.json import Jsonb

COLUMNS = "id, type, ticket_id, payload, created_at"


def ticket_payload(t: dict) -> dict:
    keys = ("subject", "category", "priority", "status", "team", "needs_human_triage")
    return {k: t.get(k) for k in keys}


def emit(conn, type_: str, ticket_id=None, payload: dict | None = None) -> None:
    """Transactional outbox: the event commits (or rolls back) together with the change."""
    conn.execute(
        "insert into events (type, ticket_id, payload) values (%s, %s, %s)",
        (type_, ticket_id, Jsonb(payload or {})),
    )


def emit_many(conn, rows: list[tuple]) -> None:  # rows: (type, ticket_id, payload)
    with conn.cursor() as cur:
        cur.executemany(
            "insert into events (type, ticket_id, payload) values (%s, %s, %s)",
            [(t, tid, Jsonb(p)) for t, tid, p in rows],
        )


def since(conn, after_id: int, limit: int = 200) -> list[dict]:
    return conn.execute(
        f"select {COLUMNS} from events where id > %s order by id limit %s", (after_id, limit)
    ).fetchall()


def recent(conn, limit: int = 30) -> list[dict]:
    return conn.execute(f"select {COLUMNS} from events order by id desc limit %s", (limit,)).fetchall()


def max_id(conn) -> int:
    return conn.execute("select coalesce(max(id), 0) as n from events").fetchone()["n"]


def prune(conn, hours: int) -> int:
    return conn.execute(
        "delete from events where created_at < now() - make_interval(hours => %s)", (hours,)
    ).rowcount
from psycopg.types.json import Jsonb

COLUMNS = "id, ticket_id, draft_text, sources, warnings, model, top_similarity, status, created_at, approved_at"


def insert(conn, *, ticket_id, draft_text, sources, warnings, model, top_similarity) -> dict:
    conn.execute(  # a new draft supersedes older unreviewed drafts
        "update replies set status = 'rejected' where ticket_id = %s and status = 'draft'", (ticket_id,)
    )
    return conn.execute(
        f"insert into replies (ticket_id, draft_text, sources, warnings, model, top_similarity) "
        f"values (%s,%s,%s,%s,%s,%s) returning {COLUMNS}",
        (ticket_id, draft_text, Jsonb(sources), Jsonb(warnings), model, top_similarity),
    ).fetchone()


def get(conn, reply_id) -> dict | None:
    return conn.execute(f"select {COLUMNS} from replies where id = %s", (reply_id,)).fetchone()


def list_for_ticket(conn, ticket_id) -> list[dict]:
    return conn.execute(
        f"select {COLUMNS} from replies where ticket_id = %s order by created_at desc", (ticket_id,)
    ).fetchall()


def update(conn, reply_id, changes: dict) -> dict:
    allowed = {"draft_text", "status", "approved_at"}
    cols = [c for c in changes if c in allowed]
    sets = ", ".join(f"{c} = %s" for c in cols)
    return conn.execute(
        f"update replies set {sets} where id = %s returning {COLUMNS}",
        [*[changes[c] for c in cols], reply_id],
    ).fetchone()
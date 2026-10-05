"""Load agents, KB articles/chunks and tickets (from CSV) into Supabase.

Usage (from backend/):
    python -m scripts.seed            # skips if tickets already exist
    python -m scripts.seed --reset    # wipe and reload
Embeddings are filled in Step 5 (scripts.embed_backfill).
"""
import argparse
import csv
from datetime import datetime
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from app.core.config import settings
from app.services.chunking import chunk_text
from scripts.constants import AGENTS
from scripts.kb_content import KB_ARTICLES

CSV_PATH = Path(__file__).resolve().parents[2] / "data" / "tickets_synthetic.csv"

INSERT_TICKET = """
insert into tickets (subject, body, customer_email, status, category, priority, team,
  assigned_agent_id, queue_length_at_creation, agent_load_at_assignment, reopen_count,
  created_at, first_response_at, resolved_at)
values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
"""


def dt(s: str):
    return datetime.fromisoformat(s) if s else None


def seed_agents(conn) -> dict[str, str]:
    for name, team in AGENTS:
        conn.execute(
            "insert into agents (name, team) values (%s, %s) on conflict (name) do nothing",
            (name, team),
        )
    return {r["name"]: r["id"] for r in conn.execute("select id, name from agents").fetchall()}


def seed_kb(conn) -> None:
    n_chunks = 0
    for a in KB_ARTICLES:
        art = conn.execute(
            "insert into kb_articles (title, category, content) values (%s,%s,%s) "
            "on conflict (title) do nothing returning id",
            (a["title"], a["category"], a["content"]),
        ).fetchone()
        if not art:
            continue
        for idx, chunk in enumerate(chunk_text(a["content"])):
            conn.execute(
                "insert into kb_chunks (article_id, chunk_index, content) values (%s,%s,%s)",
                (art["id"], idx, chunk),
            )
            n_chunks += 1
    print(f"KB: {len(KB_ARTICLES)} articles, {n_chunks} new chunks")


def seed_tickets(conn, agent_ids: dict[str, str]) -> None:
    with CSV_PATH.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    params = [
        (r["subject"], r["body"], r["customer_email"], r["status"], r["category"], r["priority"],
         r["team"], agent_ids.get(r["agent_name"]), int(r["queue_length_at_creation"]),
         int(r["agent_load_at_assignment"]) if r["agent_load_at_assignment"] else None,
         int(r["reopen_count"]), dt(r["created_at"]), dt(r["first_response_at"]),
         dt(r["resolved_at"]))
        for r in rows
    ]
    with conn.cursor() as cur:
        cur.executemany(INSERT_TICKET, params)
    conn.execute(
        "update agents a set current_load = (select count(*) from tickets t "
        "where t.assigned_agent_id = a.id and t.status in ('assigned','in_progress'))"
    )
    print(f"Tickets: inserted {len(params)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true")
    args = ap.parse_args()
    if not CSV_PATH.exists():
        raise SystemExit("Run `python -m scripts.generate_tickets` first.")

    with psycopg.connect(settings.database_url, row_factory=dict_row, prepare_threshold=None) as conn:
        if args.reset:
            conn.execute("truncate tickets, kb_articles, agents restart identity cascade")
        elif conn.execute("select count(*) as n from tickets").fetchone()["n"] > 0:
            print("Tickets already exist. Use --reset to reload.")
            return
        agent_ids = seed_agents(conn)
        seed_kb(conn)
        seed_tickets(conn, agent_ids)
        conn.commit()
    print("Seed complete.")


if __name__ == "__main__":
    main()
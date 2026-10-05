"""Apply pending .sql files from backend/migrations in order.

Usage (from backend/):  python -m scripts.migrate
"""
from pathlib import Path

import psycopg

from app.core.config import settings

MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"


def main() -> None:
    with psycopg.connect(settings.database_url, autocommit=True, prepare_threshold=None) as conn:
        conn.execute(
            "create table if not exists schema_migrations ("
            "filename text primary key, applied_at timestamptz not null default now())"
        )
        applied = {r[0] for r in conn.execute("select filename from schema_migrations").fetchall()}
        pending = [f for f in sorted(MIGRATIONS_DIR.glob("*.sql")) if f.name not in applied]
        if not pending:
            print("Database is up to date.")
            return
        for f in pending:
            print(f"Applying {f.name} ...")
            with conn.transaction():
                conn.execute(f.read_text(encoding="utf-8"))
                conn.execute("insert into schema_migrations (filename) values (%s)", (f.name,))
        print("Done.")


if __name__ == "__main__":
    main()
import hashlib

from app.core.db import standalone_connection


def is_test(subject: str, body: str) -> bool:
    """Deterministic ~20% test split. Keep identical to ml/finetune_distilbert.py."""
    digest = hashlib.md5(f"{subject}\n{body}".encode()).hexdigest()
    return int(digest, 16) % 5 == 0


def connect():
    return standalone_connection()


def load_labeled_tickets() -> list[dict]:
    """Ground-truth rows only: `classified_by is null` excludes tickets labelled by our own AI."""
    with connect() as conn:
        return conn.execute(
            "select subject, body, category, priority, embedding from tickets "
            "where embedding is not null and category is not null and priority is not null "
            "and classified_by is null"
        ).fetchall()
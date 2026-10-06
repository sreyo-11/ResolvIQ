import math
from datetime import datetime, timezone

from app.core.constants import CATEGORIES, PRIORITIES

FEATURE_NAMES = [
    "priority_rank", "hour", "dow", "is_weekend", "is_business_hours", "body_words",
    "subject_words", "queue_length", "agent_load", "elapsed_frac",
    *[f"cat_{c}" for c in CATEGORIES],
]


def feature_vector(*, priority: str, category: str, created_at: datetime, subject: str, body: str,
                   queue_length: int | None, agent_load: int | None, elapsed_frac: float) -> list[float]:
    t = created_at.astimezone(timezone.utc)
    return [
        float(PRIORITIES.index(priority)), float(t.hour), float(t.weekday()),
        float(t.weekday() >= 5), float(9 <= t.hour < 18), float(len(body.split())),
        float(len(subject.split())), float(queue_length or 0),
        math.nan if agent_load is None else float(agent_load),  # gradient boosting handles NaN natively
        float(elapsed_frac),
        *[float(category == c) for c in CATEGORIES],
    ]
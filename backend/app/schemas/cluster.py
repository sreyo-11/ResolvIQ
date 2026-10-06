from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.ticket import TicketOut


class ClusterOut(BaseModel):
    id: UUID
    title: str | None
    summary: str | None
    size: int
    prev_size: int
    trend_score: float
    is_trending: bool
    top_category: str | None
    window_start: datetime | None
    window_end: datetime | None
    created_at: datetime


class ClusterDetail(ClusterOut):
    tickets: list[TicketOut]
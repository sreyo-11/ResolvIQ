from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ReplyOut(BaseModel):
    id: UUID
    ticket_id: UUID
    draft_text: str
    sources: list[dict]
    warnings: list[str]
    model: str | None
    top_similarity: float | None
    status: Literal["draft", "approved", "sent", "rejected"]
    created_at: datetime
    approved_at: datetime | None


class DraftOut(BaseModel):
    drafted: bool
    reason: str | None = None  # why no draft was produced
    top_similarity: float | None = None
    reply: ReplyOut | None = None


class ReplyUpdate(BaseModel):
    draft_text: str | None = Field(default=None, min_length=1, max_length=3000)
    status: Literal["approved", "rejected", "sent"] | None = None
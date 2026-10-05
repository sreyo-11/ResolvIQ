from uuid import UUID

from pydantic import BaseModel


class KbHit(BaseModel):
    chunk_id: UUID
    article_id: UUID
    article_title: str
    content: str
    similarity: float
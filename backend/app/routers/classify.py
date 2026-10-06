from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.errors import ServiceUnavailableError
from app.services import classifier
from app.services.embeddings import Embedder, build_ticket_text, get_embedder
from app.services.model_store import ModelUnavailable

router = APIRouter(prefix="/classify", tags=["classification"])


class PreviewIn(BaseModel):
    subject: str = Field(min_length=3, max_length=200)
    body: str = Field(min_length=10, max_length=5000)


class PreviewOut(BaseModel):
    category: str
    category_confidence: float
    priority: str
    priority_confidence: float
    category_probs: dict[str, float]
    would_need_human_triage: bool


@router.post("/preview", response_model=PreviewOut)
def preview(data: PreviewIn, embedder: Annotated[Embedder, Depends(get_embedder)]):
    text = build_ticket_text(data.subject, data.body)
    try:
        pred = classifier.predict(text, embedder.embed_text(text))
    except ModelUnavailable as exc:
        raise ServiceUnavailableError(str(exc)) from exc
    flags = classifier.low_confidence_flags(pred, settings.category_threshold, settings.priority_threshold)
    return PreviewOut(
        category=pred.category, category_confidence=pred.category_conf,
        priority=pred.priority, priority_confidence=pred.priority_conf,
        category_probs=pred.category_probs, would_need_human_triage=flags.any,
    )
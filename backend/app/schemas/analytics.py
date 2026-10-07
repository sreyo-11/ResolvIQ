from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SummaryOut(BaseModel):
    open_tickets: int
    new_24h: int
    needs_triage: int
    at_risk: int
    sla_compliance_7d: float | None
    avg_first_response_min_7d: float | None
    trending_clusters: int


class VolumePoint(BaseModel):
    date: str
    total: int
    by_category: dict[str, int]


class NameValue(BaseModel):
    name: str
    value: int


class BreakdownOut(BaseModel):
    by_category: list[NameValue]
    by_priority: list[NameValue]
    by_status: list[NameValue]


class EventOut(BaseModel):
    id: int
    type: str
    ticket_id: UUID | None
    payload: dict
    created_at: datetime
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

Status = Literal["new", "classified", "assigned", "in_progress", "resolved", "closed"]
Category = Literal["billing", "account", "technical", "shipping", "integrations", "general"]
Priority = Literal["low", "medium", "high", "urgent"]


class TicketCreate(BaseModel):
    subject: str = Field(min_length=3, max_length=200)
    body: str = Field(min_length=10, max_length=5000)
    customer_email: EmailStr


class TicketUpdate(BaseModel):
    status: Status | None = None
    category: Category | None = None
    priority: Priority | None = None
    team: str | None = None
    assigned_agent_id: UUID | None = None


class TicketOut(BaseModel):
    id: UUID
    subject: str
    body: str
    customer_email: str
    status: Status
    category: Category | None
    priority: Priority | None
    team: str | None
    assigned_agent_id: UUID | None
    classification_confidence: float | None
    needs_human_triage: bool
    reopen_count: int
    queue_length_at_creation: int
    created_at: datetime
    first_response_at: datetime | None
    resolved_at: datetime | None
    updated_at: datetime
    priority_confidence: float | None = None
    classified_by: str | None = None
    extracted: dict = Field(default_factory=dict)
    sla_risk: float | None = None
    sla_risk_updated_at: datetime | None = None
    agent_load_at_assignment: int | None = None


class TicketPage(BaseModel):
    items: list[TicketOut]
    total: int
    limit: int
    offset: int
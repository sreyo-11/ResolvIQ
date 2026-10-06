from datetime import datetime

from pydantic import BaseModel


class SlaPoint(BaseModel):
    probability: float
    predicted_at: datetime


class SlaRiskOut(BaseModel):
    applicable: bool
    probability: float | None = None
    level: str | None = None  # low | medium | high | breached
    elapsed_fraction: float | None = None
    sla_limit_minutes: int | None = None
    model_version: str | None = None
    history: list[SlaPoint] = []
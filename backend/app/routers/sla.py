from typing import Annotated

import psycopg
from fastapi import APIRouter, Depends, Query

from app.core.db import get_conn
from app.core.errors import ServiceUnavailableError
from app.repositories import ticket_repo
from app.schemas.ticket import TicketOut
from app.services import sla_service
from app.services.model_store import ModelUnavailable

router = APIRouter(prefix="/sla", tags=["sla"])
Conn = Annotated[psycopg.Connection, Depends(get_conn)]


@router.get("/at-risk", response_model=list[TicketOut])
def at_risk(conn: Conn, min_risk: Annotated[float, Query(ge=0, le=1)] = 0.5,
            limit: Annotated[int, Query(ge=1, le=100)] = 20):
    return ticket_repo.list_at_risk(conn, min_risk, limit)


@router.post("/rescore")
def rescore(conn: Conn):
    try:
        return {"rescored": sla_service.rescore_open(conn)}
    except ModelUnavailable as exc:
        raise ServiceUnavailableError(str(exc)) from exc
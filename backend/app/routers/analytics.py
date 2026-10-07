from datetime import datetime, timezone
from typing import Annotated

import psycopg
from fastapi import APIRouter, Depends, Query

from app.core.db import get_conn
from app.repositories import analytics_repo
from app.schemas.analytics import BreakdownOut, SummaryOut, VolumePoint

router = APIRouter(prefix="/analytics", tags=["analytics"])
Conn = Annotated[psycopg.Connection, Depends(get_conn)]


@router.get("/summary", response_model=SummaryOut)
def summary(conn: Conn):
    return analytics_repo.summary(conn)


@router.get("/volume", response_model=list[VolumePoint])
def volume(conn: Conn, days: Annotated[int, Query(ge=1, le=90)] = 14):
    rows = analytics_repo.volume_rows(conn, days)
    return analytics_repo.fill_days(rows, days, datetime.now(timezone.utc).date())


@router.get("/breakdown", response_model=BreakdownOut)
def breakdown(conn: Conn, days: Annotated[int, Query(ge=1, le=90)] = 30):
    return analytics_repo.breakdown(conn, days)
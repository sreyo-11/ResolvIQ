from datetime import datetime
from typing import Annotated

import psycopg
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.db import get_conn

router = APIRouter(tags=["jobs"])
Conn = Annotated[psycopg.Connection, Depends(get_conn)]


class JobStatusOut(BaseModel):
    name: str
    status: str
    detail: dict
    started_at: datetime
    finished_at: datetime | None
    last_ok_at: datetime | None


@router.get("/jobs", response_model=list[JobStatusOut])
def job_status(conn: Conn):
    return conn.execute("""
        select distinct on (j.name) j.name, j.status, j.detail, j.started_at, j.finished_at,
               (select max(k.finished_at) from job_runs k where k.name = j.name and k.status = 'ok') as last_ok_at
        from job_runs j order by j.name, j.started_at desc
    """).fetchall()
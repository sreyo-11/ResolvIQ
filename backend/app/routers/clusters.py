from typing import Annotated
from uuid import UUID

import psycopg
from fastapi import APIRouter, BackgroundTasks, Depends, Query

from app.core.db import get_conn, get_pool
from app.core.errors import NotFoundError
from app.repositories import cluster_repo, ticket_repo
from app.schemas.cluster import ClusterDetail, ClusterOut
from app.services import clustering

router = APIRouter(prefix="/clusters", tags=["clusters"])
Conn = Annotated[psycopg.Connection, Depends(get_conn)]


def _refresh_job(days: int) -> None:
    with get_pool().connection() as conn:  # background task needs its own connection
        clustering.refresh_clusters(conn, days=days)


@router.get("", response_model=list[ClusterOut])
def list_clusters(conn: Conn, trending_only: bool = False,
                  limit: Annotated[int, Query(ge=1, le=100)] = 20):
    return cluster_repo.list_clusters(conn, trending_only, limit)


@router.post("/refresh", status_code=202)
def refresh(background: BackgroundTasks, days: Annotated[int, Query(ge=1, le=30)] = 7):
    background.add_task(_refresh_job, days)
    return {"status": "accepted", "days": days}


@router.get("/{cluster_id}", response_model=ClusterDetail)
def get_cluster(cluster_id: UUID, conn: Conn):
    cluster = cluster_repo.get(conn, cluster_id)
    if not cluster:
        raise NotFoundError(f"Cluster {cluster_id} not found")
    return {**cluster, "tickets": ticket_repo.list_by_cluster(conn, cluster_id, 10)}
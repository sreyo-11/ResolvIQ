"""Usage (from backend/):  python -m scripts.jobs rescore_sla | cluster | prune | all"""
import argparse
import logging
import sys
import time

from psycopg.types.json import Jsonb

from app.core.db import standalone_connection
from app.repositories import event_repo
from app.services import clustering, sla_service

log = logging.getLogger("jobs")


def job_rescore_sla(conn) -> dict:
    return {"rescored": sla_service.rescore_open(conn)}


def job_cluster(conn) -> dict:
    return clustering.refresh_clusters(conn, days=7)


def job_prune(conn) -> dict:
    events = event_repo.prune(conn, hours=48)
    runs = conn.execute("delete from job_runs where started_at < now() - interval '14 days'").rowcount
    conn.commit()
    return {"events_deleted": events, "job_runs_deleted": runs}


JOBS = {"rescore_sla": job_rescore_sla, "cluster": job_cluster, "prune": job_prune}


def run_job(name: str) -> int:
    with standalone_connection() as conn:
        run_id = conn.execute(
            "insert into job_runs (name, status) values (%s, 'running') returning id", (name,)
        ).fetchone()["id"]
        conn.commit()
        started = time.time()
        try:
            # transaction-level lock: released on commit/rollback, safe with Supabase poolers
            got = conn.execute("select pg_try_advisory_xact_lock(hashtext(%s)) as ok", (name,)).fetchone()["ok"]
            if got:
                status, detail = "ok", JOBS[name](conn)  # the job commits its own work
            else:
                status, detail = "skipped", {"reason": "another run holds the lock"}
        except Exception as exc:
            conn.rollback()
            log.exception("job %s failed", name)
            status, detail = "error", {"error": str(exc)[:500]}
        detail = {**detail, "seconds": round(time.time() - started, 1)}
        conn.execute(
            "update job_runs set status = %s, detail = %s, finished_at = now() where id = %s",
            (status, Jsonb(detail), run_id),
        )
        conn.commit()
    print(f"{name}: {status} {detail}")
    return 1 if status == "error" else 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ap = argparse.ArgumentParser()
    ap.add_argument("job", choices=[*JOBS, "all"])
    args = ap.parse_args()
    names = list(JOBS) if args.job == "all" else [args.job]
    sys.exit(max(run_job(n) for n in names))
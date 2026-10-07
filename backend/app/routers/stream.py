import asyncio
from typing import Annotated

import psycopg
from fastapi import APIRouter, Depends, Header, Query
from fastapi.responses import StreamingResponse

from app.core.db import get_conn, get_pool
from app.repositories import event_repo
from app.schemas.analytics import EventOut
from app.services.event_bus import bus, format_sse

router = APIRouter(tags=["realtime"])
Conn = Annotated[psycopg.Connection, Depends(get_conn)]


def _backlog(after_id: int) -> list[dict]:
    with get_pool().connection() as conn:
        return event_repo.since(conn, after_id, 100)


@router.get("/stream/events")
async def stream_events(last_event_id: Annotated[str | None, Header()] = None):
    """Server-Sent Events. Browsers reconnect automatically and send Last-Event-ID, so a client
    that was offline briefly receives what it missed."""
    try:
        last = int(last_event_id) if last_event_id else 0
    except ValueError:
        last = 0

    async def gen():
        nonlocal last
        queue = await bus.subscribe()
        try:
            yield "retry: 3000\n\n"
            if last:
                for ev in await asyncio.to_thread(_backlog, last):
                    last = ev["id"]
                    yield format_sse(ev)
            while True:
                try:
                    ev = await asyncio.wait_for(queue.get(), timeout=15)
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"  # keeps proxies from closing an idle connection
                    continue
                if ev["id"] > last:
                    last = ev["id"]
                    yield format_sse(ev)
        finally:  # runs when the client disconnects (task cancelled)
            bus.unsubscribe(queue)

    return StreamingResponse(
        gen(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/events/recent", response_model=list[EventOut])
def recent_events(conn: Conn, limit: Annotated[int, Query(ge=1, le=100)] = 30):
    return event_repo.recent(conn, limit)  # newest first; hydrates the activity feed on page load
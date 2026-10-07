import asyncio
import json
import logging
from collections import deque

from app.core.db import get_pool
from app.repositories import event_repo

log = logging.getLogger(__name__)
POLL_SECONDS = 2.0
REORDER_WINDOW = 20  # re-read the last N ids to catch rows that committed out of order


def format_sse(ev: dict) -> str:
    return f"id: {ev['id']}\ndata: {json.dumps(ev, default=str)}\n\n"


def _fetch(after_id: int) -> list[dict]:
    with get_pool().connection() as conn:
        return event_repo.since(conn, max(after_id, 0))


def _latest() -> int:
    with get_pool().connection() as conn:
        return event_repo.max_id(conn)


class EventBus:
    """One shared poller fans events out to every SSE client. It runs only while someone is
    listening, so an idle free-tier instance can go to sleep."""

    def __init__(self) -> None:
        self._subs: set[asyncio.Queue] = set()
        self._task: asyncio.Task | None = None

    async def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=200)
        self._subs.add(q)
        if self._task is None:
            self._task = asyncio.create_task(self._poll())
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self._subs.discard(q)

    async def _poll(self) -> None:
        seen: deque[int] = deque(maxlen=500)
        try:
            cursor = await asyncio.to_thread(_latest)
            for ev in await asyncio.to_thread(_fetch, cursor - REORDER_WINDOW):
                seen.append(ev["id"])  # existing history: don't replay it to live listeners
            while self._subs:
                try:
                    rows = await asyncio.to_thread(_fetch, cursor - REORDER_WINDOW)
                except Exception:
                    log.exception("event poll failed")
                    rows = []
                for ev in rows:
                    if ev["id"] in seen:
                        continue
                    seen.append(ev["id"])
                    cursor = max(cursor, ev["id"])
                    for q in list(self._subs):
                        try:
                            q.put_nowait(ev)
                        except asyncio.QueueFull:
                            log.warning("slow SSE client skipped an event")
                await asyncio.sleep(POLL_SECONDS)
        except Exception:
            log.exception("event poller crashed")
        finally:
            self._task = None


bus = EventBus()
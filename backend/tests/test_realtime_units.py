from datetime import date

from app.repositories.analytics_repo import fill_days
from app.services.event_bus import format_sse


def test_fill_days_zero_fills_and_sums():
    rows = [{"day": date(2026, 10, 6), "category": "billing", "n": 3},
            {"day": date(2026, 10, 6), "category": None, "n": 1}]
    out = fill_days(rows, 3, date(2026, 10, 7))
    assert [d["date"] for d in out] == ["2026-10-05", "2026-10-06", "2026-10-07"]
    assert [d["total"] for d in out] == [0, 4, 0]


def test_sse_frame():
    s = format_sse({"id": 7, "type": "x"})
    assert s.startswith("id: 7\ndata: ") and s.endswith("\n\n")
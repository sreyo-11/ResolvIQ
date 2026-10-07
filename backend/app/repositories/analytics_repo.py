from datetime import date, timedelta

from app.core.constants import SLA_MINUTES

OPEN = "('new','classified','assigned','in_progress')"
AT_RISK = 0.5
# built from constants (never user input): case priority when 'urgent' then 60 ... end
SLA_CASE = "case priority " + " ".join(f"when '{p}' then {m}" for p, m in SLA_MINUTES.items()) + " end"


def summary(conn) -> dict:
    t = conn.execute(f"""
        select
          count(*) filter (where status in {OPEN}) as open_tickets,
          count(*) filter (where created_at >= now() - interval '24 hours') as new_24h,
          count(*) filter (where needs_human_triage and status in ('new','classified')) as needs_triage,
          count(*) filter (where sla_risk >= {AT_RISK} and first_response_at is null
                           and status in {OPEN}) as at_risk
        from tickets""").fetchone()
    s = conn.execute(f"""
        select count(*) as responded,
               count(*) filter (where extract(epoch from (first_response_at - created_at)) / 60
                                <= {SLA_CASE}) as within_sla,
               avg(extract(epoch from (first_response_at - created_at)) / 60) as avg_min
        from tickets
        where first_response_at >= now() - interval '7 days' and priority is not null""").fetchone()
    trending = conn.execute("select count(*) as n from clusters where is_trending").fetchone()["n"]
    return {
        **t,
        "sla_compliance_7d": (s["within_sla"] / s["responded"]) if s["responded"] else None,
        "avg_first_response_min_7d": float(s["avg_min"]) if s["avg_min"] is not None else None,
        "trending_clusters": trending,
    }


def volume_rows(conn, days: int) -> list[dict]:
    return conn.execute(
        "select (created_at at time zone 'UTC')::date as day, category, count(*) as n from tickets "
        "where created_at >= ((now() at time zone 'UTC')::date - %s::int) group by 1, 2",
        (days - 1,),
    ).fetchall()


def fill_days(rows: list[dict], days: int, today: date) -> list[dict]:
    """Zero-fill missing days so the line chart has no gaps. Pure, so it's unit-tested."""
    by_day: dict[date, dict[str, int]] = {}
    for r in rows:
        by_day.setdefault(r["day"], {})[r["category"] or "unclassified"] = r["n"]
    out = []
    for i in range(days - 1, -1, -1):
        day = today - timedelta(days=i)
        cats = by_day.get(day, {})
        out.append({"date": day.isoformat(), "total": sum(cats.values()), "by_category": cats})
    return out


def breakdown(conn, days: int) -> dict:
    def group(col: str) -> list[dict]:  # col comes from the fixed literals below, never from users
        return conn.execute(
            f"select {col} as name, count(*) as value from tickets "
            f"where created_at >= now() - make_interval(days => %s) and {col} is not null "
            f"group by 1 order by 2 desc", (days,)).fetchall()
    return {"by_category": group("category"), "by_priority": group("priority"), "by_status": group("status")}
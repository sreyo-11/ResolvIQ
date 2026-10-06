COLUMNS = ("id, title, summary, size, prev_size, trend_score, is_trending, top_category, "
           "window_start, window_end, created_at")


def fetch_window(conn, start, end) -> list[dict]:
    return conn.execute(
        "select id, subject, body, category, embedding from tickets "
        "where embedding is not null and created_at >= %s and created_at < %s order by created_at",
        (start, end),
    ).fetchall()


def load_previous(conn) -> list[dict]:
    rows = conn.execute(
        "select c.title, c.summary, array_agg(m.ticket_id) as ids from clusters c "
        "join cluster_members m on m.cluster_id = c.id group by c.id"
    ).fetchall()
    return [{"title": r["title"], "summary": r["summary"], "ids": set(r["ids"])} for r in rows]


def replace_all(conn, clusters: list[dict], window_start, window_end) -> None:
    conn.execute("delete from clusters")  # members cascade
    for c in clusters:
        cid = conn.execute(
            "insert into clusters (title, summary, size, prev_size, trend_score, is_trending, "
            "top_category, window_start, window_end) values (%s,%s,%s,%s,%s,%s,%s,%s,%s) returning id",
            (c["title"], c["summary"], c["size"], c["prev_size"], c["trend_score"], c["is_trending"],
             c["top_category"], window_start, window_end),
        ).fetchone()["id"]
        with conn.cursor() as cur:
            cur.executemany("insert into cluster_members (cluster_id, ticket_id) values (%s,%s)",
                            [(cid, t) for t in c["members"]])


def list_clusters(conn, trending_only: bool, limit: int) -> list[dict]:
    where = "where is_trending" if trending_only else ""
    return conn.execute(
        f"select {COLUMNS} from clusters {where} order by trend_score desc, size desc limit %s", (limit,)
    ).fetchall()


def get(conn, cluster_id) -> dict | None:
    return conn.execute(f"select {COLUMNS} from clusters where id = %s", (cluster_id,)).fetchone()
import psycopg


def assign_least_loaded(conn: psycopg.Connection, team: str) -> dict | None:
    return conn.execute(
        """
        update agents set current_load = current_load + 1
        where id = (select id from agents where team = %s
                    order by current_load asc, random() limit 1 for update skip locked)
        returning id, name, current_load - 1 as load_before
        """,
        (team,),
    ).fetchone()


def adjust_load(conn: psycopg.Connection, agent_id, delta: int) -> None:
    conn.execute(
        "update agents set current_load = greatest(0, current_load + %s) where id = %s",
        (delta, agent_id),
    )
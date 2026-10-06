def history(conn, ticket_id, limit: int = 20) -> list[dict]:
    return conn.execute(
        "select breach_probability as probability, predicted_at from sla_predictions "
        "where ticket_id = %s order by predicted_at desc limit %s", (ticket_id, limit)
    ).fetchall()
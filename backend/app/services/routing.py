from dataclasses import dataclass
from uuid import UUID

import psycopg

from app.core.constants import CATEGORY_TEAM, TRIAGE_TEAM
from app.repositories import agent_repo


@dataclass(frozen=True)
class Route:
    team: str
    agent_id: UUID | None
    agent_load: int | None  # load BEFORE this assignment (an SLA model feature)


def route_ticket(conn: psycopg.Connection, category: str, needs_human: bool) -> Route:
    if needs_human:  # uncertain tickets wait in the triage queue, no agent yet
        return Route(TRIAGE_TEAM, None, None)
    team = CATEGORY_TEAM[category]
    agent = agent_repo.assign_least_loaded(conn, team)
    return Route(team, agent["id"] if agent else None, agent["load_before"] if agent else None)
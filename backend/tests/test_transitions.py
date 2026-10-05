import pytest

from app.services.ticket_service import can_transition


@pytest.mark.parametrize("cur,new,ok", [
    ("new", "classified", True),
    ("in_progress", "resolved", True),
    ("resolved", "in_progress", True),   # reopen
    ("closed", "in_progress", False),
    ("new", "closed", False),
    ("resolved", "new", False),
])
def test_transitions(cur, new, ok):
    assert can_transition(cur, new) is ok
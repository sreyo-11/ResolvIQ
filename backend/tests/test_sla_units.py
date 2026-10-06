from datetime import datetime, timezone

from app.services.sla import risk_level
from app.services.sla_features import FEATURE_NAMES, feature_vector


def test_feature_vector_matches_names():
    v = feature_vector(priority="urgent", category="billing", created_at=datetime.now(timezone.utc),
                       subject="a b", body="one two three", queue_length=3, agent_load=None, elapsed_frac=0.5)
    assert len(v) == len(FEATURE_NAMES)


def test_risk_levels():
    assert risk_level(0.8, 0.5) == "high"
    assert risk_level(0.3, 0.5) == "medium"
    assert risk_level(0.1, 0.5) == "low"
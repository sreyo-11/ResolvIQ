from datetime import datetime, timezone

from app.core.constants import SLA_MINUTES
from app.services.model_store import load_bundle
from app.services.sla_features import feature_vector


def risk_level(p: float, threshold: float) -> str:
    return "high" if p >= threshold else "medium" if p >= threshold / 2 else "low"


def predict_risk(ticket: dict, now: datetime | None = None) -> dict | None:
    """None when not applicable (already answered / not yet classified)."""
    if ticket["first_response_at"] is not None or not ticket["priority"] or not ticket["category"]:
        return None
    now = now or datetime.now(timezone.utc)
    limit = SLA_MINUTES[ticket["priority"]]
    frac = (now - ticket["created_at"]).total_seconds() / 60 / limit
    bundle = load_bundle("sla_model.joblib")
    if frac >= 1.0:  # unanswered past the limit: it has already breached
        return {"probability": 1.0, "level": "breached", "elapsed_fraction": round(frac, 2),
                "sla_limit_minutes": limit, "model_version": bundle["version"]}
    x = feature_vector(
        priority=ticket["priority"], category=ticket["category"], created_at=ticket["created_at"],
        subject=ticket["subject"], body=ticket["body"], queue_length=ticket["queue_length_at_creation"],
        agent_load=ticket["agent_load_at_assignment"], elapsed_frac=frac)
    p = float(bundle["model"].predict_proba([x])[0][1])
    return {"probability": round(p, 4), "level": risk_level(p, bundle["threshold"]),
            "elapsed_fraction": round(frac, 2), "sla_limit_minutes": limit, "model_version": bundle["version"]}
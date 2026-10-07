"""Usage (from backend/):  python -m ml.train_sla"""
import json
from datetime import datetime, timezone

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    precision_recall_curve,
    roc_auc_score,
)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from app.core.config import BACKEND_DIR
from app.core.constants import SLA_MINUTES
from app.services.sla_features import FEATURE_NAMES, feature_vector
from ml.data import connect

SNAPSHOTS = (0.0, 0.25, 0.5, 0.75)  # fraction of the SLA window already elapsed
FRAC_COL = FEATURE_NAMES.index("elapsed_frac")
QUERY = """
select priority, category, subject, body, created_at, first_response_at,
       queue_length_at_creation, agent_load_at_assignment
from tickets
where priority is not null and category is not null and classified_by is null
  and created_at < now() - interval '24 hours'   -- mature tickets only: labels are final
order by created_at
"""


def expand(rows: list[dict], now: datetime):
    X, y = [], []
    for r in rows:
        limit = SLA_MINUTES[r["priority"]]
        end = r["first_response_at"] or now  # still unanswered after >24h => it breached
        minutes = (end - r["created_at"]).total_seconds() / 60
        breached = int(minutes > limit)
        for f in SNAPSHOTS:
            if minutes <= f * limit:  # already answered by then -> it was not an open ticket
                continue
            X.append(feature_vector(
                priority=r["priority"], category=r["category"], created_at=r["created_at"],
                subject=r["subject"], body=r["body"], queue_length=r["queue_length_at_creation"],
                agent_load=r["agent_load_at_assignment"], elapsed_frac=f))
            y.append(breached)
    return np.array(X, dtype=float), np.array(y)


def metrics(y, p, X) -> dict:
    at_creation = X[:, FRAC_COL] == 0.0
    return {
        "pr_auc": float(average_precision_score(y, p)),
        "pr_auc_at_creation": float(average_precision_score(y[at_creation], p[at_creation])),
        "roc_auc": float(roc_auc_score(y, p)),
        "brier": float(brier_score_loss(y, p)),
        "base_rate": float(y.mean()),
    }


def main() -> None:
    with connect() as conn:
        rows = conn.execute(QUERY).fetchall()
    now = datetime.now(timezone.utc)
    n = len(rows)
    a, b = int(n * 0.70), int(n * 0.85)  # chronological split BY TICKET
    Xtr, ytr = expand(rows[:a], now)
    Xva, yva = expand(rows[a:b], now)
    Xte, yte = expand(rows[b:], now)
    print(f"tickets={n}  snapshot rows train/val/test = {len(ytr)}/{len(yva)}/{len(yte)}")
    print(f"breach rate train={ytr.mean():.1%} val={yva.mean():.1%} test={yte.mean():.1%}")

    rate = {k: (ytr[Xtr[:, 0] == k].mean() if (Xtr[:, 0] == k).any() else ytr.mean()) for k in range(4)}
    baseline = lambda X: np.array([rate[int(v)] for v in X[:, 0]])  # noqa: E731
    models = {
        "logreg": make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                                LogisticRegression(max_iter=1000)),
        "hist_gb": HistGradientBoostingClassifier(max_depth=4, learning_rate=0.05, max_iter=250,
                                                  l2_regularization=1.0, random_state=42),
    }
    report = {"baseline_priority_only": metrics(yte, baseline(Xte), Xte)}
    print(f"baseline (priority only)  test PR-AUC = {report['baseline_priority_only']['pr_auc']:.3f}")

    fitted, val_scores = {}, {}
    for name, model in models.items():
        model.fit(Xtr, ytr)
        fitted[name] = model
        val_scores[name] = average_precision_score(yva, model.predict_proba(Xva)[:, 1])
        report[name] = metrics(yte, model.predict_proba(Xte)[:, 1], Xte)
        print(f"{name:8s} val PR-AUC={val_scores[name]:.3f}  test PR-AUC={report[name]['pr_auc']:.3f}  "
              f"at-creation={report[name]['pr_auc_at_creation']:.3f}  Brier={report[name]['brier']:.3f}")

    best = max(val_scores, key=val_scores.get)  # choose on validation, not test
    model = fitted[best]

    prec, rec, thr = precision_recall_curve(yva, model.predict_proba(Xva)[:, 1])
    f2 = 5 * prec[:-1] * rec[:-1] / np.maximum(4 * prec[:-1] + rec[:-1], 1e-9)  # favour recall
    threshold = float(thr[int(np.argmax(f2))])
    pte = model.predict_proba(Xte)[:, 1] >= threshold
    tp = int((pte & (yte == 1)).sum())
    report["operating_point"] = {
        "model": best, "threshold": threshold,
        "test_precision": tp / max(int(pte.sum()), 1), "test_recall": tp / max(int(yte.sum()), 1),
    }
    print(f"\nwinner={best} threshold={threshold:.2f} -> test precision="
          f"{report['operating_point']['test_precision']:.2f} recall={report['operating_point']['test_recall']:.2f}")

    imp = permutation_importance(model, Xte, yte, scoring="average_precision", n_repeats=5, random_state=0)
    top = sorted(zip(FEATURE_NAMES, imp.importances_mean,strict=True), key=lambda t: -t[1])[:6]
    report["top_features"] = [{"feature": f, "importance": float(v)} for f, v in top]
    print("top features:", ", ".join(f"{f} ({v:.3f})" for f, v in top))

    (BACKEND_DIR / "models").mkdir(exist_ok=True)
    version = f"{best}-{now:%Y%m%d}"
    joblib.dump({"model": model, "threshold": threshold, "version": version,
                 "feature_names": FEATURE_NAMES, "metrics": report}, BACKEND_DIR / "models" / "sla_model.joblib")
    out = BACKEND_DIR.parent / "docs" / "metrics"
    out.mkdir(parents=True, exist_ok=True)
    (out / "sla.json").write_text(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
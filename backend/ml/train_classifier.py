"""Usage (from backend/):  python -m ml.train_classifier"""
import json
from datetime import datetime, timezone

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import make_pipeline

from app.core.config import BACKEND_DIR
from ml.data import is_test, load_labeled_tickets

MODELS_DIR = BACKEND_DIR / "models"
METRICS_DIR = BACKEND_DIR.parent / "docs" / "metrics"
CLASS_WEIGHT = {"category": None, "priority": "balanced"}  # urgent is only ~7% of tickets


def candidates(target: str) -> dict:
    cw = CLASS_WEIGHT[target]
    return {
        "tfidf_lr": ("text", make_pipeline(
            TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True),
            LogisticRegression(C=10, max_iter=2000, class_weight=cw))),
        "embedding_lr": ("embedding", LogisticRegression(C=10, max_iter=2000, class_weight=cw)),
    }


def features(rows: list[dict]) -> dict:
    return {
        "text": [f"{r['subject']}\n{r['body']}" for r in rows],
        "embedding": np.vstack([r["embedding"].to_numpy() for r in rows]),
    }


def main() -> None:
    rows = load_labeled_tickets()
    train = [r for r in rows if not is_test(r["subject"], r["body"])]
    test = [r for r in rows if is_test(r["subject"], r["body"])]
    print(f"train={len(train)} test={len(test)}")
    ftr, fte = features(train), features(test)
    MODELS_DIR.mkdir(exist_ok=True)
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    report = {"n_train": len(train), "n_test": len(test), "targets": {}}

    for target in ("category", "priority"):
        ytr = np.array([str(r[target]) for r in train])
        yte = np.array([str(r[target]) for r in test])
        results = {}
        for name, (kind, model) in candidates(target).items():
            cv = float(cross_val_score(model, ftr[kind], ytr, cv=5, scoring="f1_macro").mean())
            model.fit(ftr[kind], ytr)
            pred = model.predict(fte[kind])
            acc = float(accuracy_score(yte, pred))
            f1 = float(f1_score(yte, pred, average="macro"))
            results[name] = {"kind": kind, "model": model, "cv_f1": cv, "acc": acc, "f1": f1}
            print(f"[{target}] {name:13s} cv_macro_f1={cv:.3f}  test_acc={acc:.3f}  test_macro_f1={f1:.3f}")

        best = max(results, key=lambda n: results[n]["cv_f1"])  # selected WITHOUT looking at test
        win = results[best]
        model = win["model"]
        proba = model.predict_proba(fte[win["kind"]])
        conf, pred = proba.max(axis=1), model.classes_[proba.argmax(axis=1)]
        print(f"\n[{target}] winner = {best}\n{classification_report(yte, pred, zero_division=0)}")

        table = []
        for t in (0.5, 0.6, 0.7, 0.8):
            m = conf >= t
            acc_auto = float((pred[m] == yte[m]).mean()) if m.any() else None
            table.append({"threshold": t, "coverage": float(m.mean()), "accuracy_on_auto": acc_auto})
            print(f"  threshold {t}: auto-routed {m.mean():.1%}, accuracy on those {acc_auto:.3f}")

        joblib.dump({
            "target": target, "kind": win["kind"], "model": model, "name": best,
            "n_train": len(train), "trained_at": datetime.now(timezone.utc).isoformat(),
        }, MODELS_DIR / f"{target}_clf.joblib")
        report["targets"][target] = {
            "winner": best, "threshold_table": table,
            "candidates": {n: {k: v for k, v in r.items() if k not in ("model", "kind")}
                           for n, r in results.items()},
        }

    (METRICS_DIR / "classifier.json").write_text(json.dumps(report, indent=2))
    print(f"\nSaved models to {MODELS_DIR} and metrics to {METRICS_DIR / 'classifier.json'}")


if __name__ == "__main__":
    main()
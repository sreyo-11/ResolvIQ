from dataclasses import dataclass

import numpy as np

from app.services.model_store import load_bundle


@dataclass(frozen=True)
class Prediction:
    category: str
    category_conf: float
    priority: str
    priority_conf: float
    category_probs: dict[str, float]


@dataclass(frozen=True)
class Flags:
    low_category: bool
    low_priority: bool

    @property
    def any(self) -> bool:
        return self.low_category or self.low_priority


def _predict(bundle: dict, text: str, embedding: np.ndarray):
    x = [text] if bundle["kind"] == "text" else embedding.reshape(1, -1)
    model = bundle["model"]
    probs = {str(c): float(p) for c, p in zip(model.classes_, model.predict_proba(x)[0])}
    label = max(probs, key=probs.get)
    return label, probs[label], probs


def predict(text: str, embedding: np.ndarray) -> Prediction:
    cat, cat_conf, cat_probs = _predict(load_bundle("category_clf.joblib"), text, embedding)
    pri, pri_conf, _ = _predict(load_bundle("priority_clf.joblib"), text, embedding)
    return Prediction(cat, cat_conf, pri, pri_conf, cat_probs)


def low_confidence_flags(pred: Prediction, category_thr: float, priority_thr: float) -> Flags:
    """Pure function, so it is trivially unit-testable."""
    return Flags(pred.category_conf < category_thr, pred.priority_conf < priority_thr)
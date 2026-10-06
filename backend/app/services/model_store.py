from functools import lru_cache

import joblib

from app.core.config import BACKEND_DIR

MODELS_DIR = BACKEND_DIR / "models"


class ModelUnavailable(RuntimeError):
    pass


@lru_cache
def load_bundle(filename: str) -> dict:
    """Load a joblib bundle once per process. Failures are not cached, so retraining works live."""
    path = MODELS_DIR / filename
    if not path.exists():
        raise ModelUnavailable(f"{filename} not found. Train it first (see Steps 6/8).")
    return joblib.load(path)
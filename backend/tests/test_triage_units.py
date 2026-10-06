from app.services.classifier import Prediction, low_confidence_flags
from app.services.pii import mask_pii


def test_flags():
    p = Prediction("billing", 0.55, "high", 0.9, {})
    f = low_confidence_flags(p, 0.6, 0.5)
    assert f.low_category and not f.low_priority and f.any


def test_pii_masking():
    out = mask_pii("mail a.b@x.com, call +91 98765 43210, card 4111 1111 1111 1111, order #482913")
    assert "[EMAIL]" in out and "[PHONE]" in out and "[CARD]" in out
    assert "4111" not in out and "98765" not in out and "#482913" in out
import re

_URL = re.compile(r"https?://\S+")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_SECRET = re.compile(r"\b(?:sk|pk|gsk|AIza)[-_A-Za-z0-9]{16,}\b")
_NUMBER_RUN = re.compile(r"\+?\d[\d -]{7,22}\d")


def _mask_digits(m: re.Match) -> str:
    n = sum(c.isdigit() for c in m.group())
    if n >= 13:
        return "[CARD]"
    if n >= 10:
        return "[PHONE]"
    return m.group()  # order numbers (6 digits), versions, dates stay readable


def mask_pii(text: str) -> str:
    text = _URL.sub("[URL]", text)
    text = _EMAIL.sub("[EMAIL]", text)
    text = _SECRET.sub("[SECRET]", text)
    return _NUMBER_RUN.sub(_mask_digits, text)
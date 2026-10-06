import json
import logging
import re
import time
from dataclasses import dataclass

import httpx

from app.core.config import settings

log = logging.getLogger(__name__)


class LLMUnavailable(RuntimeError):
    """No API key configured for the selected provider."""


class LLMError(RuntimeError):
    """Provider returned an error or unusable output."""


@dataclass(frozen=True)
class LLMResult:
    text: str
    model: str


def llm_available() -> bool:
    key = settings.groq_api_key if settings.llm_provider == "groq" else settings.gemini_api_key
    return bool(key)


def _post(url: str, headers: dict, payload: dict, retries: int = 2) -> dict:
    for attempt in range(retries + 1):
        try:
            r = httpx.post(url, headers=headers, json=payload, timeout=30)
        except httpx.HTTPError as exc:
            raise LLMError(f"network error: {exc}") from exc
        if r.status_code == 429 and attempt < retries:  # free-tier rate limit: back off, retry
            wait = min(float(r.headers.get("retry-after", 2 * (attempt + 1))), 10.0)
            log.warning("LLM rate limited, sleeping %.1fs", wait)
            time.sleep(wait)
            continue
        if r.status_code >= 400:
            raise LLMError(f"{r.status_code}: {r.text[:200]}")
        return r.json()
    raise LLMError("rate limited")


def complete(system: str, user: str, *, json_mode: bool = False,
             max_tokens: int = 400, temperature: float = 0.2) -> LLMResult:
    provider = settings.llm_provider.lower()
    if provider == "groq":
        if not settings.groq_api_key:
            raise LLMUnavailable("GROQ_API_KEY is not set")
        payload = {
            "model": settings.groq_model, "temperature": temperature, "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        data = _post("https://api.groq.com/openai/v1/chat/completions",
                     {"Authorization": f"Bearer {settings.groq_api_key}"}, payload)
        return LLMResult(data["choices"][0]["message"]["content"], settings.groq_model)

    if provider == "gemini":
        if not settings.gemini_api_key:
            raise LLMUnavailable("GEMINI_API_KEY is not set")
        gen_cfg = {"temperature": temperature, "maxOutputTokens": max(max_tokens, 800)}
        if json_mode:
            gen_cfg["responseMimeType"] = "application/json"
        payload = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": gen_cfg,
        }
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"
        data = _post(url, {"x-goog-api-key": settings.gemini_api_key}, payload)
        try:
            return LLMResult(data["candidates"][0]["content"]["parts"][0]["text"], settings.gemini_model)
        except (KeyError, IndexError) as exc:
            raise LLMError(f"unexpected Gemini response: {str(data)[:200]}") from exc

    raise LLMUnavailable(f"unknown LLM_PROVIDER '{settings.llm_provider}'")


def complete_json(system: str, user: str, **kw) -> dict:
    text = complete(system, user, json_mode=True, **kw).text
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    try:
        return json.loads(text[text.index("{"): text.rindex("}") + 1])
    except (ValueError, json.JSONDecodeError) as exc:
        raise LLMError(f"model did not return valid JSON: {text[:120]}") from exc
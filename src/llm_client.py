"""
UniFlow QA Agent — foundation model client.

Owner: Odongo Emmanuel/ Ainebyona Alvin (Backend / System Lead)
Week 2 deliverable D1: working baseline model interaction.

Thin provider wrapper. Deliberately boring: one entry point, explicit timeouts,
bounded retry, and a switchable provider so a rate-limited or dead primary does
not stop the project.

Install:  pip install requests python-dotenv
Configure: copy .env.example to .env and fill in one API key.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, asdict

# pyright: ignore[reportMissingImports] — install with: pip install requests
import requests
from dotenv import load_dotenv

load_dotenv()

TIMEOUT_SECONDS = 60
MAX_RETRIES = 3
BACKOFF_BASE = 2.0

# Pinned for evaluation runs. A probabilistic system cannot be called a
# "baseline" unless sampling is pinned and recorded (Huyen Ch.2, pp. 105-111).
DEFAULT_TEMPERATURE = 0.2


@dataclass
class LLMResponse:
    """Everything a trace needs. Do not drop fields — Week 7 will need this."""
    text: str
    provider: str
    model: str
    temperature: float
    latency_ms: int
    prompt_tokens: int | None
    completion_tokens: int | None
    attempts: int
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class LLMError(RuntimeError):
    pass


class RateLimitError(LLMError):
    pass


def _post(url: str, payload: dict, headers: dict) -> dict:
    resp = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT_SECONDS)
    if resp.status_code == 429:
        raise RateLimitError(f"rate limited: {resp.text[:200]}")
    if resp.status_code >= 400:
        raise LLMError(f"HTTP {resp.status_code}: {resp.text[:300]}")
    return resp.json()


def _call_gemini(system: str, user: str, model: str, temperature: float) -> tuple[str, int | None, int | None]:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise LLMError("GEMINI_API_KEY is not set. Copy .env.example to .env and fill it in.")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {
            "temperature": temperature,
            "responseMimeType": "application/json",  # helps enforce the output contract
        },
    }
    data = _post(url, payload, {"x-goog-api-key": key, "Content-Type": "application/json"})

    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:
        raise LLMError(f"unexpected Gemini response shape: {json.dumps(data)[:300]}") from exc

    usage = data.get("usageMetadata", {})
    return text, usage.get("promptTokenCount"), usage.get("candidatesTokenCount")


def _call_groq(system: str, user: str, model: str, temperature: float) -> tuple[str, int | None, int | None]:
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise LLMError("GROQ_API_KEY is not set. Copy .env.example to .env and fill it in.")

    payload = {
        "model": model,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "response_format": {"type": "json_object"},
    }
    data = _post(
        "https://api.groq.com/openai/v1/chat/completions",
        payload,
        {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )

    text = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    return text, usage.get("prompt_tokens"), usage.get("completion_tokens")


_PROVIDERS = {
    "gemini": (_call_gemini, "GEMINI_MODEL", "gemini-3.6-flash"),
    "groq": (_call_groq, "GROQ_MODEL", "llama-3.3-70b-versatile"),
}


def generate(user: str, system: str = "", temperature: float = DEFAULT_TEMPERATURE) -> LLMResponse:
    """Call the configured provider. Retries transient errors with backoff.

    Set LLM_PROVIDER=gemini|groq in .env to switch. That single env var is the
    whole fallback story — document it in the Model Selection Note.
    """
    provider = os.environ.get("LLM_PROVIDER", "gemini").lower()
    if provider not in _PROVIDERS:
        raise LLMError(f"unknown LLM_PROVIDER {provider!r}; expected one of {list(_PROVIDERS)}")

    fn, model_env, default_model = _PROVIDERS[provider]
    model = os.environ.get(model_env, default_model)

    started = time.perf_counter()
    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            text, p_tok, c_tok = fn(system, user, model, temperature)
            return LLMResponse(
                text=text,
                provider=provider,
                model=model,
                temperature=temperature,
                latency_ms=int((time.perf_counter() - started) * 1000),
                prompt_tokens=p_tok,
                completion_tokens=c_tok,
                attempts=attempt,
            )
        except (RateLimitError, requests.Timeout, requests.ConnectionError) as exc:
            last_error = exc
            if attempt < MAX_RETRIES:
                wait = BACKOFF_BASE ** attempt
                print(f"  [retry {attempt}/{MAX_RETRIES}] {type(exc).__name__}; waiting {wait:.0f}s")
                time.sleep(wait)
        except LLMError as exc:
            # Non-transient (bad key, bad model name). Do not burn retries.
            last_error = exc
            break

    return LLMResponse(
        text="",
        provider=provider,
        model=model,
        temperature=temperature,
        latency_ms=int((time.perf_counter() - started) * 1000),
        prompt_tokens=None,
        completion_tokens=None,
        attempts=MAX_RETRIES,
        error=str(last_error),
    )


if __name__ == "__main__":
    # Smoke test — run this first to confirm your key works.
    r = generate(
        user='Reply with exactly {"ok": true} and nothing else.',
        system="You reply only with raw JSON.",
    )
    if r.error:
        print(f"FAILED: {r.error}")
        raise SystemExit(1)
    print(f"OK  provider={r.provider}  model={r.model}  latency={r.latency_ms}ms")
    print(f"    response: {r.text.strip()[:120]}")

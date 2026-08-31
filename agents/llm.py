"""
Shared LLM client — OpenRouter with configurable model.

All agents import get_client() and get_model() from here.
Model is set via the FORGE_MODEL env var. Defaults to Nemotron 3 Super.

Supported free models:
  nvidia/nemotron-3-super-120b-a12b:free  — 120B, 1M ctx, agentic (default)
  thinkingmachines/inkling:free           — 975B MoE, 41B active, multimodal
  minimax/minimax-m2.7:free               — built for multi-agent workflows, 197K ctx

OpenRouter uses the same OpenAI SDK interface — just a different base_url and api_key.
"""

import os
import sys
import time

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    InternalServerError,
    OpenAI,
    RateLimitError,
)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"

# Free OpenRouter tiers rate-limit aggressively; retry transient errors.
MAX_ATTEMPTS = 3
RETRYABLE_ERRORS = (
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
    InternalServerError,
)


def get_client() -> OpenAI:
    """Return an OpenAI client configured for OpenRouter using OPENROUTER_API_KEY."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENROUTER_API_KEY is not set. "
            "Get a free key at https://openrouter.ai/keys and add it to .env"
        )
    return OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=api_key,
        default_headers={
            "HTTP-Referer": "https://github.com/T9ner/forge-dispatch",
            "X-Title": "Forge Dispatch",
        },
    )


def get_model() -> str:
    """Return the configured model name from FORGE_MODEL or fallback to DEFAULT_MODEL."""
    return os.environ.get("FORGE_MODEL", DEFAULT_MODEL)


def _has_content(response) -> bool:
    """True when the response carries a non-empty message body.
    Free models occasionally return an empty choices list or a None
    content — treated as a transient failure and retried."""
    try:
        return bool(response.choices[0].message.content)
    except (IndexError, AttributeError, TypeError):
        return False


def chat(client: OpenAI, *, model: str, messages: list, **kwargs):
    """chat.completions.create with retry on transient free-tier errors:
    rate limits, timeouts, connection drops, 5xx server errors, and empty responses.

    Raises RuntimeError naming the failure after MAX_ATTEMPTS exhausted.
    """
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = client.chat.completions.create(model=model, messages=messages, **kwargs)
        except RETRYABLE_ERRORS as e:
            last_error = e
        except APIStatusError as e:
            if getattr(e, "status_code", 0) in (429, 500, 502, 503, 504) or getattr(e, "status_code", 0) >= 500:
                last_error = e
            else:
                raise
        else:
            if _has_content(response):
                return response
            last_error = RuntimeError("model returned an empty response")
        if attempt < MAX_ATTEMPTS:
            delay = 2 ** attempt
            # stderr: stdout must stay clean for callers that parse it as JSON
            print(f"[llm] {type(last_error).__name__} from '{model}', retry {attempt}/{MAX_ATTEMPTS - 1} in {delay}s",
                  file=sys.stderr)
            time.sleep(delay)
    raise RuntimeError(
        f"LLM call to '{model}' failed after {MAX_ATTEMPTS} attempts: {last_error}"
    )


def usage_of(response) -> dict:
    """Extract token usage from a chat completion as a plain dict."""
    usage = getattr(response, "usage", None)
    if usage is None:
        return {}
    return {
        "prompt_tokens": getattr(usage, "prompt_tokens", 0),
        "completion_tokens": getattr(usage, "completion_tokens", 0),
        "total_tokens": getattr(usage, "total_tokens", 0),
    }


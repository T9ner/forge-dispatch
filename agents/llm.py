"""
Shared LLM client factory supporting multi-provider configuration.

Supported providers:
1. OpenRouter (OPENROUTER_API_KEY) — access to open-source and commercial models.
2. OpenAI (OPENAI_API_KEY) — official OpenAI endpoints (e.g. gpt-4o, gpt-4o-mini).
3. Anthropic (ANTHROPIC_API_KEY) — official Anthropic Claude endpoints (e.g. claude-3-5-sonnet).
4. Custom OpenAI-compatible endpoints (OPENAI_BASE_URL or LLM_BASE_URL) — Ollama, vLLM, Groq, Together AI, Mistral, DeepSeek, etc.

Model is selected via FORGE_MODEL or defaults per provider.
"""

import os
import sys
import time
from typing import Any

import requests
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    InternalServerError,
    OpenAI,
    RateLimitError,
)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_OPENROUTER_MODEL = "minimax/minimax-m2.7:free"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_ANTHROPIC_MODEL = "claude-3-5-sonnet-latest"

MAX_ATTEMPTS = 3
RETRYABLE_ERRORS = (
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
    InternalServerError,
)


class AnthropicClientAdapter:
    """Lightweight adapter for Anthropic Messages API with OpenAI-compatible interface."""

    def __init__(self, api_key: str, base_url: str = "https://api.anthropic.com/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    class _Completions:
        def __init__(self, parent: "AnthropicClientAdapter"):
            self.parent = parent

        def create(self, *, model: str, messages: list, **kwargs) -> Any:
            system_prompt = None
            filtered_messages = []
            for msg in messages:
                if msg.get("role") == "system":
                    system_prompt = msg.get("content")
                else:
                    filtered_messages.append({
                        "role": msg.get("role"),
                        "content": msg.get("content"),
                    })

            payload: dict[str, Any] = {
                "model": model,
                "max_tokens": kwargs.get("max_tokens", 4096),
                "messages": filtered_messages,
            }
            if system_prompt:
                payload["system"] = system_prompt
            if "temperature" in kwargs:
                payload["temperature"] = kwargs["temperature"]

            headers = {
                "x-api-key": self.parent.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            resp = requests.post(
                f"{self.parent.base_url}/messages",
                json=payload,
                headers=headers,
                timeout=kwargs.get("timeout", 60),
            )
            if resp.status_code != 200:
                raise APIStatusError(
                    message=f"Anthropic API error {resp.status_code}: {resp.text}",
                    response=resp,
                    body=resp.text,
                )

            data = resp.json()
            text = "".join(
                block.get("text", "")
                for block in data.get("content", [])
                if block.get("type") == "text"
            )

            class _Msg:
                content = text

            class _Choice:
                message = _Msg()

            class _Usage:
                prompt_tokens = data.get("usage", {}).get("input_tokens", 0)
                completion_tokens = data.get("usage", {}).get("output_tokens", 0)
                total_tokens = prompt_tokens + completion_tokens

            class _Response:
                choices = [_Choice()]
                usage = _Usage()

            return _Response()

    @property
    def chat(self):
        class _Chat:
            completions = self._Completions(self)

        return _Chat()


def get_provider() -> str:
    """Resolve active LLM provider from environment variables."""
    explicit = os.environ.get("LLM_PROVIDER", "").strip().lower()
    if explicit in ("openrouter", "openai", "anthropic", "custom"):
        return explicit
    if os.environ.get("OPENROUTER_API_KEY"):
        return "openrouter"
    if os.environ.get("OPENAI_BASE_URL") or os.environ.get("LLM_BASE_URL"):
        return "custom"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    return "openrouter"


def get_client() -> Any:
    """Return configured LLM client instance based on active provider."""
    provider = get_provider()

    if provider == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError("ANTHROPIC_API_KEY is not set in environment.")
        return AnthropicClientAdapter(api_key=api_key)

    if provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY is not set in environment.")
        return OpenAI(api_key=api_key)

    if provider == "custom":
        base_url = os.environ.get("OPENAI_BASE_URL") or os.environ.get("LLM_BASE_URL")
        api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY") or "dummy"
        return OpenAI(base_url=base_url, api_key=api_key)

    # Default: OpenRouter
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "No LLM credentials found. Set OPENROUTER_API_KEY, OPENAI_API_KEY, "
            "ANTHROPIC_API_KEY, or OPENAI_BASE_URL in your .env file."
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
    """Return model name from FORGE_MODEL or provider-specific default."""
    configured = os.environ.get("FORGE_MODEL")
    if configured:
        return configured

    provider = get_provider()
    if provider == "openai":
        return DEFAULT_OPENAI_MODEL
    if provider == "anthropic":
        return DEFAULT_ANTHROPIC_MODEL
    return DEFAULT_OPENROUTER_MODEL


def _has_content(response: Any) -> bool:
    """True when the response carries a non-empty message body."""
    try:
        return bool(response.choices[0].message.content)
    except (IndexError, AttributeError, TypeError):
        return False


def chat(client: Any, *, model: str, messages: list, **kwargs) -> Any:
    """chat.completions.create with retry on transient network and API errors."""
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
            print(
                f"[llm] {type(last_error).__name__} from '{model}', retry {attempt}/{MAX_ATTEMPTS - 1} in {delay}s",
                file=sys.stderr,
            )
            time.sleep(delay)
    raise RuntimeError(
        f"LLM call to '{model}' failed after {MAX_ATTEMPTS} attempts: {last_error}"
    )


def usage_of(response: Any) -> dict:
    """Extract token usage from a chat completion as a plain dict."""
    usage = getattr(response, "usage", None)
    if usage is None:
        return {}
    return {
        "prompt_tokens": getattr(usage, "prompt_tokens", 0),
        "completion_tokens": getattr(usage, "completion_tokens", 0),
        "total_tokens": getattr(usage, "total_tokens", 0),
    }


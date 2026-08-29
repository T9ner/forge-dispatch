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
from openai import OpenAI

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"


def get_client() -> OpenAI:
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
    return os.environ.get("FORGE_MODEL", DEFAULT_MODEL)

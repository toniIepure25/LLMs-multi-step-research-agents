"""
Factory helpers for constructing live provider adapters behind ASAR's abstractions.
"""

from __future__ import annotations

import os

from asar.common.config import ASARSettings
from asar.core.errors import ConfigurationError
from asar.core.llm import LLMClientProtocol
from asar.core.search import SearchClientProtocol
from asar.providers.brave_search import BraveSearchClient
from asar.providers.openai_llm import OpenAILLMClient
from asar.providers.tavily_search import TavilySearchClient


def build_live_llm_client(settings: ASARSettings) -> LLMClientProtocol:
    """Build the configured live LLM client for v0."""

    planning_route = settings.models.route_for("planning")
    deliberation_route = settings.models.route_for("deliberation")
    llm_providers = {
        planning_route.provider.lower(),
        deliberation_route.provider.lower(),
    }
    if len(llm_providers) != 1:
        raise ConfigurationError(
            "v0 live mode requires the same LLM provider for planning and deliberation",
            details={"providers": sorted(llm_providers)},
        )

    provider = next(iter(llm_providers))
    if provider != "openai":
        raise ConfigurationError(
            "v0 live mode currently supports only the OpenAI LLM adapter. "
            "Set ASAR_MODEL_PROVIDER=openai and ASAR_MODEL_MODEL=<model>.",
            details={"provider": provider},
        )

    llm_models = {
        planning_route.model.strip(),
        deliberation_route.model.strip(),
    }
    if "" in llm_models or len(llm_models) != 1:
        raise ConfigurationError(
            "v0 live mode requires the same LLM model for planning and deliberation. "
            "Set ASAR_MODEL_MODEL=llama3.3:70b.",
            details={"models": sorted(model for model in llm_models if model)},
        )

    model = next(iter(llm_models))
    if model.startswith("claude-"):
        raise ConfigurationError(
            "v0 live mode requires an OpenAI-compatible model name for the "
            "remote inference endpoint. "
            "Set ASAR_MODEL_MODEL=llama3.3:70b.",
            details={"model": model},
        )

    base_url = os.environ.get("ASAR_OPENAI_BASE_URL", "").strip()
    if not base_url:
        raise ConfigurationError(
            "v0 live mode requires ASAR_OPENAI_BASE_URL for the "
            "OpenAI-compatible inference endpoint. "
            "Set ASAR_OPENAI_BASE_URL=https://inference.ccrolabs.com/v1.",
            details={"env_var": "ASAR_OPENAI_BASE_URL"},
        )

    timeout_seconds = _resolve_openai_timeout_seconds(settings)

    return OpenAILLMClient(
        base_url=base_url,
        timeout=timeout_seconds,
    )


def build_live_search_client() -> SearchClientProtocol:
    """Build the configured live search client for v0."""

    provider = os.environ.get("ASAR_SEARCH_PROVIDER", "tavily").strip().lower()
    if provider == "tavily":
        return TavilySearchClient()
    if provider == "brave":
        return BraveSearchClient()
    raise ConfigurationError(
        "v0 live mode currently supports Tavily as the canonical search adapter. "
        "Set ASAR_SEARCH_PROVIDER=tavily.",
        details={"provider": provider},
    )


def _resolve_openai_timeout_seconds(settings: ASARSettings) -> float:
    env_value = os.environ.get("ASAR_OPENAI_TIMEOUT_SECONDS", "").strip()
    if not env_value:
        return float(settings.pipeline.execution.timeout_seconds)

    try:
        timeout_seconds = float(env_value)
    except ValueError as exc:
        raise ConfigurationError(
            "ASAR_OPENAI_TIMEOUT_SECONDS must be a positive number.",
            details={"env_var": "ASAR_OPENAI_TIMEOUT_SECONDS", "value": env_value},
        ) from exc

    if timeout_seconds <= 0:
        raise ConfigurationError(
            "ASAR_OPENAI_TIMEOUT_SECONDS must be greater than zero.",
            details={"env_var": "ASAR_OPENAI_TIMEOUT_SECONDS", "value": env_value},
        )

    return timeout_seconds

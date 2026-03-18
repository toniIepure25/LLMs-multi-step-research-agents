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


def build_live_llm_client(settings: ASARSettings) -> LLMClientProtocol:
    """Build the configured live LLM client for v0."""

    llm_providers = {
        settings.models.route_for("planning").provider.lower(),
        settings.models.route_for("deliberation").provider.lower(),
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

    return OpenAILLMClient()


def build_live_search_client() -> SearchClientProtocol:
    """Build the configured live search client for v0."""

    provider = os.environ.get("ASAR_SEARCH_PROVIDER", "brave").strip().lower()
    if provider != "brave":
        raise ConfigurationError(
            "v0 live mode currently supports only the Brave Search adapter. "
            "Set ASAR_SEARCH_PROVIDER=brave.",
            details={"provider": provider},
        )

    return BraveSearchClient()

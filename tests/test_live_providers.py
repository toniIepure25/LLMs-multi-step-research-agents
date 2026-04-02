"""
Tests for live provider wiring and safe live smoke behavior.
"""

from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

from asar.common import load_settings
from asar.core.errors import ConfigurationError, LLMClientError
from asar.core.llm import LLMGenerationRequest, LLMMessage, MessageRole
from asar.demo import build_demo_orchestrator
from asar.providers import (
    OpenAILLMClient,
    TavilySearchClient,
    build_live_llm_client,
    build_live_search_client,
)
from tests.test_common_foundations import CONFIG_DIR


def test_global_model_env_overrides_update_all_active_routes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ASAR_MODEL_PROVIDER", "openai")
    monkeypatch.setenv("ASAR_MODEL_MODEL", "llama3.3:70b")

    settings = load_settings(CONFIG_DIR)

    assert settings.models.default.provider == "openai"
    assert settings.models.route_for("planning").provider == "openai"
    assert settings.models.route_for("deliberation").provider == "openai"
    assert settings.models.route_for("planning").model == "llama3.3:70b"
    assert settings.models.route_for("deliberation").model == "llama3.3:70b"


def test_build_live_llm_client_uses_custom_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    monkeypatch.setenv("ASAR_MODEL_PROVIDER", "openai")
    monkeypatch.setenv("ASAR_MODEL_MODEL", "llama3.3:70b")
    monkeypatch.setenv("ASAR_OPENAI_BASE_URL", "https://inference.ccrolabs.com/v1")

    settings = load_settings(CONFIG_DIR)
    client = build_live_llm_client(settings)

    assert isinstance(client, OpenAILLMClient)
    assert str(client._client.base_url) == "https://inference.ccrolabs.com/v1/"
    assert client._timeout_seconds == float(settings.pipeline.execution.timeout_seconds)


def test_build_live_llm_client_honors_timeout_env_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    monkeypatch.setenv("ASAR_MODEL_PROVIDER", "openai")
    monkeypatch.setenv("ASAR_MODEL_MODEL", "llama3.3:70b")
    monkeypatch.setenv("ASAR_OPENAI_BASE_URL", "https://inference.ccrolabs.com/v1")
    monkeypatch.setenv("ASAR_OPENAI_TIMEOUT_SECONDS", "180")

    settings = load_settings(CONFIG_DIR)
    client = build_live_llm_client(settings)

    assert isinstance(client, OpenAILLMClient)
    assert client._timeout_seconds == 180.0


def test_build_live_search_client_prefers_tavily(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ASAR_SEARCH_PROVIDER", "tavily")
    monkeypatch.setenv("TAVILY_API_KEY", "dummy")

    client = build_live_search_client()

    assert isinstance(client, TavilySearchClient)


@pytest.mark.asyncio
async def test_openai_client_uses_chat_completions_for_custom_base_url() -> None:
    client = OpenAILLMClient(
        api_key="dummy",
        base_url="https://inference.ccrolabs.com/v1",
    )

    state = {"chat_called": False, "responses_called": False}

    async def fake_chat_create(**kwargs):
        state["chat_called"] = True
        assert kwargs["model"] == "llama3.3:70b"
        assert kwargs["messages"][0]["role"] == "system"
        assert kwargs["messages"][1]["role"] == "user"
        assert kwargs["max_tokens"] == 1024
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content=(
                            '{"steps":[{"description":"step one","expected_output":"notes",'
                            '"success_criteria":"done"},{"description":"step two",'
                            '"expected_output":"notes","success_criteria":"done"},'
                            '{"description":"step three","expected_output":"notes",'
                            '"success_criteria":"done"}]}'
                        )
                    ),
                    finish_reason="stop",
                )
            ],
            usage=SimpleNamespace(prompt_tokens=11, completion_tokens=7),
            model_dump=lambda: {"ok": True},
        )

    async def fake_responses_create(**kwargs):
        state["responses_called"] = True
        raise AssertionError("responses.create should not be called for custom base URLs")

    client._client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=fake_chat_create)),
        responses=SimpleNamespace(create=fake_responses_create),
    )

    response = await client.generate(
        LLMGenerationRequest(
            model="llama3.3:70b",
            messages=[
                LLMMessage(role=MessageRole.SYSTEM, content="Return JSON only."),
                LLMMessage(role=MessageRole.USER, content="Plan this question."),
            ],
            temperature=0.0,
            max_tokens=4096,
        )
    )

    assert state == {"chat_called": True, "responses_called": False}
    assert response.output_text.startswith('{"steps":')
    assert response.finish_reason == "stop"
    assert response.usage.input_tokens == 11
    assert response.usage.output_tokens == 7


@pytest.mark.asyncio
async def test_openai_client_adds_resource_hint_for_compatibility_endpoint_failures() -> None:
    client = OpenAILLMClient(
        api_key="dummy",
        base_url="https://inference.ccrolabs.com/v1",
    )

    async def fake_chat_create(**kwargs):
        raise RuntimeError(
            "Error code: 500 - {'error': {'message': 'model runner has unexpectedly stopped, "
            "this may be due to resource limitations or an internal error'}}"
        )

    client._client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=fake_chat_create)),
        responses=SimpleNamespace(create=None),
    )

    with pytest.raises(LLMClientError) as exc_info:
        await client.generate(
            LLMGenerationRequest(
                model="llama3.3:70b",
                messages=[
                    LLMMessage(role=MessageRole.SYSTEM, content="Return JSON only."),
                    LLMMessage(role=MessageRole.USER, content="Plan this question."),
                ],
                temperature=0.0,
                max_tokens=4096,
            )
        )

    error = exc_info.value
    assert error.details["base_url"] == "https://inference.ccrolabs.com/v1"
    assert "ASAR_MODEL_MAX_TOKENS" in error.details["hint"]


@pytest.mark.asyncio
async def test_openai_client_marks_timeout_failures_retryable() -> None:
    client = OpenAILLMClient(
        api_key="dummy",
        base_url="https://inference.ccrolabs.com/v1",
        timeout=90.0,
    )

    async def fake_chat_create(**kwargs):
        raise TimeoutError("Request timed out.")

    client._client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=fake_chat_create)),
        responses=SimpleNamespace(create=None),
    )

    with pytest.raises(LLMClientError) as exc_info:
        await client.generate(
            LLMGenerationRequest(
                model="llama3.3:70b",
                messages=[
                    LLMMessage(role=MessageRole.SYSTEM, content="Return JSON only."),
                    LLMMessage(role=MessageRole.USER, content="Plan this question."),
                ],
                temperature=0.0,
                max_tokens=4096,
            )
        )

    error = exc_info.value
    assert error.retryable is True
    assert error.details["timeout_seconds"] == 90.0


def test_live_demo_mode_fails_clearly_when_openai_base_url_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    monkeypatch.setenv("ASAR_MODEL_PROVIDER", "openai")
    monkeypatch.setenv("ASAR_MODEL_MODEL", "llama3.3:70b")
    monkeypatch.delenv("ASAR_OPENAI_BASE_URL", raising=False)

    with pytest.raises(ConfigurationError, match="ASAR_OPENAI_BASE_URL"):
        build_demo_orchestrator(config_dir=CONFIG_DIR, mode="live")


def test_live_demo_mode_fails_clearly_when_tavily_key_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    monkeypatch.setenv("ASAR_MODEL_PROVIDER", "openai")
    monkeypatch.setenv("ASAR_MODEL_MODEL", "llama3.3:70b")
    monkeypatch.setenv("ASAR_OPENAI_BASE_URL", "https://inference.ccrolabs.com/v1")
    monkeypatch.setenv("ASAR_SEARCH_PROVIDER", "tavily")
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    with pytest.raises(ConfigurationError, match="TAVILY_API_KEY"):
        build_demo_orchestrator(config_dir=CONFIG_DIR, mode="live")


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.environ.get("ASAR_RUN_LIVE_SMOKE") != "1"
    or "OPENAI_API_KEY" not in os.environ
    or "ASAR_OPENAI_BASE_URL" not in os.environ
    or "TAVILY_API_KEY" not in os.environ,
    reason=(
        "Set ASAR_RUN_LIVE_SMOKE=1 plus OPENAI_API_KEY, "
        "ASAR_OPENAI_BASE_URL, and TAVILY_API_KEY to run."
    ),
)
async def test_live_demo_smoke_path() -> None:
    from asar.demo import run_demo_pipeline

    output = await run_demo_pipeline(
        "What were the main causes of the 2008 financial crisis?",
        mode="live",
    )

    assert output.decision is not None
    assert output.verification is not None

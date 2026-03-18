"""
Unit tests for common and core foundation utilities.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from asar.common.config import load_settings
from asar.common.ids import IDPrefix, generate_id, generate_trace_id
from asar.common.logging import TraceLoggerAdapter, get_logger, setup_logging
from asar.core.errors import ConfigurationError
from asar.core.llm import LLMGenerationRequest, LLMMessage, MessageRole, TokenUsage
from asar.core.result import OperationResult


CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def test_load_settings_from_repo_config() -> None:
    settings = load_settings(CONFIG_DIR)

    assert settings.project.name == "asar"
    assert settings.project.version == "0.1.0"
    assert settings.models.route_for("planning").model == "claude-sonnet-4-6"
    assert settings.pipeline.logging.level == "info"
    assert settings.experiments.defaults.seed == 42


def test_load_settings_applies_environment_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ASAR_MODEL_PROVIDER", "openai")
    monkeypatch.setenv("ASAR_PLANNING_MODEL", "gpt-5.4")
    monkeypatch.setenv("ASAR_LOG_LEVEL", "debug")

    settings = load_settings(CONFIG_DIR)

    assert settings.models.default.provider == "openai"
    assert settings.models.planning is not None
    assert settings.models.planning.model == "gpt-5.4"
    assert settings.pipeline.logging.level == "debug"


def test_load_settings_raises_for_missing_file(tmp_path: Path) -> None:
    (tmp_path / "project.toml").write_text("[project]\nname='asar'\n", encoding="utf-8")

    with pytest.raises(ConfigurationError):
        load_settings(tmp_path)


def test_generate_id_uses_prefix_and_is_unique() -> None:
    identifiers = {generate_id(IDPrefix.EVIDENCE) for _ in range(20)}

    assert len(identifiers) == 20
    assert all(identifier.startswith("evidence_") for identifier in identifiers)
    assert generate_trace_id().startswith("trace_")


def test_generate_id_rejects_empty_prefix() -> None:
    with pytest.raises(ValueError):
        generate_id("")


def test_setup_logging_and_trace_adapter_emit_trace_id() -> None:
    settings = load_settings(CONFIG_DIR)
    stream = io.StringIO()
    setup_logging(settings.pipeline.logging, force=True, stream=stream)

    logger = get_logger("asar.tests.common", trace_id="trace-123")
    assert isinstance(logger, TraceLoggerAdapter)
    logger.info("foundation log")

    output = stream.getvalue()
    assert "foundation log" in output
    assert "trace-123" in output


def test_operation_result_success_and_failure() -> None:
    success = OperationResult.ok("ready")
    failure = OperationResult[str].fail("config_error", "bad config", retryable=False)

    assert success.is_ok
    assert success.unwrap() == "ready"
    assert failure.is_error
    with pytest.raises(RuntimeError):
        failure.unwrap()


def test_llm_request_and_usage_are_typed() -> None:
    request = LLMGenerationRequest(
        model="gpt-5.4",
        messages=[
            LLMMessage(role=MessageRole.SYSTEM, content="You are helpful."),
            LLMMessage(role=MessageRole.USER, content="Summarize this."),
        ],
        max_tokens=256,
    )
    usage = TokenUsage(input_tokens=10, output_tokens=5)

    assert request.messages[0].role is MessageRole.SYSTEM
    assert usage.total_tokens == 15

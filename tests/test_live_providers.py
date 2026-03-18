"""
Tests for live provider wiring and safe live smoke behavior.
"""

from __future__ import annotations

import os

import pytest

from asar.common import load_settings
from asar.core.errors import ConfigurationError
from asar.demo import build_demo_orchestrator

from tests.test_common_foundations import CONFIG_DIR


def test_global_model_env_overrides_update_all_active_routes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ASAR_MODEL_PROVIDER", "openai")
    monkeypatch.setenv("ASAR_MODEL_MODEL", "gpt-5.2")

    settings = load_settings(CONFIG_DIR)

    assert settings.models.default.provider == "openai"
    assert settings.models.route_for("planning").provider == "openai"
    assert settings.models.route_for("deliberation").provider == "openai"
    assert settings.models.route_for("planning").model == "gpt-5.2"
    assert settings.models.route_for("deliberation").model == "gpt-5.2"


def test_live_demo_mode_fails_clearly_when_credentials_are_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ASAR_MODEL_PROVIDER", "openai")
    monkeypatch.setenv("ASAR_MODEL_MODEL", "gpt-5.2")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)

    with pytest.raises(ConfigurationError, match="OPENAI_API_KEY"):
        build_demo_orchestrator(config_dir=CONFIG_DIR, mode="live")


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.environ.get("ASAR_RUN_LIVE_SMOKE") != "1"
    or "OPENAI_API_KEY" not in os.environ
    or "BRAVE_SEARCH_API_KEY" not in os.environ,
    reason="Set ASAR_RUN_LIVE_SMOKE=1 plus OPENAI_API_KEY and BRAVE_SEARCH_API_KEY to run.",
)
async def test_live_demo_smoke_path() -> None:
    from asar.demo import run_demo_pipeline

    output = await run_demo_pipeline(
        "What were the main causes of the 2008 financial crisis?",
        mode="live",
    )

    assert output.decision is not None
    assert output.verification is not None

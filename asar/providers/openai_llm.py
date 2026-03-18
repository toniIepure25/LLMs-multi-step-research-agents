"""
OpenAI-backed implementation of ASAR's typed LLM client protocol.
"""

from __future__ import annotations

import os
from typing import Any

from asar.core.errors import ConfigurationError, LLMClientError
from asar.core.llm import LLMGenerationRequest, LLMGenerationResponse, TokenUsage


class OpenAILLMClient:
    """Minimal OpenAI Responses API adapter for the v0 planner and synthesizer."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        resolved_api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not resolved_api_key:
            raise ConfigurationError(
                "Live OpenAI mode requires OPENAI_API_KEY",
                details={"env_var": "OPENAI_API_KEY"},
            )

        try:
            from openai import AsyncOpenAI
        except ImportError as exc:  # pragma: no cover - dependency controlled by local env
            raise ConfigurationError(
                "OpenAI SDK is not installed. Run `uv sync --extra dev` or `uv sync` first.",
            ) from exc

        self._client = AsyncOpenAI(
            api_key=resolved_api_key,
            base_url=base_url or os.environ.get("ASAR_OPENAI_BASE_URL"),
            timeout=timeout,
        )

    async def generate(self, request: LLMGenerationRequest) -> LLMGenerationResponse:
        instructions, input_text = _to_openai_payload(request)

        try:
            response = await self._client.responses.create(
                model=request.model,
                instructions=instructions,
                input=input_text,
                temperature=request.temperature,
                max_output_tokens=request.max_tokens,
            )
        except Exception as exc:
            raise LLMClientError(
                "OpenAI Responses API call failed",
                details={
                    "model": request.model,
                    "metadata": request.metadata,
                    "error": str(exc),
                },
                retryable=False,
            ) from exc

        output_text = getattr(response, "output_text", None) or _extract_output_text(response)
        if not output_text:
            raise LLMClientError(
                "OpenAI Responses API returned no output text",
                details={"model": request.model, "metadata": request.metadata},
            )

        return LLMGenerationResponse(
            model=request.model,
            output_text=output_text,
            finish_reason=getattr(response, "status", None),
            usage=_extract_usage(response),
            raw_response=_model_dump(response),
        )


def _to_openai_payload(request: LLMGenerationRequest) -> tuple[str | None, str]:
    instruction_parts: list[str] = []
    input_parts: list[str] = []

    for message in request.messages:
        if message.role.value == "system":
            instruction_parts.append(message.content)
        else:
            input_parts.append(f"{message.role.value.upper()}:\n{message.content}")

    instructions = "\n\n".join(instruction_parts) if instruction_parts else None
    input_text = "\n\n".join(input_parts).strip()
    if not input_text:
        raise LLMClientError("OpenAI adapter requires at least one non-system message")
    return instructions, input_text


def _extract_output_text(response: Any) -> str:
    output_items = getattr(response, "output", None) or []
    texts: list[str] = []
    for item in output_items:
        for content_item in getattr(item, "content", None) or []:
            text_value = getattr(content_item, "text", None)
            if isinstance(text_value, str) and text_value:
                texts.append(text_value)
    return "\n".join(texts).strip()


def _extract_usage(response: Any) -> TokenUsage:
    usage = getattr(response, "usage", None)
    if usage is None:
        return TokenUsage()
    return TokenUsage(
        input_tokens=getattr(usage, "input_tokens", 0) or 0,
        output_tokens=getattr(usage, "output_tokens", 0) or 0,
    )


def _model_dump(response: Any) -> dict[str, Any]:
    if hasattr(response, "model_dump"):
        dumped = response.model_dump()
        if isinstance(dumped, dict):
            return dumped
    if hasattr(response, "to_dict"):
        dumped = response.to_dict()
        if isinstance(dumped, dict):
            return dumped
    return {}

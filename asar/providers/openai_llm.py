"""
OpenAI-backed implementation of ASAR's typed LLM client protocol.
"""

from __future__ import annotations

import os
from typing import Any

from asar.core.errors import ConfigurationError, LLMClientError
from asar.core.llm import LLMGenerationRequest, LLMGenerationResponse, TokenUsage

_COMPAT_MAX_TOKENS = 1024


class OpenAILLMClient:
    """Minimal OpenAI adapter for the v0 planner and synthesizer.

    The default OpenAI-hosted path uses the Responses API. When a custom
    OpenAI-compatible base URL is configured, the adapter switches to the chat
    completions API because many compatibility endpoints implement that surface
    but not the newer Responses API.
    """

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

        resolved_base_url = base_url or os.environ.get("ASAR_OPENAI_BASE_URL")

        try:
            from openai import AsyncOpenAI
        except ImportError as exc:  # pragma: no cover - dependency controlled by local env
            raise ConfigurationError(
                "OpenAI SDK is not installed. Run `uv sync --extra dev` or `uv sync` first.",
            ) from exc

        self._client = AsyncOpenAI(
            api_key=resolved_api_key,
            base_url=resolved_base_url,
            timeout=timeout,
        )
        self._base_url = resolved_base_url
        self._timeout_seconds = timeout
        self._use_chat_completions = bool(resolved_base_url)

    async def generate(self, request: LLMGenerationRequest) -> LLMGenerationResponse:
        if self._use_chat_completions:
            return await self._generate_via_chat_completions(request)
        return await self._generate_via_responses(request)

    async def _generate_via_responses(
        self,
        request: LLMGenerationRequest,
    ) -> LLMGenerationResponse:
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
                    "timeout_seconds": self._timeout_seconds,
                },
                retryable=_is_timeout_error(exc),
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

    async def _generate_via_chat_completions(
        self,
        request: LLMGenerationRequest,
    ) -> LLMGenerationResponse:
        messages = _to_chat_completions_messages(request)
        max_tokens = min(request.max_tokens, _COMPAT_MAX_TOKENS)

        try:
            response = await self._client.chat.completions.create(
                model=request.model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=max_tokens,
            )
        except Exception as exc:
            details = {
                "model": request.model,
                "metadata": request.metadata,
                "base_url": self._base_url,
                "error": str(exc),
                "timeout_seconds": self._timeout_seconds,
            }
            hint = _compatibility_hint(exc)
            if hint is not None:
                details["hint"] = hint
            raise LLMClientError(
                "OpenAI-compatible chat completions call failed",
                details=details,
                retryable=_is_timeout_error(exc),
            ) from exc

        output_text = _extract_chat_completion_text(response)
        if not output_text:
            raise LLMClientError(
                "OpenAI-compatible chat completions returned no output text",
                details={
                    "model": request.model,
                    "metadata": request.metadata,
                    "base_url": self._base_url,
                },
            )

        return LLMGenerationResponse(
            model=request.model,
            output_text=output_text,
            finish_reason=_extract_chat_finish_reason(response),
            usage=_extract_chat_usage(response),
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


def _to_chat_completions_messages(request: LLMGenerationRequest) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for message in request.messages:
        messages.append(
            {
                "role": message.role.value,
                "content": message.content,
            }
        )
    return messages


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


def _extract_chat_completion_text(response: Any) -> str:
    choices = getattr(response, "choices", None) or []
    if not choices:
        return ""

    message = getattr(choices[0], "message", None)
    if message is None:
        return ""

    content = getattr(message, "content", None)
    if isinstance(content, str):
        return content.strip()
    return ""


def _extract_chat_finish_reason(response: Any) -> str | None:
    choices = getattr(response, "choices", None) or []
    if not choices:
        return None
    return getattr(choices[0], "finish_reason", None)


def _extract_chat_usage(response: Any) -> TokenUsage:
    usage = getattr(response, "usage", None)
    if usage is None:
        return TokenUsage()
    return TokenUsage(
        input_tokens=getattr(usage, "prompt_tokens", 0) or 0,
        output_tokens=getattr(usage, "completion_tokens", 0) or 0,
    )


def _compatibility_hint(exc: Exception) -> str | None:
    error_text = str(exc).lower()
    if "resource limitation" in error_text or "runner has unexpectedly stopped" in error_text:
        return (
            "The upstream OpenAI-compatible endpoint reported a model-runner/resource failure. "
            "Try lowering ASAR_MODEL_MAX_TOKENS to 512 if the problem persists."
        )
    return None


def _is_timeout_error(exc: Exception) -> bool:
    current: BaseException | None = exc
    timeout_names = {
        "APITimeoutError",
        "ConnectTimeout",
        "ReadTimeout",
        "TimeoutError",
        "WriteTimeout",
    }

    while current is not None:
        if isinstance(current, TimeoutError):
            return True
        if current.__class__.__name__ in timeout_names:
            return True
        current = current.__cause__ or current.__context__

    error_text = str(exc).lower()
    return "timed out" in error_text or "timeout" in error_text


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

"""
Typed LLM client abstractions used by higher-level ASAR layers.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Supported roles for an LLM conversation turn."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class LLMMessage(BaseModel):
    """One prompt/response message in an LLM request."""

    role: MessageRole
    content: str = Field(..., min_length=1)


class TokenUsage(BaseModel):
    """Token accounting returned by an LLM provider."""

    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class LLMGenerationRequest(BaseModel):
    """Typed input for a single text generation call."""

    model: str = Field(..., min_length=1)
    messages: list[LLMMessage] = Field(..., min_length=1)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1)
    metadata: dict[str, str] = Field(default_factory=dict)


class LLMGenerationResponse(BaseModel):
    """Typed output for a single text generation call."""

    model: str = Field(..., min_length=1)
    output_text: str = Field(..., min_length=1)
    finish_reason: str | None = None
    usage: TokenUsage = Field(default_factory=TokenUsage)
    raw_response: dict[str, Any] = Field(default_factory=dict)


@runtime_checkable
class LLMClientProtocol(Protocol):
    """Smallest useful protocol for an LLM-backed component."""

    async def generate(self, request: LLMGenerationRequest) -> LLMGenerationResponse:
        """Generate a text response from a typed request."""
        ...

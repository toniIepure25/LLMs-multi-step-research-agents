"""
Core — Shared protocols, base classes, and type definitions.

This module defines the interfaces that all layers must implement.
It contains no concrete implementations — only contracts.

Responsibilities:
- Protocol definitions for each layer (see asar/core/protocols.py)
- Base exception types
- Shared type aliases
"""

from asar.core.errors import (
    ASARError,
    ConfigurationError,
    DeliberationError,
    EvaluationError,
    ExecutionError,
    LLMClientError,
    MemoryStoreError,
    OrchestrationError,
    PlanningError,
    SearchClientError,
    VerificationError,
)
from asar.core.llm import (
    LLMClientProtocol,
    LLMGenerationRequest,
    LLMGenerationResponse,
    LLMMessage,
    MessageRole,
    TokenUsage,
)
from asar.core.result import ErrorInfo, OperationResult
from asar.core.search import SearchClientProtocol, SearchRequest, SearchResponse, SearchResultItem

__all__ = [
    "ASARError",
    "ConfigurationError",
    "DeliberationError",
    "EvaluationError",
    "ExecutionError",
    "LLMClientError",
    "PlanningError",
    "SearchClientError",
    "MemoryStoreError",
    "OrchestrationError",
    "VerificationError",
    "ErrorInfo",
    "OperationResult",
    "SearchClientProtocol",
    "SearchRequest",
    "SearchResponse",
    "SearchResultItem",
    "LLMClientProtocol",
    "LLMGenerationRequest",
    "LLMGenerationResponse",
    "LLMMessage",
    "MessageRole",
    "TokenUsage",
]

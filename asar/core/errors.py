"""
Core error types shared across ASAR foundations and layers.
"""

from __future__ import annotations

from typing import Any


class ASARError(Exception):
    """Base exception for all first-party ASAR errors."""

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.retryable = retryable


class ConfigurationError(ASARError):
    """Raised when configuration cannot be loaded or validated."""


class LLMClientError(ASARError):
    """Raised when an LLM client cannot satisfy a request."""


class PlanningError(ASARError):
    """Raised when the planning layer cannot build a valid research plan."""


class DeliberationError(ASARError):
    """Raised when the deliberation layer cannot build a valid decision packet."""


class VerificationError(ASARError):
    """Raised when the verification layer cannot safely evaluate a decision packet."""


class EvaluationError(ASARError):
    """Raised when the evaluation layer cannot build or persist a run record."""


class OrchestrationError(ASARError):
    """Raised when the orchestration layer cannot complete a pipeline run."""


class SearchClientError(ASARError):
    """Raised when a search provider cannot satisfy a search request."""


class ExecutionError(ASARError):
    """Raised when the execution layer cannot normalize task results."""


class MemoryStoreError(ASARError):
    """Raised when working memory cannot store or retrieve data safely."""

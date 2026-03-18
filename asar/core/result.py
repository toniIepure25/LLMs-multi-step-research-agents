"""
Minimal typed result containers for recoverable operations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar


T = TypeVar("T")


@dataclass(frozen=True)
class ErrorInfo:
    """Structured error information for non-exception result paths."""

    code: str
    message: str
    retryable: bool = False
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OperationResult(Generic[T]):
    """A typed success-or-failure container."""

    value: T | None = None
    error: ErrorInfo | None = None

    def __post_init__(self) -> None:
        if (self.value is None) == (self.error is None):
            raise ValueError("OperationResult must contain exactly one of value or error")

    @property
    def is_ok(self) -> bool:
        return self.error is None

    @property
    def is_error(self) -> bool:
        return self.error is not None

    @classmethod
    def ok(cls, value: T) -> "OperationResult[T]":
        return cls(value=value)

    @classmethod
    def fail(
        cls,
        code: str,
        message: str,
        *,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> "OperationResult[T]":
        return cls(
            error=ErrorInfo(
                code=code,
                message=message,
                retryable=retryable,
                details=details or {},
            )
        )

    def unwrap(self) -> T:
        if self.error is not None:
            raise RuntimeError(self.error.message)
        if self.value is None:
            raise RuntimeError("OperationResult has no value")
        return self.value

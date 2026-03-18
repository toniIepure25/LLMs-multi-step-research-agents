"""
ID generation helpers for typed ASAR artifacts.
"""

from __future__ import annotations

from enum import Enum
from uuid import uuid4


class IDPrefix(str, Enum):
    """Canonical prefixes for generated ASAR identifiers."""

    PLAN = "plan"
    STEP = "step"
    TASK = "task"
    EVIDENCE = "evidence"
    DECISION = "decision"
    CLAIM = "claim"
    CONFLICT = "conflict"
    EXPERIMENT = "experiment"
    TRACE = "trace"


def generate_id(prefix: IDPrefix | str) -> str:
    """Generate a stable, human-readable identifier with a prefix."""

    prefix_value = prefix.value if isinstance(prefix, IDPrefix) else prefix.strip().lower()
    if not prefix_value:
        raise ValueError("ID prefix must not be empty")
    return f"{prefix_value}_{uuid4().hex[:12]}"


def generate_trace_id() -> str:
    """Generate a trace identifier for structured logging."""

    return generate_id(IDPrefix.TRACE)

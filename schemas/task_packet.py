"""
TaskPacket — The unit of work dispatched from orchestration to execution.

Each TaskPacket represents a single executable action derived from a PlanStep.
Executors are stateless — all context needed to execute comes from the TaskPacket.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from schemas._timestamps import UTCDateTime


class TaskStatus(str, Enum):
    """Lifecycle status of a task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskPacket(BaseModel):
    """A single unit of work for the execution layer."""
    task_id: str = Field(..., description="Unique identifier for this task")
    plan_id: str = Field(..., description="ID of the parent ResearchPlan")
    step_id: str = Field(..., description="ID of the parent PlanStep")
    action: str = Field(..., description="What the executor should do (e.g., 'search', 'retrieve', 'parse')")
    query: str = Field(..., description="The specific query or instruction for the executor")
    context: Optional[str] = Field(
        default=None,
        description="Additional context from the plan or prior steps",
    )
    expected_output_type: str = Field(
        default="evidence",
        description="What type of output is expected (e.g., 'evidence', 'summary', 'extraction')",
    )
    constraints: dict[str, Any] = Field(
        default_factory=dict,
        description="Execution constraints (e.g., max_results, timeout, source_filter)",
    )
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    created_at: UTCDateTime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # TODO: Add retry count and max retries
    # TODO: Add cost budget per task

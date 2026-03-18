"""
ResearchPlan — The structured output of the planning layer.

A ResearchPlan decomposes a research goal into ordered and/or parallel steps,
each with typed expectations and success criteria.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from schemas._timestamps import UTCDateTime


class StepDependencyType(str, Enum):
    """How a step relates to other steps in the plan."""
    SEQUENTIAL = "sequential"  # Must run after dependencies complete
    PARALLEL = "parallel"      # Can run concurrently with siblings
    CONDITIONAL = "conditional" # Runs only if a condition is met


class PlanStep(BaseModel):
    """A single step in a research plan."""
    step_id: str = Field(..., description="Unique identifier for this step")
    description: str = Field(..., description="What this step should accomplish")
    expected_output: str = Field(..., description="What a successful result looks like")
    success_criteria: str = Field(..., description="How to determine if the step succeeded")
    dependency_type: StepDependencyType = Field(
        default=StepDependencyType.SEQUENTIAL,
        description="Execution ordering constraint",
    )
    depends_on: list[str] = Field(
        default_factory=list,
        description="Step IDs that must complete before this step",
    )
    tool_hint: Optional[str] = Field(
        default=None,
        description="Suggested executor/tool type (e.g., 'web_search', 'document_retrieval')",
    )
    priority: int = Field(
        default=1,
        ge=1,
        le=5,
        description="Priority 1 (highest) to 5 (lowest)",
    )

    # TODO: Add estimated complexity/cost field
    # TODO: Add retry policy field


class ResearchPlan(BaseModel):
    """A structured research plan produced by the planning layer."""
    plan_id: str = Field(..., description="Unique identifier for this plan")
    goal: str = Field(..., description="The original research goal")
    steps: list[PlanStep] = Field(..., min_length=1, description="Ordered list of plan steps")
    created_at: UTCDateTime = Field(default_factory=lambda: datetime.now(timezone.utc))
    constraints: Optional[str] = Field(
        default=None,
        description="Any constraints on the research (scope, time, sources)",
    )
    revision: int = Field(
        default=0,
        description="Revision number — incremented on re-planning",
    )
    parent_plan_id: Optional[str] = Field(
        default=None,
        description="ID of the plan this was revised from (if re-planned)",
    )

    # TODO: Add estimated total cost field
    # TODO: Add plan-level success criteria

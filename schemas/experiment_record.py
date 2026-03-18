"""
ExperimentRecord — Metadata and results for a single experiment run.

Used by the evaluation layer to track experiments and enable reproducibility.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from schemas._timestamps import UTCDateTime


class ExperimentStatus(str, Enum):
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"


class ExperimentRecord(BaseModel):
    """Full record of an experiment run."""
    experiment_id: str = Field(..., description="Unique identifier (e.g., EXP-001)")
    name: str = Field(..., description="Human-readable experiment name")
    hypothesis: str = Field(..., description="What this experiment tests")
    status: ExperimentStatus = Field(default=ExperimentStatus.PLANNED)

    # Reproducibility fields
    git_commit: Optional[str] = Field(default=None, description="Git commit hash at run time")
    config_snapshot: dict[str, Any] = Field(
        default_factory=dict,
        description="Full configuration used for this run",
    )
    seed: int = Field(default=42, description="Random seed")
    python_version: Optional[str] = None
    dependency_versions: dict[str, str] = Field(
        default_factory=dict,
        description="Key dependency versions (e.g., {'pydantic': '2.6.0'})",
    )

    # Timing
    started_at: Optional[UTCDateTime] = None
    completed_at: Optional[UTCDateTime] = None

    # Results
    metrics: dict[str, float] = Field(
        default_factory=dict,
        description="Measured metrics (e.g., {'accuracy': 0.85, 'completeness': 0.72})",
    )
    artifacts: list[str] = Field(
        default_factory=list,
        description="Paths to result artifacts (logs, outputs, etc.)",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Freeform notes about the run",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if the experiment failed",
    )

    # TODO: Add cost tracking (total API cost, token counts)
    # TODO: Add comparison to baseline metrics

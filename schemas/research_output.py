"""
ResearchOutput — The final output artifact of a complete pipeline run.

Contains every intermediate artifact produced during the run: plan, evidence,
synthesis, verification, and experiment metadata. This is the single object
that gets serialized to disk as the run output.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from schemas._timestamps import UTCDateTime
from schemas.research_plan import ResearchPlan
from schemas.evidence_item import EvidenceItem
from schemas.decision_packet import DecisionPacket
from schemas.verification_result import VerificationResult
from schemas.experiment_record import ExperimentRecord


class ResearchOutput(BaseModel):
    """Complete output of one pipeline run."""
    goal: str = Field(..., description="The original research goal")
    plan: ResearchPlan = Field(..., description="The plan that was executed")
    evidence: list[EvidenceItem] = Field(
        default_factory=list,
        description="All evidence collected during execution",
    )
    decision: Optional[DecisionPacket] = Field(
        default=None,
        description="Synthesized claims from deliberation",
    )
    verification: Optional[VerificationResult] = Field(
        default=None,
        description="Per-claim verification verdicts",
    )
    experiment: Optional[ExperimentRecord] = Field(
        default=None,
        description="Run metadata and metrics",
    )
    created_at: UTCDateTime = Field(default_factory=lambda: datetime.now(timezone.utc))

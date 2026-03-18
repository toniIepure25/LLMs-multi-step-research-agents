"""
DecisionPacket — The output of the deliberation layer.

Contains synthesized claims with epistemic status, conflicts, and reasoning traces.
Fed to verification for constraint checking.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from schemas._timestamps import UTCDateTime


class EpistemicStatus(str, Enum):
    """Confidence level of a claim based on evidence."""
    HIGH_CONFIDENCE = "high_confidence"          # Strong, consistent evidence
    MODERATE_CONFIDENCE = "moderate_confidence"    # Some evidence, minor gaps
    LOW_CONFIDENCE = "low_confidence"              # Weak or conflicting evidence
    CONTESTED = "contested"                        # Significant conflicting evidence
    SPECULATIVE = "speculative"                    # Inference beyond available evidence
    UNKNOWN = "unknown"                            # No relevant evidence found


class Claim(BaseModel):
    """A single claim produced by deliberation."""
    claim_id: str = Field(..., description="Unique identifier")
    text: str = Field(..., description="The claim text")
    epistemic_status: EpistemicStatus = Field(
        default=EpistemicStatus.UNKNOWN,
        description="Confidence based on evidence",
    )
    supporting_evidence_ids: list[str] = Field(
        default_factory=list,
        description="IDs of EvidenceItems supporting this claim",
    )
    contradicting_evidence_ids: list[str] = Field(
        default_factory=list,
        description="IDs of EvidenceItems contradicting this claim",
    )
    reasoning_trace: Optional[str] = Field(
        default=None,
        description="How this claim was derived from the evidence",
    )


class Conflict(BaseModel):
    """A detected conflict between claims or evidence."""
    conflict_id: str
    claim_ids: list[str] = Field(..., min_length=2, description="IDs of conflicting claims")
    description: str = Field(..., description="Nature of the conflict")
    resolution: Optional[str] = Field(
        default=None,
        description="How the conflict was resolved (if at all)",
    )


class DecisionPacket(BaseModel):
    """Output of the Deliberation layer — synthesized claims with reasoning."""
    decision_id: str = Field(..., description="Unique identifier")
    plan_id: str = Field(..., description="ID of the parent ResearchPlan")
    claims: list[Claim] = Field(default_factory=list)
    conflicts: list[Conflict] = Field(default_factory=list)
    synthesis: Optional[str] = Field(
        default=None,
        description="Overall synthesis narrative",
    )
    information_gaps: list[str] = Field(
        default_factory=list,
        description="Topics where evidence is insufficient",
    )
    created_at: UTCDateTime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # TODO: Add confidence distribution across claims
    # TODO: Add link to deliberation strategy used

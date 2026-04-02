"""
CandidateClaimSet — intermediate claim generation output for v1-minimal.

This schema defines the boundary between candidate claim generation and
support-aware claim selection. It preserves claim text, evidence references,
and lightweight provenance without replacing the existing v0 DecisionPacket.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from schemas._timestamps import UTCDateTime
from schemas.decision_packet import EpistemicStatus


class CandidateClaim(BaseModel):
    """A generated claim proposal emitted before final claim selection."""

    candidate_claim_id: str = Field(..., description="Unique identifier")
    source_claim_index: int = Field(
        ...,
        ge=1,
        description="1-based index of the originating claim in the generator response",
    )
    text: str = Field(..., description="Candidate claim text")
    epistemic_status: EpistemicStatus = Field(
        default=EpistemicStatus.UNKNOWN,
        description="Confidence estimated during claim generation",
    )
    supporting_evidence_ids: list[str] = Field(
        ...,
        min_length=1,
        description="IDs of EvidenceItems supporting this candidate claim",
    )
    contradicting_evidence_ids: list[str] = Field(
        default_factory=list,
        description="IDs of EvidenceItems contradicting this candidate claim",
    )
    reasoning_trace: str | None = Field(
        default=None,
        description="Short rationale emitted by the generator",
    )


class CandidateClaimSet(BaseModel):
    """Typed candidate-claim output from deliberation generation."""

    candidate_set_id: str = Field(..., description="Unique identifier")
    plan_id: str = Field(..., description="ID of the parent ResearchPlan")
    claims: list[CandidateClaim] = Field(
        ...,
        min_length=1,
        max_length=4,
        description="Generated candidate claims before final selection",
    )
    draft_synthesis: str | None = Field(
        default=None,
        description="Provisional synthesis text emitted during claim generation",
    )
    information_gaps: list[str] = Field(
        default_factory=list,
        description="Topics where evidence is still insufficient",
    )
    created_at: UTCDateTime = Field(default_factory=lambda: datetime.now(UTC))

"""
VerificationResult — The output of the verification layer.

Contains per-claim verdicts produced by checking claims against evidence.
Verification never modifies claims — it produces a separate result artifact.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from schemas._timestamps import UTCDateTime


class ClaimVerdict(str, Enum):
    """Outcome of verifying a single claim against evidence."""
    SUPPORTED = "supported"            # Evidence exists and references are valid
    UNSUPPORTED = "unsupported"        # No supporting evidence IDs on the claim
    INSUFFICIENT = "insufficient"      # IDs exist but evidence does not support claim
    CONTRADICTED = "contradicted"      # Contradicting evidence outweighs support


class ClaimVerification(BaseModel):
    """Verification result for a single claim."""
    claim_id: str = Field(..., description="ID of the Claim being verified")
    verdict: ClaimVerdict = Field(..., description="Verification outcome")
    supporting_ids_checked: list[str] = Field(
        default_factory=list,
        description="Evidence IDs that were checked as supporting",
    )
    contradicting_ids_checked: list[str] = Field(
        default_factory=list,
        description="Evidence IDs that were checked as contradicting",
    )
    reasoning: str = Field(
        default="",
        description="Why this verdict was assigned",
    )


class VerificationResult(BaseModel):
    """Output of the verification layer — per-claim verdicts without mutating claims."""
    decision_id: str = Field(..., description="ID of the DecisionPacket that was verified")
    claim_verdicts: list[ClaimVerification] = Field(
        default_factory=list,
        description="One verdict per claim in the DecisionPacket",
    )
    summary: str = Field(
        default="",
        description="Human-readable summary (e.g., '4/5 claims supported, 1 insufficient')",
    )
    created_at: UTCDateTime = Field(default_factory=lambda: datetime.now(timezone.utc))

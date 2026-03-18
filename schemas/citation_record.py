"""
CitationRecord — Links a claim to its supporting evidence.

Produced by the Grounding layer, consumed by Verification.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from schemas._timestamps import UTCDateTime


class CitationStrength(str, Enum):
    """How strongly the evidence supports the claim."""
    STRONG = "strong"          # Direct, explicit support
    MODERATE = "moderate"      # Indirect or partial support
    WEAK = "weak"              # Tangential or ambiguous
    CONTRADICTS = "contradicts" # Evidence contradicts the claim


class CitationRecord(BaseModel):
    """A structured link between a claim and its evidence."""
    citation_id: str = Field(..., description="Unique identifier")
    claim_text: str = Field(..., description="The claim being cited")
    evidence_id: str = Field(..., description="ID of the supporting EvidenceItem")
    strength: CitationStrength = Field(
        default=CitationStrength.MODERATE,
        description="How strongly the evidence supports the claim",
    )
    excerpt: Optional[str] = Field(
        default=None,
        description="Specific excerpt from the evidence supporting the claim",
    )
    reasoning: Optional[str] = Field(
        default=None,
        description="Why this evidence supports (or contradicts) the claim",
    )
    created_at: UTCDateTime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # TODO: Add semantic similarity score between claim and evidence

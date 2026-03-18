"""
EvidenceItem — A piece of information produced by the execution layer.

Every EvidenceItem has source attribution and confidence metadata.
These are the atomic units that flow through grounding, memory, and verification.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from schemas._timestamps import UTCDateTime


class SourceType(str, Enum):
    """Where the evidence came from."""
    WEB_SEARCH = "web_search"
    DOCUMENT = "document"
    API = "api"
    DATABASE = "database"
    USER_INPUT = "user_input"
    LLM_GENERATED = "llm_generated"  # For synthesized content — flag for verification


class SourceMetadata(BaseModel):
    """Provenance information for an evidence item."""
    source_type: SourceType
    url: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    publication_date: Optional[str] = None
    access_date: UTCDateTime = Field(default_factory=lambda: datetime.now(timezone.utc))
    raw_snippet: Optional[str] = Field(
        default=None,
        description="Original text snippet before any processing",
    )
    additional: dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific metadata",
    )


class EvidenceItem(BaseModel):
    """A single piece of evidence with source and confidence metadata."""
    evidence_id: str = Field(..., description="Unique identifier")
    task_id: str = Field(..., description="ID of the TaskPacket that produced this")
    content: str = Field(..., description="The evidence content (text)")
    source: SourceMetadata
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence in this evidence (0=none, 1=certain)",
    )
    relevance: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Relevance to the original research goal (0=irrelevant, 1=highly relevant)",
    )
    created_at: UTCDateTime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tags: list[str] = Field(default_factory=list, description="Semantic tags for retrieval")

    # TODO: Add embedding vector field for semantic retrieval
    # TODO: Add normalized/canonical form after grounding

"""
Typed search client abstractions for the v0 execution layer.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Typed request for a web/search lookup."""

    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1)
    metadata: dict[str, str] = Field(default_factory=dict)


class SearchResultItem(BaseModel):
    """Normalized search result returned by a search provider."""

    url: str = Field(..., min_length=1)
    snippet: str = Field(..., min_length=1)
    title: str | None = None
    author: str | None = None
    publication_date: str | None = None
    rank: int = Field(..., ge=1)
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    source_name: str | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    """Typed container for normalized search results."""

    results: list[SearchResultItem] = Field(default_factory=list)


@runtime_checkable
class SearchClientProtocol(Protocol):
    """Minimal async protocol for a search provider client."""

    async def search(self, request: SearchRequest) -> SearchResponse:
        """Execute a search request and return normalized search results."""
        ...

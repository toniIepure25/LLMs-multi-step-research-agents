"""
Simple in-memory working memory for v0.
"""

from __future__ import annotations

from enum import Enum

from asar.core.errors import MemoryStoreError
from schemas.evidence_item import EvidenceItem


class MemoryTier(str, Enum):
    """Explicit memory tiers tracked by the memory module."""

    WORKING = "working"
    COMPRESSED = "compressed"
    EVICTED = "evicted"


class WorkingMemory:
    """Dict-backed `MemoryProtocol` implementation for the v0 evidence set."""

    def __init__(self, max_items: int = 50) -> None:
        if max_items < 1:
            raise ValueError("max_items must be at least 1")
        self._max_items = max_items
        self._items: dict[str, EvidenceItem] = {}
        self._tiers: dict[str, MemoryTier] = {}

    async def store(self, item: EvidenceItem) -> str:
        if item.evidence_id not in self._items and len(self._items) >= self._max_items:
            raise MemoryStoreError(
                "Working memory capacity exceeded",
                details={"max_items": self._max_items, "attempted_id": item.evidence_id},
            )
        self._items[item.evidence_id] = item
        self._tiers[item.evidence_id] = MemoryTier.WORKING
        return item.evidence_id

    async def retrieve(self, query: str, limit: int = 10) -> list[EvidenceItem]:
        if limit < 1:
            return []

        normalized_query = query.strip().casefold()
        ranked: list[tuple[tuple[int, float, float], EvidenceItem]] = []
        for item in self._items.values():
            if self._tiers.get(item.evidence_id) != MemoryTier.WORKING:
                continue

            score = _match_score(item, normalized_query)
            if normalized_query and score == 0:
                continue

            ranking = (score, item.relevance, item.confidence)
            ranked.append((ranking, item))

        ranked.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in ranked[:limit]]

    async def compress(self) -> int:
        return 0

    def get_tier(self, evidence_id: str) -> MemoryTier:
        try:
            return self._tiers[evidence_id]
        except KeyError as exc:
            raise MemoryStoreError(
                "Unknown evidence ID",
                details={"evidence_id": evidence_id},
            ) from exc

    def list_items(self, tier: MemoryTier = MemoryTier.WORKING) -> list[EvidenceItem]:
        return [
            item
            for evidence_id, item in self._items.items()
            if self._tiers.get(evidence_id) == tier
        ]

    def __len__(self) -> int:
        return len(self._items)


def _match_score(item: EvidenceItem, normalized_query: str) -> int:
    if not normalized_query:
        return 1

    haystacks = [
        item.content.casefold(),
        (item.source.title or "").casefold(),
        " ".join(item.tags).casefold(),
    ]
    return sum(1 for haystack in haystacks if normalized_query in haystack)

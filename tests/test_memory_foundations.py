"""
Unit tests for the v0 working memory foundation.
"""

from __future__ import annotations

import pytest

from asar.core.errors import MemoryStoreError
from asar.memory import MemoryTier, WorkingMemory
from schemas.evidence_item import EvidenceItem, SourceMetadata, SourceType


def _evidence(
    evidence_id: str,
    content: str,
    *,
    title: str | None = None,
    tags: list[str] | None = None,
    relevance: float = 0.5,
) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        task_id="task-1",
        content=content,
        source=SourceMetadata(source_type=SourceType.WEB_SEARCH, title=title),
        tags=tags or [],
        relevance=relevance,
    )


@pytest.mark.asyncio
async def test_working_memory_store_retrieve_and_tier() -> None:
    memory = WorkingMemory(max_items=5)
    item = _evidence(
        "e1",
        "Ocean acidification is driven by carbon dioxide absorption.",
        title="Ocean chemistry overview",
        tags=["climate", "ocean"],
        relevance=0.9,
    )

    stored_id = await memory.store(item)
    retrieved = await memory.retrieve("ocean", limit=5)

    assert stored_id == "e1"
    assert retrieved[0].evidence_id == "e1"
    assert memory.get_tier("e1") is MemoryTier.WORKING
    assert memory.list_items() == [item]


@pytest.mark.asyncio
async def test_working_memory_retrieve_ranks_matches() -> None:
    memory = WorkingMemory(max_items=5)
    strong = _evidence(
        "e1",
        "Battery storage costs fell sharply in 2024.",
        title="Battery storage costs",
        tags=["battery", "costs"],
        relevance=0.9,
    )
    weak = _evidence(
        "e2",
        "Wind generation output rose year over year.",
        title="Wind output",
        tags=["wind"],
        relevance=0.4,
    )

    await memory.store(weak)
    await memory.store(strong)

    retrieved = await memory.retrieve("battery", limit=2)

    assert [item.evidence_id for item in retrieved] == ["e1"]


@pytest.mark.asyncio
async def test_working_memory_compress_is_no_op() -> None:
    memory = WorkingMemory(max_items=5)
    await memory.store(_evidence("e1", "A"))

    compressed = await memory.compress()

    assert compressed == 0
    assert len(memory) == 1


@pytest.mark.asyncio
async def test_working_memory_enforces_capacity() -> None:
    memory = WorkingMemory(max_items=1)
    await memory.store(_evidence("e1", "First"))

    with pytest.raises(MemoryStoreError):
        await memory.store(_evidence("e2", "Second"))


def test_working_memory_requires_positive_capacity() -> None:
    with pytest.raises(ValueError):
        WorkingMemory(max_items=0)

"""
Memory — In-memory working storage for the frozen v0 pipeline.

v0 responsibilities:
- Store collected `EvidenceItem`s
- Retrieve stored evidence with simple matching
- Preserve explicit tier semantics even though v0 only uses working memory

Implements: `MemoryProtocol` (see `asar/core/protocols.py`)
Invariant: the tier of every item (working/compressed/evicted) is always queryable

v0 implementation target: `WorkingMemory`
v0 note: `compress()` exists in the protocol but is a no-op in v0

TODO: Implement `WorkingMemory` — dict-backed store/retrieve for v0
TODO: Implement simple retrieval suitable for the small v0 evidence set
FUTURE: compression, eviction, and embedding-based retrieval after v0
"""

from asar.memory.working_memory import MemoryTier, WorkingMemory

__all__ = ["MemoryTier", "WorkingMemory"]

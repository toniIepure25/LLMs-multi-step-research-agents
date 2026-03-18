"""
Execution — Evidence retrieval for the frozen v0 pipeline.

v0 responsibilities:
- Execute a `TaskPacket` via one web/search integration
- Return typed `EvidenceItem`s with `SourceMetadata`
- Remain stateless: all execution context comes from the `TaskPacket`

Implements: `ExecutorProtocol` (see `asar/core/protocols.py`)
Input: `TaskPacket` (see `schemas/task_packet.py`)
Output: `list[EvidenceItem]` (see `schemas/evidence_item.py`)

v0 implementation target: `WebSearchExecutor`
v0 note: no executor registry, no parallel swarm, and no alternative executor families yet

TODO: Implement `WebSearchExecutor` — one search API call per `TaskPacket`
FUTURE: additional executor types and dispatch strategies after v0
"""

from asar.execution.web_search_executor import WebSearchExecutor

__all__ = ["WebSearchExecutor"]

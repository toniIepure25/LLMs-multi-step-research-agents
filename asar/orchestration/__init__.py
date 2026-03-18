"""
Orchestration — Sequential coordination for the frozen v0 pipeline.

v0 responsibilities:
- Accept one research goal and drive the full pipeline
- Call planning, create `TaskPacket`s, and dispatch them sequentially
- Store evidence, trigger deliberation, verification, and evaluation
- Assemble the final `ResearchOutput`

This is the ONLY module that imports and coordinates multiple layers.
Individual layers do not import each other; routing goes through orchestration.

v0 implementation target: `SequentialOrchestrator`
v0 note: no re-planning loop, no parallel dispatch, and no multi-agent routing
"""

from asar.orchestration.sequential_orchestrator import SequentialOrchestrator

__all__ = ["SequentialOrchestrator"]

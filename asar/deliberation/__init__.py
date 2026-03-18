"""
Deliberation — Single-pass synthesis for the frozen v0 pipeline.

v0 responsibilities:
- Synthesize collected evidence into claims
- Preserve conflicts instead of silently resolving them
- Produce a `DecisionPacket` with claims, information gaps, and synthesis text

Implements: `DeliberationProtocol` (see `asar/core/protocols.py`)
Input: `list[EvidenceItem]` + optional context
Output: `DecisionPacket` (see `schemas/decision_packet.py`)

Invariant: conflicts are preserved, not silently resolved

v0 implementation target: `SimpleSynthesizer`
v0 note: no multi-perspective debate, advocate/critic loop, or red-team logic

TODO: Implement `SimpleSynthesizer` — one LLM call over all evidence
FUTURE: debate and multi-perspective deliberation after v0
"""

from asar.deliberation.simple_synthesizer import SimpleSynthesizer

__all__ = ["SimpleSynthesizer"]

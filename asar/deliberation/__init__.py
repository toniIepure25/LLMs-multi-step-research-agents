"""
Deliberation — Single-pass synthesis for the frozen v0 pipeline.

v0 responsibilities:
- Synthesize collected evidence into claims
- Preserve conflicts instead of silently resolving them
- Produce a `DecisionPacket` with claims, information gaps, and synthesis text

v1-minimal preparation:
- `SimpleSynthesizer` can also emit a typed `CandidateClaimSet`
- this creates the boundary between candidate claim generation and later
  support-aware claim selection without changing the frozen v0 protocol yet
- `ClaimSelector` performs deterministic final claim selection without an extra
  LLM step

v1.1 preparation:
- a local `SupportAttributor` helper can provide deterministic support
  attribution signals to selection without activating a full grounding layer

v1.2 preparation:
- a local `MechanismBundler` helper can group raw evidence into compact
  mechanism-family slices before final claim generation

v1.3 preparation:
- a local `MechanismSketcher` helper can preserve compact evidence-grounded
  mechanism sketches before final claim wording

v1.4 preparation:
- a local `MechanismSlotBuilder` helper can preserve compact grounded mechanism
  slots before final claim drafting

v1.5 preparation:
- a local `MechanismSlateSelector` helper can choose a bounded diverse
  mechanism slate before final claim wording

Implements: `DeliberationProtocol` (see `asar/core/protocols.py`)
Input: `list[EvidenceItem]` + optional context
Output: `DecisionPacket` (see `schemas/decision_packet.py`)

Invariant: conflicts are preserved, not silently resolved

v0 implementation target: `SimpleSynthesizer`
v0 note: no multi-perspective debate, advocate/critic loop, or red-team logic

TODO: Implement `SimpleSynthesizer` — one LLM call over all evidence
FUTURE: debate and multi-perspective deliberation after v0
"""

from asar.deliberation.claim_selector import ClaimSelector
from asar.deliberation.mechanism_bundler import MechanismBundler
from asar.deliberation.mechanism_sketcher import MechanismSketcher
from asar.deliberation.mechanism_slate_selector import MechanismSlateSelector
from asar.deliberation.mechanism_slot_builder import MechanismSlotBuilder
from asar.deliberation.simple_synthesizer import SimpleSynthesizer

__all__ = [
    "ClaimSelector",
    "MechanismBundler",
    "MechanismSketcher",
    "MechanismSlateSelector",
    "MechanismSlotBuilder",
    "SimpleSynthesizer",
]

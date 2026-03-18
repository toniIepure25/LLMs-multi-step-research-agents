"""
Verification — Deterministic evidence checking for the frozen v0 pipeline.

v0 responsibilities:
- Check claims against collected `EvidenceItem`s
- Validate referential integrity between claims and evidence IDs
- Return per-claim verdicts in a separate `VerificationResult`

Implements: `VerificationProtocol` (see `asar/core/protocols.py`)
Input: `DecisionPacket` + `list[EvidenceItem]` in v0
Output: `VerificationResult` with per-claim verdicts

Invariant: verification never modifies claims; it returns a separate result artifact
Invariant: verification is separate from generation

v0 implementation target: `EvidenceChecker`
v0 note: this is weak deterministic support checking, not full truth adjudication
v0 note: citation-aware validation starts only when grounding activates in Phase 2
"""

from asar.verification.evidence_checker import EvidenceChecker

__all__ = ["EvidenceChecker"]

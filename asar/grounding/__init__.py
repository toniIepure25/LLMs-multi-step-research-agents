"""
Grounding — Phase 2 evidence normalization and citation linking.

This module exists conceptually in the full ASAR architecture but is postponed in v0.

Phase 2 responsibilities:
- Normalize evidence items into canonical form
- Create `CitationRecord`s linking claims to evidence
- Extract graph-ready facts and provenance chains

Implements: `GroundingProtocol` (see `asar/core/protocols.py`)
Input: `list[EvidenceItem]`
Output: `list[CitationRecord]` + graph triples

Invariant: every output triple links back to a source `EvidenceItem`

TODO: Keep this module inactive until Phase 2 begins
FUTURE: evidence normalization, citation linking, and knowledge-graph support after v0
"""

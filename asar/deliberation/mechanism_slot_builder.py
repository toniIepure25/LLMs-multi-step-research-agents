"""
Deterministic slot-grounded mechanism construction for v1.4.

This helper stays local to deliberation for the first v1.4 step. It does not
introduce a new public schema or change the external pipeline shape. Its job is
to turn evidence-grounded mechanism sketches into a small set of compact slots
that preserve mechanism family, evidence support, and target-event anchoring
before final claim wording.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from asar.deliberation.mechanism_sketcher import MechanismSketcher
from schemas.evidence_item import EvidenceItem

_MAX_GROUNDED_RATIONALE_CHARS = 240
_QUESTION_PREFIXES = (
    "what were the main causes of ",
    "what were the causes of ",
    "what were the main drivers of ",
    "what were the drivers of ",
    "what were the main reasons for ",
    "what were the reasons for ",
    "what caused ",
    "why did ",
)
_TRAILING_EVENT_SUFFIXES = (
    " happen",
    " occur",
)
_WHITESPACE_PATTERN = re.compile(r"\s+")


@dataclass(frozen=True)
class MechanismSlot:
    """Compact internal representation of one grounded mechanism drafting slot."""

    slot_id: str
    family_key: str
    canonical_label: str
    target_event_anchor: str
    supporting_evidence_ids: tuple[str, ...]
    grounded_rationale: str
    source_titles: tuple[str, ...]
    support_diversity_count: int
    family_score: int
    goal_overlap_count: int
    slot_score: int


class MechanismSlotBuilder:
    """Deterministically turn evidence into a bounded set of grounded slots."""

    def __init__(
        self,
        *,
        mechanism_sketcher: MechanismSketcher | None = None,
        max_slots: int = 4,
    ) -> None:
        self._mechanism_sketcher = mechanism_sketcher or MechanismSketcher()
        self._max_slots = max_slots

    def build(
        self,
        evidence: list[EvidenceItem],
        *,
        goal: str | None = None,
    ) -> list[MechanismSlot]:
        """Return a bounded list of grounded mechanism slots."""

        if not evidence:
            return []

        target_event_anchor = _target_event_anchor(goal)
        sketches = self._mechanism_sketcher.sketch(evidence, goal=goal)
        slots: list[MechanismSlot] = []
        for sketch in sketches[: self._max_slots]:
            slot_score = (
                sketch.family_score
                + sketch.support_diversity_count
                + sketch.goal_overlap_count
            )
            slots.append(
                MechanismSlot(
                    slot_id=f"slot_{sketch.family_key}",
                    family_key=sketch.family_key,
                    canonical_label=sketch.mechanism_label,
                    target_event_anchor=target_event_anchor,
                    supporting_evidence_ids=sketch.supporting_evidence_ids,
                    grounded_rationale=_build_grounded_rationale(sketch.grounded_summary),
                    source_titles=sketch.source_titles,
                    support_diversity_count=sketch.support_diversity_count,
                    family_score=sketch.family_score,
                    goal_overlap_count=sketch.goal_overlap_count,
                    slot_score=slot_score,
                )
            )

        slots.sort(
            key=lambda slot: (
                slot.slot_score,
                slot.support_diversity_count,
                slot.goal_overlap_count,
                slot.slot_id,
            ),
            reverse=True,
        )
        return slots


def _target_event_anchor(goal: str | None) -> str:
    if goal is None:
        return "the event in question"

    normalized_goal = goal.strip()
    if not normalized_goal:
        return "the event in question"

    lowered = normalized_goal.lower().rstrip(" ?")
    for prefix in _QUESTION_PREFIXES:
        if lowered.startswith(prefix):
            anchor = normalized_goal[len(prefix) :].strip().rstrip(" ?")
            break
    else:
        anchor = normalized_goal.rstrip(" ?")

    lowered_anchor = anchor.lower()
    for suffix in _TRAILING_EVENT_SUFFIXES:
        if lowered_anchor.endswith(suffix):
            anchor = anchor[: -len(suffix)].rstrip()
            break

    if not anchor:
        return "the event in question"
    return anchor


def _build_grounded_rationale(grounded_summary: str) -> str:
    rationale = _WHITESPACE_PATTERN.sub(" ", grounded_summary.strip())
    if len(rationale) <= _MAX_GROUNDED_RATIONALE_CHARS:
        return rationale
    return rationale[: _MAX_GROUNDED_RATIONALE_CHARS - 3].rstrip() + "..."

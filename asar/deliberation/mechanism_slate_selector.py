"""
Deterministic set-level mechanism slate selection for v1.5.

This helper stays local to deliberation for the first v1.5 step. It does not
introduce a new public schema or change the external pipeline shape. Its job is
to take compact structured mechanism candidates and choose a bounded, diverse,
support-sufficient slate before final claim wording.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace

from asar.deliberation.mechanism_slot_builder import MechanismSlot


@dataclass(frozen=True)
class MechanismSlateEntry:
    """Compact internal representation of one candidate mechanism-slate entry."""

    entry_id: str
    family_key: str
    canonical_label: str
    target_event_anchor: str
    supporting_evidence_ids: tuple[str, ...]
    grounded_rationale: str
    source_titles: tuple[str, ...]
    support_diversity_count: int
    support_sufficiency_score: int
    goal_overlap_count: int
    family_duplication_count: int
    entry_score: int


@dataclass(frozen=True)
class MechanismSlate:
    """Compact internal representation of a selected final mechanism slate."""

    slate_id: str
    target_event_anchor: str
    entries: tuple[MechanismSlateEntry, ...]
    distinct_family_count: int
    duplicated_family_keys: tuple[str, ...]
    total_support_diversity_count: int
    slate_score: int


class MechanismSlateSelector:
    """Deterministically choose a bounded diverse mechanism slate."""

    def __init__(self, *, max_entries: int = 3) -> None:
        self._max_entries = max_entries

    def entries_from_slots(self, slots: list[MechanismSlot]) -> list[MechanismSlateEntry]:
        """Return slate entries derived from existing grounded slots."""

        if not slots:
            return []

        return [
            MechanismSlateEntry(
                entry_id=f"slate_entry_{slot.family_key}",
                family_key=slot.family_key,
                canonical_label=slot.canonical_label,
                target_event_anchor=slot.target_event_anchor,
                supporting_evidence_ids=slot.supporting_evidence_ids,
                grounded_rationale=slot.grounded_rationale,
                source_titles=slot.source_titles,
                support_diversity_count=slot.support_diversity_count,
                support_sufficiency_score=_support_sufficiency_score(slot),
                goal_overlap_count=slot.goal_overlap_count,
                family_duplication_count=0,
                entry_score=slot.slot_score + _support_sufficiency_score(slot),
            )
            for slot in slots
        ]

    def select(
        self,
        entries: list[MechanismSlateEntry],
        *,
        goal: str | None = None,
    ) -> MechanismSlate:
        """Return a bounded slate with no same-family duplication when avoidable."""

        if not entries:
            return MechanismSlate(
                slate_id="slate_empty",
                target_event_anchor=_target_event_anchor(entries, goal),
                entries=(),
                distinct_family_count=0,
                duplicated_family_keys=(),
                total_support_diversity_count=0,
                slate_score=0,
            )

        family_counts = Counter(entry.family_key for entry in entries)
        duplicated_family_keys = tuple(
            sorted(family for family, count in family_counts.items() if count > 1)
        )
        normalized_entries = [
            replace(
                entry,
                family_duplication_count=max(family_counts[entry.family_key] - 1, 0),
            )
            for entry in entries
        ]

        best_entries_by_family: dict[str, MechanismSlateEntry] = {}
        for entry in normalized_entries:
            current_best = best_entries_by_family.get(entry.family_key)
            if current_best is None or _entry_sort_key(entry) > _entry_sort_key(current_best):
                best_entries_by_family[entry.family_key] = entry

        selected_entries = sorted(
            best_entries_by_family.values(),
            key=_entry_sort_key,
            reverse=True,
        )[: self._max_entries]

        selected_entries = tuple(selected_entries)
        return MechanismSlate(
            slate_id=f"slate_{'-'.join(entry.family_key for entry in selected_entries)}",
            target_event_anchor=_target_event_anchor(normalized_entries, goal),
            entries=selected_entries,
            distinct_family_count=len({entry.family_key for entry in selected_entries}),
            duplicated_family_keys=duplicated_family_keys,
            total_support_diversity_count=sum(
                entry.support_diversity_count for entry in selected_entries
            ),
            slate_score=sum(entry.entry_score for entry in selected_entries),
        )

    def select_from_slots(
        self,
        slots: list[MechanismSlot],
        *,
        goal: str | None = None,
    ) -> MechanismSlate:
        """Convenience seam for the current deliberation stack."""

        return self.select(self.entries_from_slots(slots), goal=goal)


def _support_sufficiency_score(slot: MechanismSlot) -> int:
    return (
        min(len(slot.supporting_evidence_ids), 2)
        + min(slot.support_diversity_count, 2)
        + min(slot.goal_overlap_count, 1)
    )


def _entry_sort_key(entry: MechanismSlateEntry) -> tuple[int, int, int, int, int, str]:
    return (
        entry.support_sufficiency_score,
        entry.entry_score,
        entry.support_diversity_count,
        entry.goal_overlap_count,
        len(entry.supporting_evidence_ids),
        entry.canonical_label,
    )


def _target_event_anchor(
    entries: list[MechanismSlateEntry] | tuple[MechanismSlateEntry, ...],
    goal: str | None,
) -> str:
    if entries:
        return entries[0].target_event_anchor
    if goal:
        return goal
    return "the event in question"

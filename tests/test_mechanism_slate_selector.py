"""Unit tests for the deterministic MechanismSlateSelector helper."""

from __future__ import annotations

from asar.deliberation.mechanism_slate_selector import (
    MechanismSlateEntry,
    MechanismSlateSelector,
)
from asar.deliberation.mechanism_slot_builder import MechanismSlotBuilder
from schemas.evidence_item import EvidenceItem, SourceMetadata, SourceType


def _evidence(evidence_id: str, content: str, *, title: str | None = None) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        task_id="task_123",
        content=content,
        source=SourceMetadata(
            source_type=SourceType.WEB_SEARCH,
            title=title or evidence_id,
            url=f"https://example.com/{evidence_id}",
            raw_snippet=content,
        ),
    )


def _entry(
    entry_id: str,
    *,
    family_key: str,
    canonical_label: str,
    supporting_evidence_ids: tuple[str, ...],
    support_diversity_count: int,
    support_sufficiency_score: int,
    entry_score: int,
    target_event_anchor: str = "the 2008 financial crisis",
    goal_overlap_count: int = 1,
    grounded_rationale: str | None = None,
) -> MechanismSlateEntry:
    return MechanismSlateEntry(
        entry_id=entry_id,
        family_key=family_key,
        canonical_label=canonical_label,
        target_event_anchor=target_event_anchor,
        supporting_evidence_ids=supporting_evidence_ids,
        grounded_rationale=grounded_rationale or canonical_label,
        source_titles=tuple(f"title-{evidence_id}" for evidence_id in supporting_evidence_ids),
        support_diversity_count=support_diversity_count,
        support_sufficiency_score=support_sufficiency_score,
        goal_overlap_count=goal_overlap_count,
        family_duplication_count=0,
        entry_score=entry_score,
    )


def test_mechanism_slate_selector_returns_compact_slate_invariants_from_slots() -> None:
    slot_builder = MechanismSlotBuilder()
    selector = MechanismSlateSelector()
    slots = slot_builder.build(
        [
            _evidence(
                "evidence_1",
                "The Smoot-Hawley Tariff reduced world trade during the Great Depression.",
            ),
            _evidence(
                "evidence_2",
                "The stock market crash of 1929 damaged confidence and spending.",
            ),
        ],
        goal="What were the main causes of the Great Depression?",
    )

    slate = selector.select_from_slots(
        slots,
        goal="What were the main causes of the Great Depression?",
    )

    assert slate.slate_id.startswith("slate_")
    assert len(slate.entries) == 2
    assert slate.distinct_family_count == 2
    assert slate.duplicated_family_keys == ()
    assert slate.target_event_anchor == "the Great Depression"
    assert all(entry.family_duplication_count == 0 for entry in slate.entries)
    assert all(entry.support_sufficiency_score >= 1 for entry in slate.entries)
    assert {
        evidence_id
        for entry in slate.entries
        for evidence_id in entry.supporting_evidence_ids
    } == {"evidence_1", "evidence_2"}
    assert slate.total_support_diversity_count == sum(
        entry.support_diversity_count for entry in slate.entries
    )


def test_mechanism_slate_selector_preserves_distinct_2008_mechanisms_over_same_family_duplication(
) -> None:
    selector = MechanismSlateSelector(max_entries=3)
    slate = selector.select(
        [
            _entry(
                "entry_1",
                family_key="securitization",
                canonical_label="Securitization",
                supporting_evidence_ids=("evidence_1", "evidence_2"),
                support_diversity_count=2,
                support_sufficiency_score=5,
                entry_score=11,
                grounded_rationale=(
                    "Thin 2008 evidence ties securitization to systemic mortgage risk."
                ),
            ),
            _entry(
                "entry_2",
                family_key="securitization",
                canonical_label="Mortgage-backed lending",
                supporting_evidence_ids=("evidence_2",),
                support_diversity_count=1,
                support_sufficiency_score=3,
                entry_score=7,
                grounded_rationale=(
                    "Thin 2008 evidence also mentions mortgage-backed lending directly."
                ),
            ),
            _entry(
                "entry_3",
                family_key="otc_derivatives",
                canonical_label="OTC derivatives and deregulation",
                supporting_evidence_ids=("evidence_3", "evidence_4"),
                support_diversity_count=2,
                support_sufficiency_score=5,
                entry_score=10,
                grounded_rationale=(
                    "Thin 2008 evidence links OTC derivatives deregulation to leverage."
                ),
            ),
            _entry(
                "entry_4",
                family_key="monetary_policy",
                canonical_label="Monetary policy and low interest rates",
                supporting_evidence_ids=("evidence_5",),
                support_diversity_count=1,
                support_sufficiency_score=3,
                entry_score=8,
                grounded_rationale=(
                    "Thin 2008 evidence ties low interest rates to excess risk-taking."
                ),
            ),
        ]
    )

    assert len(slate.entries) == 3
    assert slate.distinct_family_count == 3
    assert slate.target_event_anchor == "the 2008 financial crisis"
    assert slate.duplicated_family_keys == ("securitization",)
    assert {entry.family_key for entry in slate.entries} == {
        "securitization",
        "otc_derivatives",
        "monetary_policy",
    }
    assert [entry.canonical_label for entry in slate.entries] == [
        "Securitization",
        "OTC derivatives and deregulation",
        "Monetary policy and low interest rates",
    ]
    assert all(entry.family_duplication_count in {0, 1} for entry in slate.entries)
    assert sum(1 for entry in slate.entries if entry.family_key == "securitization") == 1

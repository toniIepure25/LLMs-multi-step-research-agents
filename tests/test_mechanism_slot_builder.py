"""Unit tests for the deterministic MechanismSlotBuilder helper."""

from __future__ import annotations

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


def test_mechanism_slot_builder_returns_compact_slot_invariants() -> None:
    slot_builder = MechanismSlotBuilder()
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

    assert len(slots) == 2
    assert len({slot.slot_id for slot in slots}) == 2
    assert {
        evidence_id
        for slot in slots
        for evidence_id in slot.supporting_evidence_ids
    } == {
        "evidence_1",
        "evidence_2",
    }
    assert all(slot.canonical_label for slot in slots)
    assert all(slot.grounded_rationale for slot in slots)
    assert all(slot.target_event_anchor == "the Great Depression" for slot in slots)
    assert all(slot.support_diversity_count == len(slot.supporting_evidence_ids) for slot in slots)
    assert all(slot.slot_score >= slot.family_score for slot in slots)


def test_mechanism_slot_builder_recovers_three_2008_grounded_slots_from_thin_evidence() -> None:
    slot_builder = MechanismSlotBuilder()
    slots = slot_builder.build(
        [
            _evidence(
                "evidence_1",
                "Securitization pooled loans into securities sold to investors before 2008.",
            ),
            _evidence(
                "evidence_2",
                (
                    "Subprime mortgage-backed securities destabilized bank "
                    "balance sheets during the crisis."
                ),
            ),
            _evidence(
                "evidence_3",
                (
                    "Deregulation of the OTC derivatives market increased "
                    "leverage before the 2008 financial crisis."
                ),
            ),
            _evidence(
                "evidence_4",
                (
                    "Monetary policy kept interest rates low and encouraged "
                    "excessive risk-taking before 2008."
                ),
            ),
        ],
        goal="What were the main causes of the 2008 financial crisis?",
    )

    assert {slot.family_key for slot in slots} == {
        "securitization",
        "otc_derivatives",
        "monetary_policy",
    }
    assert all(slot.target_event_anchor == "the 2008 financial crisis" for slot in slots)

    securitization_slot = next(slot for slot in slots if slot.family_key == "securitization")
    otc_slot = next(slot for slot in slots if slot.family_key == "otc_derivatives")
    monetary_slot = next(slot for slot in slots if slot.family_key == "monetary_policy")

    assert set(securitization_slot.supporting_evidence_ids) == {"evidence_1", "evidence_2"}
    assert securitization_slot.support_diversity_count == 2
    assert securitization_slot.canonical_label == "Securitization and mortgage-backed lending"
    assert "Securitization and mortgage-backed lending" in securitization_slot.grounded_rationale

    assert otc_slot.supporting_evidence_ids == ("evidence_3",)
    assert otc_slot.canonical_label == "OTC derivatives and deregulation"

    assert monetary_slot.supporting_evidence_ids == ("evidence_4",)
    assert monetary_slot.canonical_label == "Monetary policy and low interest rates"

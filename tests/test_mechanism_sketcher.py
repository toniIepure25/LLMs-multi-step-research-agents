"""Unit tests for the deterministic MechanismSketcher helper."""

from __future__ import annotations

from asar.deliberation.mechanism_sketcher import MechanismSketcher
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


def test_mechanism_sketcher_returns_compact_sketch_invariants() -> None:
    sketcher = MechanismSketcher()
    sketches = sketcher.sketch(
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

    assert len(sketches) == 2
    assert len({sketch.sketch_id for sketch in sketches}) == 2
    assert {
        evidence_id
        for sketch in sketches
        for evidence_id in sketch.supporting_evidence_ids
    } == {
        "evidence_1",
        "evidence_2",
    }
    assert all(sketch.mechanism_label for sketch in sketches)
    assert all(sketch.grounded_summary for sketch in sketches)
    assert all(
        sketch.support_diversity_count == len(sketch.supporting_evidence_ids)
        for sketch in sketches
    )


def test_mechanism_sketcher_recovers_three_2008_mechanism_structures_from_thin_evidence() -> None:
    sketcher = MechanismSketcher()
    sketches = sketcher.sketch(
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

    assert {sketch.family_key for sketch in sketches} == {
        "securitization",
        "otc_derivatives",
        "monetary_policy",
    }
    securitization_sketch = next(
        sketch for sketch in sketches if sketch.family_key == "securitization"
    )
    otc_sketch = next(sketch for sketch in sketches if sketch.family_key == "otc_derivatives")
    monetary_sketch = next(sketch for sketch in sketches if sketch.family_key == "monetary_policy")

    assert set(securitization_sketch.supporting_evidence_ids) == {"evidence_1", "evidence_2"}
    assert securitization_sketch.support_diversity_count == 2
    assert otc_sketch.supporting_evidence_ids == ("evidence_3",)
    assert monetary_sketch.supporting_evidence_ids == ("evidence_4",)
    assert (
        securitization_sketch.mechanism_label
        == "Securitization and mortgage-backed lending"
    )
    assert (
        "Securitization and mortgage-backed lending" in securitization_sketch.grounded_summary
    )
    assert otc_sketch.mechanism_label == "OTC derivatives and deregulation"
    assert monetary_sketch.mechanism_label == "Monetary policy and low interest rates"

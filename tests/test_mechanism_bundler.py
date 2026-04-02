"""Unit tests for the deterministic MechanismBundler helper."""

from __future__ import annotations

from asar.deliberation.mechanism_bundler import MechanismBundler
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


def test_mechanism_bundler_returns_compact_bundle_invariants() -> None:
    bundler = MechanismBundler()
    bundles = bundler.bundle(
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

    assert len(bundles) == 2
    assert len({bundle.bundle_id for bundle in bundles}) == 2
    assert {evidence_id for bundle in bundles for evidence_id in bundle.evidence_ids} == {
        "evidence_1",
        "evidence_2",
    }
    assert all(bundle.mechanism_label for bundle in bundles)
    assert all(bundle.merged_content for bundle in bundles)
    assert all(bundle.support_diversity_count == len(bundle.evidence_ids) for bundle in bundles)


def test_mechanism_bundler_recovers_three_2008_mechanism_slices_from_thin_evidence() -> None:
    bundler = MechanismBundler()
    bundles = bundler.bundle(
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

    assert {bundle.family_key for bundle in bundles} == {
        "securitization",
        "otc_derivatives",
        "monetary_policy",
    }
    securitization_bundle = next(
        bundle for bundle in bundles if bundle.family_key == "securitization"
    )
    otc_bundle = next(bundle for bundle in bundles if bundle.family_key == "otc_derivatives")
    monetary_bundle = next(
        bundle for bundle in bundles if bundle.family_key == "monetary_policy"
    )
    assert set(securitization_bundle.evidence_ids) == {"evidence_1", "evidence_2"}
    assert securitization_bundle.support_diversity_count == 2
    assert otc_bundle.evidence_ids == ("evidence_3",)
    assert monetary_bundle.evidence_ids == ("evidence_4",)
    assert (
        securitization_bundle.mechanism_label
        == "Securitization and mortgage-backed lending"
    )
    assert otc_bundle.mechanism_label == "OTC derivatives and deregulation"
    assert monetary_bundle.mechanism_label == "Monetary policy and low interest rates"

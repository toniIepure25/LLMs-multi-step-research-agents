"""
Unit tests for the deterministic v1-minimal ClaimSelector.
"""

from __future__ import annotations

from asar.deliberation import ClaimSelector
from schemas.candidate_claim_set import CandidateClaim, CandidateClaimSet
from schemas.decision_packet import EpistemicStatus
from schemas.evidence_item import EvidenceItem, SourceMetadata, SourceType


def _candidate(
    candidate_claim_id: str,
    text: str,
    *,
    source_claim_index: int,
    supporting: list[str],
    contradicting: list[str] | None = None,
) -> CandidateClaim:
    return CandidateClaim(
        candidate_claim_id=candidate_claim_id,
        source_claim_index=source_claim_index,
        text=text,
        epistemic_status=EpistemicStatus.MODERATE_CONFIDENCE,
        supporting_evidence_ids=supporting,
        contradicting_evidence_ids=contradicting or [],
    )


def _candidate_set(*claims: CandidateClaim) -> CandidateClaimSet:
    return CandidateClaimSet(
        candidate_set_id="candidate_set_1",
        plan_id="plan_123",
        claims=list(claims),
        draft_synthesis="Draft synthesis.",
    )


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


def test_claim_selector_prefers_supported_broad_claim_over_weak_over_specific_claim() -> None:
    selector = ClaimSelector()
    candidate_set = _candidate_set(
        _candidate(
            "candidate_claim_1",
            "Securitization of subprime mortgages contributed to the 2008 financial crisis.",
            source_claim_index=1,
            supporting=["evidence_1"],
        ),
        _candidate(
            "candidate_claim_2",
            "Securitization contributed to the 2008 financial crisis.",
            source_claim_index=2,
            supporting=["evidence_1", "evidence_2"],
        ),
    )

    selected = selector.select(
        candidate_claim_set=candidate_set,
        evidence=[
            _evidence(
                "evidence_1",
                "Securitization spread mortgage risk throughout the financial system.",
            ),
            _evidence(
                "evidence_2",
                "Securitization weakened underwriting discipline before the crisis.",
            ),
        ],
        goal="What were the main causes of the 2008 financial crisis?",
    )

    assert [claim.text for claim in selected.claims] == [
        "Securitization contributed to the 2008 financial crisis."
    ]


def test_claim_selector_prefers_strongly_attributed_claim_over_plausible_weakly_attributed_claim(
) -> None:
    selector = ClaimSelector(max_selected_claims=1)
    candidate_set = _candidate_set(
        _candidate(
            "candidate_claim_1",
            "Monetary policy contributed to the 2008 financial crisis.",
            source_claim_index=1,
            supporting=["evidence_1", "evidence_2"],
        ),
        _candidate(
            "candidate_claim_2",
            "Subprime lending contributed to the 2008 financial crisis.",
            source_claim_index=2,
            supporting=["evidence_3"],
        ),
    )

    selected = selector.select(
        candidate_claim_set=candidate_set,
        evidence=[
            _evidence(
                "evidence_1",
                "Interest rates stayed low before the 2008 financial crisis.",
            ),
            _evidence(
                "evidence_2",
                "Banks packaged loans into securities before the crisis.",
            ),
            _evidence(
                "evidence_3",
                "Banks issued mortgages to subprime borrowers, and subprime lending "
                "expanded before the 2008 financial crisis.",
            ),
        ],
        goal="What were the main causes of the 2008 financial crisis?",
    )

    assert [claim.text for claim in selected.claims] == [
        "Subprime lending contributed to the 2008 financial crisis."
    ]


def test_claim_selector_prefers_better_supported_same_family_direct_causal_claim() -> None:
    selector = ClaimSelector(max_selected_claims=1)
    candidate_set = _candidate_set(
        _candidate(
            "candidate_claim_1",
            "Securitization contributed to the 2008 financial crisis.",
            source_claim_index=1,
            supporting=["evidence_1"],
        ),
        _candidate(
            "candidate_claim_2",
            "Mortgage securitization contributed to the 2008 financial crisis.",
            source_claim_index=2,
            supporting=["evidence_1", "evidence_2"],
        ),
    )

    selected = selector.select(
        candidate_claim_set=candidate_set,
        evidence=[
            _evidence(
                "evidence_1",
                "Securitization of financial instruments packaged loans into securities.",
            ),
            _evidence(
                "evidence_2",
                "Mortgage securitization weakened underwriting discipline before the crisis.",
            ),
        ],
        goal="What were the main causes of the 2008 financial crisis?",
    )

    assert [claim.text for claim in selected.claims] == [
        "Mortgage securitization contributed to the 2008 financial crisis."
    ]


def test_claim_selector_keeps_one_of_near_duplicate_claims() -> None:
    selector = ClaimSelector()
    candidate_set = _candidate_set(
        _candidate(
            "candidate_claim_1",
            "Securitization contributed to the 2008 financial crisis.",
            source_claim_index=1,
            supporting=["evidence_1"],
        ),
        _candidate(
            "candidate_claim_2",
            "Securitization was a significant contributor to the 2008 financial crisis.",
            source_claim_index=2,
            supporting=["evidence_1"],
        ),
    )

    selected = selector.select(
        candidate_claim_set=candidate_set,
        evidence=[_evidence("evidence_1", "Securitization contributed to the 2008 crisis.")],
        goal="What were the main causes of the 2008 financial crisis?",
    )

    assert len(selected.claims) == 1


def test_claim_selector_preserves_distinct_supported_mechanisms() -> None:
    selector = ClaimSelector()
    candidate_set = _candidate_set(
        _candidate(
            "candidate_claim_1",
            "Securitization contributed to the 2008 financial crisis.",
            source_claim_index=1,
            supporting=["evidence_1"],
        ),
        _candidate(
            "candidate_claim_2",
            "Deregulation of the OTC derivatives market contributed to the 2008 financial crisis.",
            source_claim_index=2,
            supporting=["evidence_2"],
        ),
    )

    selected = selector.select(
        candidate_claim_set=candidate_set,
        evidence=[
            _evidence("evidence_1", "Securitization spread mortgage risk."),
            _evidence("evidence_2", "Deregulation of OTC derivatives increased leverage."),
        ],
        goal="What were the main causes of the 2008 financial crisis?",
    )

    assert [claim.text for claim in selected.claims] == [
        "Securitization contributed to the 2008 financial crisis.",
        "Deregulation of the OTC derivatives market contributed to the 2008 financial crisis.",
    ]


def test_claim_selector_prefers_more_diverse_supported_set_over_same_source_stack() -> None:
    selector = ClaimSelector(max_selected_claims=3)
    candidate_set = _candidate_set(
        _candidate(
            "candidate_claim_1",
            "Bank failures contributed to the Great Depression.",
            source_claim_index=1,
            supporting=["evidence_1"],
        ),
        _candidate(
            "candidate_claim_2",
            "Reduced consumer spending contributed to the Great Depression.",
            source_claim_index=2,
            supporting=["evidence_1"],
        ),
        _candidate(
            "candidate_claim_3",
            "The collapse of world trade due to the Smoot-Hawley Tariff contributed "
            "to the Great Depression.",
            source_claim_index=3,
            supporting=["evidence_2"],
        ),
        _candidate(
            "candidate_claim_4",
            "The stock market crash of 1929 contributed to the Great Depression.",
            source_claim_index=4,
            supporting=["evidence_3"],
        ),
    )

    selected = selector.select(
        candidate_claim_set=candidate_set,
        evidence=[
            _evidence(
                "evidence_1",
                "A broad survey of the Great Depression highlights bank failures and "
                "reduced consumer spending as linked parts of the downturn.",
            ),
            _evidence(
                "evidence_2",
                "The Smoot-Hawley Tariff reduced world trade and deepened the Great Depression.",
            ),
            _evidence(
                "evidence_3",
                "The stock market crash of 1929 undermined confidence and spending.",
            ),
        ],
        goal="What were the main causes of the Great Depression?",
    )

    selected_texts = [claim.text for claim in selected.claims]

    assert (
        "The collapse of world trade due to the Smoot-Hawley Tariff contributed "
        "to the Great Depression."
    ) in selected_texts
    assert "The stock market crash of 1929 contributed to the Great Depression." in selected_texts
    assert sum(
        text in selected_texts
        for text in [
            "Bank failures contributed to the Great Depression.",
            "Reduced consumer spending contributed to the Great Depression.",
        ]
    ) == 1


def test_claim_selector_prefers_exact_goal_event_over_related_alternate_event() -> None:
    selector = ClaimSelector(max_selected_claims=1)
    candidate_set = _candidate_set(
        _candidate(
            "candidate_claim_1",
            "Securitization contributed to the 2008 financial crisis.",
            source_claim_index=1,
            supporting=["evidence_1", "evidence_2"],
        ),
        _candidate(
            "candidate_claim_2",
            "Securitization of subprime mortgages contributed to the housing crisis.",
            source_claim_index=2,
            supporting=["evidence_2", "evidence_3"],
        ),
    )

    selected = selector.select(
        candidate_claim_set=candidate_set,
        evidence=[
            _evidence("evidence_1", "Securitization contributed to the financial crisis."),
            _evidence("evidence_2", "Subprime mortgage securitization deepened the crisis."),
            _evidence("evidence_3", "The housing crisis was fueled by subprime mortgages."),
        ],
        goal="What were the main causes of the 2008 financial crisis?",
    )

    assert [claim.text for claim in selected.claims] == [
        "Securitization contributed to the 2008 financial crisis."
    ]


def test_claim_selector_prefers_sharper_supported_mechanism_over_broad_umbrella_variant() -> None:
    selector = ClaimSelector(max_selected_claims=2)
    candidate_set = _candidate_set(
        _candidate(
            "candidate_claim_1",
            "Deregulation of the financial system contributed to the 2008 financial crisis.",
            source_claim_index=1,
            supporting=["evidence_1", "evidence_2"],
        ),
        _candidate(
            "candidate_claim_2",
            "Deregulation of the OTC derivatives market contributed to the 2008 financial crisis.",
            source_claim_index=2,
            supporting=["evidence_1"],
        ),
        _candidate(
            "candidate_claim_3",
            "Securitization contributed to the 2008 financial crisis.",
            source_claim_index=3,
            supporting=["evidence_3"],
        ),
    )

    selected = selector.select(
        candidate_claim_set=candidate_set,
        evidence=[
            _evidence(
                "evidence_1",
                "Deregulation of the OTC derivatives market increased leverage and risk.",
            ),
            _evidence(
                "evidence_2",
                "Financial deregulation contributed to the crisis more broadly.",
            ),
            _evidence("evidence_3", "Securitization spread mortgage risk."),
        ],
        goal="What were the main causes of the 2008 financial crisis?",
    )

    assert [claim.text for claim in selected.claims] == [
        "Deregulation of the OTC derivatives market contributed to the 2008 financial crisis.",
        "Securitization contributed to the 2008 financial crisis.",
    ]


def test_claim_selector_suppresses_broad_same_family_claim_when_sharper_inflected_variant_exists(
) -> None:
    selector = ClaimSelector(max_selected_claims=3)
    candidate_set = _candidate_set(
        _candidate(
            "candidate_claim_1",
            "Deregulation of the Financial System contributed to the 2008 financial crisis.",
            source_claim_index=1,
            supporting=["evidence_1"],
        ),
        _candidate(
            "candidate_claim_2",
            "The deregulated OTC derivatives market contributed to the 2008 financial crisis.",
            source_claim_index=2,
            supporting=["evidence_2"],
        ),
        _candidate(
            "candidate_claim_3",
            "The securitization of financial instruments contributed to the 2008 financial crisis.",
            source_claim_index=3,
            supporting=["evidence_3"],
        ),
        _candidate(
            "candidate_claim_4",
            "Monetary policy contributed to the 2008 financial crisis.",
            source_claim_index=4,
            supporting=["evidence_4"],
        ),
    )

    selected = selector.select(
        candidate_claim_set=candidate_set,
        evidence=[
            _evidence(
                "evidence_1",
                "Lesson summaries describe deregulation of the financial system broadly.",
            ),
            _evidence(
                "evidence_2",
                "The deregulated OTC derivatives market increased leverage and opacity.",
            ),
            _evidence(
                "evidence_3",
                "The securitization of financial instruments spread risk before 2008.",
            ),
            _evidence("evidence_4", "Monetary policy distorted risk pricing."),
        ],
        goal="What were the main causes of the 2008 financial crisis?",
    )

    assert [claim.text for claim in selected.claims] == [
        "The deregulated OTC derivatives market contributed to the 2008 financial crisis.",
        "The securitization of financial instruments contributed to the 2008 financial crisis.",
        "Monetary policy contributed to the 2008 financial crisis.",
    ]


def test_claim_selector_preserves_distinct_supported_mechanisms_while_dropping_broader_variant(
) -> None:
    selector = ClaimSelector(max_selected_claims=3)
    candidate_set = _candidate_set(
        _candidate(
            "candidate_claim_1",
            "Deregulation of the financial system contributed to the 2008 financial crisis.",
            source_claim_index=1,
            supporting=["evidence_1", "evidence_2"],
        ),
        _candidate(
            "candidate_claim_2",
            "Deregulation of the OTC derivatives market contributed to the 2008 financial crisis.",
            source_claim_index=2,
            supporting=["evidence_1"],
        ),
        _candidate(
            "candidate_claim_3",
            "Securitization contributed to the 2008 financial crisis.",
            source_claim_index=3,
            supporting=["evidence_3"],
        ),
        _candidate(
            "candidate_claim_4",
            "Monetary policy contributed to the 2008 financial crisis.",
            source_claim_index=4,
            supporting=["evidence_4"],
        ),
    )

    selected = selector.select(
        candidate_claim_set=candidate_set,
        evidence=[
            _evidence(
                "evidence_1",
                "Deregulation of the OTC derivatives market increased leverage and risk.",
            ),
            _evidence("evidence_2", "Financial deregulation was a broader background factor."),
            _evidence("evidence_3", "Securitization spread mortgage risk."),
            _evidence("evidence_4", "Monetary policy distorted risk pricing."),
        ],
        goal="What were the main causes of the 2008 financial crisis?",
    )

    assert [claim.text for claim in selected.claims] == [
        "Deregulation of the OTC derivatives market contributed to the 2008 financial crisis.",
        "Securitization contributed to the 2008 financial crisis.",
        "Monetary policy contributed to the 2008 financial crisis.",
    ]


def test_claim_selector_keeps_distinct_supported_mechanisms_while_dropping_thin_same_family_claim(
) -> None:
    selector = ClaimSelector(max_selected_claims=3)
    candidate_set = _candidate_set(
        _candidate(
            "candidate_claim_1",
            "Securitization contributed to the 2008 financial crisis.",
            source_claim_index=1,
            supporting=["evidence_1"],
        ),
        _candidate(
            "candidate_claim_2",
            "Mortgage securitization contributed to the 2008 financial crisis.",
            source_claim_index=2,
            supporting=["evidence_1", "evidence_2"],
        ),
        _candidate(
            "candidate_claim_3",
            "Deregulation of the OTC derivatives market contributed to the 2008 financial crisis.",
            source_claim_index=3,
            supporting=["evidence_3"],
        ),
        _candidate(
            "candidate_claim_4",
            "Monetary policy contributed to the 2008 financial crisis.",
            source_claim_index=4,
            supporting=["evidence_4"],
        ),
    )

    selected = selector.select(
        candidate_claim_set=candidate_set,
        evidence=[
            _evidence(
                "evidence_1",
                "Securitization of financial instruments packaged loans into securities.",
            ),
            _evidence(
                "evidence_2",
                "Mortgage securitization weakened underwriting discipline before the crisis.",
            ),
            _evidence(
                "evidence_3",
                "Deregulation of the OTC derivatives market increased leverage and opacity.",
            ),
            _evidence("evidence_4", "Monetary policy distorted risk pricing."),
        ],
        goal="What were the main causes of the 2008 financial crisis?",
    )

    assert [claim.text for claim in selected.claims] == [
        "Mortgage securitization contributed to the 2008 financial crisis.",
        "Deregulation of the OTC derivatives market contributed to the 2008 financial crisis.",
        "Monetary policy contributed to the 2008 financial crisis.",
    ]


def test_claim_selector_prefers_specific_supported_claims_over_vague_umbrella_claim() -> None:
    selector = ClaimSelector()
    candidate_set = _candidate_set(
        _candidate(
            "candidate_claim_1",
            "A perfect storm of several factors caused the Great Depression.",
            source_claim_index=1,
            supporting=["evidence_1"],
        ),
        _candidate(
            "candidate_claim_2",
            "Bank failures contracted credit and worsened the Great Depression.",
            source_claim_index=2,
            supporting=["evidence_2"],
        ),
        _candidate(
            "candidate_claim_3",
            "Monetary contraction deepened the Great Depression.",
            source_claim_index=3,
            supporting=["evidence_3"],
        ),
    )

    selected = selector.select(
        candidate_claim_set=candidate_set,
        evidence=[
            _evidence("evidence_1", "Some summaries describe several causes."),
            _evidence("evidence_2", "Bank failures contracted credit during the Depression."),
            _evidence("evidence_3", "Monetary contraction deepened the Depression."),
        ],
        goal="What were the main causes of the Great Depression?",
    )

    assert [claim.text for claim in selected.claims] == [
        "Bank failures contracted credit and worsened the Great Depression.",
        "Monetary contraction deepened the Great Depression.",
    ]


def test_claim_selector_prefers_more_diverse_supported_set_over_three_claims_from_one_broad_source(
) -> None:
    selector = ClaimSelector(max_selected_claims=3)
    candidate_set = _candidate_set(
        _candidate(
            "candidate_claim_1",
            "Stock market crashes contributed to the Great Depression.",
            source_claim_index=1,
            supporting=["evidence_1"],
        ),
        _candidate(
            "candidate_claim_2",
            "Bank failures contributed to the Great Depression.",
            source_claim_index=2,
            supporting=["evidence_1"],
        ),
        _candidate(
            "candidate_claim_3",
            (
                "The collapse of world trade due to the Smoot-Hawley Tariff "
                "contributed to the Great Depression."
            ),
            source_claim_index=3,
            supporting=["evidence_2"],
        ),
        _candidate(
            "candidate_claim_4",
            (
                "The worldwide collapse in national money supplies contributed to the "
                "Great Depression."
            ),
            source_claim_index=4,
            supporting=["evidence_3"],
        ),
    )

    selected = selector.select(
        candidate_claim_set=candidate_set,
        evidence=[
            _evidence(
                "evidence_1",
                (
                    "Broad summaries list stock market crashes, bank failures, and reduced "
                    "consumer spending among several causes."
                ),
                title="Top 5 Causes of the Great Depression - ThoughtCo",
            ),
            _evidence(
                "evidence_2",
                (
                    "The collapse of world trade due to the Smoot-Hawley Tariff "
                    "deepened the Depression."
                ),
                title="What Caused the Great Depression? | St. Louis Fed",
            ),
            _evidence(
                "evidence_3",
                "The worldwide collapse in national money supplies deepened the Depression.",
                title="Essays on the Great Depression - JSTOR",
            ),
        ],
        goal="What were the main causes of the Great Depression?",
    )

    assert [claim.text for claim in selected.claims] == [
        "Stock market crashes contributed to the Great Depression.",
        (
            "The collapse of world trade due to the Smoot-Hawley Tariff "
            "contributed to the Great Depression."
        ),
        (
            "The worldwide collapse in national money supplies contributed to the "
            "Great Depression."
        ),
    ]


def test_claim_selector_returns_schema_valid_filtered_candidate_set() -> None:
    selector = ClaimSelector()
    original = _candidate_set(
        _candidate(
            "candidate_claim_1",
            "Securitization contributed to the 2008 financial crisis.",
            source_claim_index=1,
            supporting=["evidence_1"],
        ),
        _candidate(
            "candidate_claim_2",
            "Securitization was a significant contributor to the 2008 financial crisis.",
            source_claim_index=2,
            supporting=["evidence_1"],
        ),
    )

    selected = selector.select(
        candidate_claim_set=original,
        evidence=[_evidence("evidence_1", "Securitization spread risk before 2008.")],
        goal="What were the main causes of the 2008 financial crisis?",
    )

    restored = CandidateClaimSet.model_validate(selected.model_dump())
    assert restored.plan_id == "plan_123"
    assert len(restored.claims) == 1

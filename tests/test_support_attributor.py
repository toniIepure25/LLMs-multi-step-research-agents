"""
Unit tests for the deterministic SupportAttributor helper.
"""

from __future__ import annotations

from asar.deliberation.support_attributor import SupportAttributor
from schemas.candidate_claim_set import CandidateClaim, CandidateClaimSet
from schemas.decision_packet import EpistemicStatus
from schemas.evidence_item import EvidenceItem, SourceMetadata, SourceType


def _candidate(
    candidate_claim_id: str,
    text: str,
    *,
    supporting: list[str],
) -> CandidateClaim:
    return CandidateClaim(
        candidate_claim_id=candidate_claim_id,
        source_claim_index=1,
        text=text,
        epistemic_status=EpistemicStatus.MODERATE_CONFIDENCE,
        supporting_evidence_ids=supporting,
        contradicting_evidence_ids=[],
    )


def _candidate_set(*claims: CandidateClaim) -> CandidateClaimSet:
    return CandidateClaimSet(
        candidate_set_id="candidate_set_1",
        plan_id="plan_123",
        claims=list(claims),
        draft_synthesis="Draft.",
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


def test_support_attributor_returns_ranked_support_metadata() -> None:
    attributor = SupportAttributor()
    candidate_set = _candidate_set(
        _candidate(
            "candidate_claim_1",
            "Deregulation of the OTC derivatives market contributed to the 2008 financial crisis.",
            supporting=["evidence_1", "evidence_2", "evidence_3"],
        )
    )
    attributions = attributor.attribute(
        candidate_claim_set=candidate_set,
        evidence=[
            _evidence(
                "evidence_1",
                "Deregulation of the OTC derivatives market increased leverage "
                "before the 2008 financial crisis.",
            ),
            _evidence(
                "evidence_2",
                "Financial deregulation changed oversight before the crisis.",
            ),
            _evidence(
                "evidence_3",
                "Securitization spread mortgage risk before 2008.",
            ),
        ],
        goal="What were the main causes of the 2008 financial crisis?",
    )

    attribution = attributions["candidate_claim_1"]

    assert attribution.candidate_claim_id == "candidate_claim_1"
    assert attribution.best_supporting_evidence_ids == ("evidence_1", "evidence_2")
    assert set(attribution.attributed_supporting_evidence_ids).issubset(
        {"evidence_1", "evidence_2", "evidence_3"}
    )
    assert attribution.total_support_score >= attribution.best_evidence_score > 0
    assert attribution.support_overlap_count >= attribution.support_event_overlap_count >= 1
    assert "derivatives" not in attribution.unsupported_specificity_tokens


def test_support_attributor_maps_mbs_evidence_to_subprime_lending_family() -> None:
    attributor = SupportAttributor()
    candidate_set = _candidate_set(
        _candidate(
            "candidate_claim_1",
            "Subprime lending contributed to the 2008 financial crisis.",
            supporting=["evidence_1"],
        )
    )
    attributions = attributor.attribute(
        candidate_claim_set=candidate_set,
        evidence=[
            _evidence(
                "evidence_1",
                "Subprime mortgage-backed securities and subprime borrowers destabilized "
                "banks before the 2008 financial crisis.",
            )
        ],
        goal="What were the main causes of the 2008 financial crisis?",
    )

    attribution = attributions["candidate_claim_1"]

    assert attribution.attributed_supporting_evidence_ids == ("evidence_1",)
    assert "lending" in attribution.supported_mechanism_tokens
    assert "lending" not in attribution.unsupported_specificity_tokens
    assert attribution.support_overlap_count >= 2

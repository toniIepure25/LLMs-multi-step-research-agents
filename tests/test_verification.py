"""
Unit tests for the v0 `EvidenceChecker`.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from asar.common import load_settings, setup_logging
from asar.core.errors import VerificationError
from asar.verification import EvidenceChecker
from schemas.decision_packet import Claim, Conflict, DecisionPacket, EpistemicStatus
from schemas.evidence_item import EvidenceItem, SourceMetadata, SourceType
from schemas.verification_result import ClaimVerdict


CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def _evidence(evidence_id: str, content: str) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        task_id="task_123",
        content=content,
        source=SourceMetadata(
            source_type=SourceType.WEB_SEARCH,
            url=f"https://example.com/{evidence_id}",
            title=f"Source for {evidence_id}",
            raw_snippet=content,
        ),
    )


def _claim(
    claim_id: str,
    text: str,
    *,
    supporting_ids: list[str] | None = None,
    contradicting_ids: list[str] | None = None,
) -> Claim:
    return Claim(
        claim_id=claim_id,
        text=text,
        epistemic_status=EpistemicStatus.MODERATE_CONFIDENCE,
        supporting_evidence_ids=supporting_ids or [],
        contradicting_evidence_ids=contradicting_ids or [],
    )


def _decision(*claims: Claim) -> DecisionPacket:
    return DecisionPacket(
        decision_id="decision_123",
        plan_id="plan_123",
        claims=list(claims),
        conflicts=[
            Conflict(
                conflict_id="conflict_123",
                claim_ids=[claim.claim_id for claim in claims[:2]] or ["claim_1", "claim_2"],
                description="Conflict placeholder",
            )
        ]
        if len(claims) >= 2
        else [],
        synthesis="Concise synthesis.",
        information_gaps=[],
    )


@pytest.mark.asyncio
async def test_evidence_checker_marks_supported_claims() -> None:
    settings = load_settings(CONFIG_DIR)
    setup_logging(settings.pipeline.logging, force=True, stream=io.StringIO())
    checker = EvidenceChecker(settings)

    result = await checker.verify(
        _decision(
            _claim(
                "claim_1",
                "Battery storage costs fell across multiple markets in 2024.",
                supporting_ids=["evidence_1"],
            )
        ),
        [_evidence("evidence_1", "Battery storage costs fell across multiple markets in 2024.")],
    )

    assert result.claim_verdicts[0].verdict is ClaimVerdict.SUPPORTED
    assert result.claim_verdicts[0].supporting_ids_checked == ["evidence_1"]


@pytest.mark.asyncio
async def test_evidence_checker_marks_claim_without_supporting_ids_as_unsupported() -> None:
    settings = load_settings(CONFIG_DIR)
    checker = EvidenceChecker(settings)

    result = await checker.verify(
        _decision(_claim("claim_1", "A claim without references.")),
        [_evidence("evidence_1", "Some evidence text.")],
    )

    assert result.claim_verdicts[0].verdict is ClaimVerdict.UNSUPPORTED
    assert "no supporting evidence ids" in result.claim_verdicts[0].reasoning.lower()


@pytest.mark.asyncio
async def test_evidence_checker_marks_missing_supporting_ids_as_insufficient() -> None:
    settings = load_settings(CONFIG_DIR)
    checker = EvidenceChecker(settings)

    result = await checker.verify(
        _decision(
            _claim(
                "claim_1",
                "Battery storage costs fell in 2024.",
                supporting_ids=["evidence_missing"],
            )
        ),
        [],
    )

    assert result.claim_verdicts[0].verdict is ClaimVerdict.INSUFFICIENT
    assert "missing supporting evidence ids" in result.claim_verdicts[0].reasoning.lower()


@pytest.mark.asyncio
async def test_evidence_checker_marks_weak_lexical_support_as_insufficient() -> None:
    settings = load_settings(CONFIG_DIR)
    checker = EvidenceChecker(settings)

    result = await checker.verify(
        _decision(
            _claim(
                "claim_1",
                "Battery storage costs fell in 2024.",
                supporting_ids=["evidence_1"],
            )
        ),
        [_evidence("evidence_1", "Bananas remained a popular export crop in Peru.")],
    )

    assert result.claim_verdicts[0].verdict is ClaimVerdict.INSUFFICIENT
    assert "lexical support threshold" in result.claim_verdicts[0].reasoning.lower()


@pytest.mark.asyncio
async def test_evidence_checker_marks_valid_contradicting_evidence_as_contradicted() -> None:
    settings = load_settings(CONFIG_DIR)
    checker = EvidenceChecker(settings)

    result = await checker.verify(
        _decision(
            _claim(
                "claim_1",
                "Solar installations grew rapidly in 2024.",
                supporting_ids=["evidence_1"],
                contradicting_ids=["evidence_2"],
            )
        ),
        [
            _evidence("evidence_1", "Solar installations grew rapidly in 2024."),
            _evidence("evidence_2", "Solar installations grew slowly in 2024."),
        ],
    )

    assert result.claim_verdicts[0].verdict is ClaimVerdict.CONTRADICTED
    assert result.claim_verdicts[0].contradicting_ids_checked == ["evidence_2"]


@pytest.mark.asyncio
async def test_evidence_checker_aggregates_multiple_claim_verdicts_in_summary() -> None:
    settings = load_settings(CONFIG_DIR)
    checker = EvidenceChecker(settings)

    result = await checker.verify(
        _decision(
            _claim("claim_1", "Battery costs fell in 2024.", supporting_ids=["evidence_1"]),
            _claim("claim_2", "A claim without references."),
            _claim("claim_3", "Wind output declined sharply.", supporting_ids=["evidence_2"]),
        ),
        [
            _evidence("evidence_1", "Battery costs fell in 2024."),
            _evidence("evidence_2", "Wind farms expanded offshore capacity."),
        ],
    )

    verdicts = [verdict.verdict for verdict in result.claim_verdicts]

    assert verdicts == [
        ClaimVerdict.SUPPORTED,
        ClaimVerdict.UNSUPPORTED,
        ClaimVerdict.INSUFFICIENT,
    ]
    assert result.summary == "supported=1, unsupported=1, insufficient=1, contradicted=0"


@pytest.mark.asyncio
async def test_evidence_checker_does_not_mutate_input_decision_packet() -> None:
    settings = load_settings(CONFIG_DIR)
    checker = EvidenceChecker(settings)
    decision = _decision(
        _claim(
            "claim_1",
            "Battery costs fell in 2024.",
            supporting_ids=["evidence_1"],
            contradicting_ids=["evidence_2"],
        )
    )
    before = decision.model_dump()

    await checker.verify(
        decision,
        [
            _evidence("evidence_1", "Battery costs fell in 2024."),
            _evidence("evidence_2", "Battery costs rose in 2024."),
        ],
    )

    assert decision.model_dump() == before


@pytest.mark.asyncio
async def test_evidence_checker_uses_utc_timestamps_and_schema_valid_result() -> None:
    settings = load_settings(CONFIG_DIR)
    checker = EvidenceChecker(settings)

    result = await checker.verify(
        _decision(
            _claim(
                "claim_1",
                "Battery costs fell in 2024.",
                supporting_ids=["evidence_1"],
            )
        ),
        [_evidence("evidence_1", "Battery costs fell in 2024.")],
    )

    assert result.created_at.utcoffset() is not None
    assert result.claim_verdicts[0].claim_id == "claim_1"


@pytest.mark.asyncio
async def test_evidence_checker_handles_empty_evidence_input_explicitly() -> None:
    settings = load_settings(CONFIG_DIR)
    checker = EvidenceChecker(settings)

    result = await checker.verify(
        _decision(
            _claim(
                "claim_1",
                "Battery costs fell in 2024.",
                supporting_ids=["evidence_1"],
            )
        ),
        [],
    )

    assert result.claim_verdicts[0].verdict is ClaimVerdict.INSUFFICIENT
    assert "missing supporting evidence ids" in result.claim_verdicts[0].reasoning.lower()


@pytest.mark.asyncio
async def test_evidence_checker_duplicate_evidence_ids_use_typed_error_path() -> None:
    settings = load_settings(CONFIG_DIR)
    checker = EvidenceChecker(settings)

    result = await checker.verify_result(
        _decision(
            _claim(
                "claim_1",
                "Battery costs fell in 2024.",
                supporting_ids=["evidence_1"],
            )
        ),
        [
            _evidence("evidence_1", "Battery costs fell in 2024."),
            _evidence("evidence_1", "Duplicate evidence item."),
        ],
    )

    assert result.is_error
    assert result.error is not None
    assert result.error.code == "verification_invalid_input"
    assert result.error.details["trace_id"].startswith("trace_")


@pytest.mark.asyncio
async def test_evidence_checker_duplicate_claim_ids_raise_typed_verification_error() -> None:
    settings = load_settings(CONFIG_DIR)
    checker = EvidenceChecker(settings)

    with pytest.raises(VerificationError):
        await checker.verify(
            _decision(
                _claim("claim_1", "First claim.", supporting_ids=["evidence_1"]),
                _claim("claim_1", "Second claim.", supporting_ids=["evidence_2"]),
            ),
            [
                _evidence("evidence_1", "First claim."),
                _evidence("evidence_2", "Second claim."),
            ],
        )

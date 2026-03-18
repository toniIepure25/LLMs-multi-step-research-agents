"""
Minimal deterministic v0 evidence checker.
"""

from __future__ import annotations

import re
from collections import Counter

from asar.common import ASARSettings, generate_trace_id, get_logger, setup_logging
from asar.core.errors import VerificationError
from asar.core.result import OperationResult
from schemas.decision_packet import Claim, DecisionPacket
from schemas.evidence_item import EvidenceItem
from schemas.verification_result import ClaimVerdict, ClaimVerification, VerificationResult


_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "was",
    "were",
    "with",
}


class EvidenceChecker:
    """
    Deterministically verify grounded claims against the provided evidence set.

    v0 heuristic:
    - normalize claim and evidence text to lowercase alphanumeric tokens
    - drop a small stopword list
    - treat lexical support as present when overlap reaches 2 informative tokens,
      or 1 token for very short claims with 3 or fewer informative tokens
    - mark contradiction only when contradicting evidence IDs are valid and meet
      the same lexical-overlap threshold
    """

    def __init__(self, settings: ASARSettings) -> None:
        self._settings = settings
        setup_logging(settings.pipeline.logging)
        self._base_logger_name = "asar.verification.evidence_checker"

    async def verify(self, decision: DecisionPacket, evidence: list[EvidenceItem]) -> VerificationResult:
        """Verify claims or raise a typed verification error."""

        result = await self.verify_result(decision, evidence)
        if result.is_error and result.error is not None:
            raise VerificationError(
                result.error.message,
                details=result.error.details,
                retryable=result.error.retryable,
            )
        return result.unwrap()

    async def verify_result(
        self,
        decision: DecisionPacket,
        evidence: list[EvidenceItem],
    ) -> OperationResult[VerificationResult]:
        """Verify claims while keeping integrity failures inspectable."""

        trace_id = generate_trace_id()
        logger = get_logger(self._base_logger_name, trace_id=trace_id)

        try:
            evidence_index = _index_evidence(evidence)
            _validate_claim_ids(decision)
        except VerificationError as exc:
            return OperationResult.fail(
                "verification_invalid_input",
                exc.message,
                details={**exc.details, "decision_id": decision.decision_id, "trace_id": trace_id},
            )

        logger.info("Verifying decision packet")
        verdicts = [
            _verify_claim(claim, evidence_index)
            for claim in decision.claims
        ]

        result = VerificationResult(
            decision_id=decision.decision_id,
            claim_verdicts=verdicts,
            summary=_build_summary(verdicts),
        )
        logger.info("Verification complete")
        return OperationResult.ok(result)


def _index_evidence(evidence: list[EvidenceItem]) -> dict[str, EvidenceItem]:
    evidence_index: dict[str, EvidenceItem] = {}
    for item in evidence:
        if item.evidence_id in evidence_index:
            raise VerificationError(
                "Evidence IDs must be unique for verification",
                details={"evidence_id": item.evidence_id},
            )
        evidence_index[item.evidence_id] = item
    return evidence_index


def _validate_claim_ids(decision: DecisionPacket) -> None:
    seen_claim_ids: set[str] = set()
    for claim in decision.claims:
        if claim.claim_id in seen_claim_ids:
            raise VerificationError(
                "Claim IDs must be unique for verification",
                details={"claim_id": claim.claim_id},
            )
        seen_claim_ids.add(claim.claim_id)


def _verify_claim(claim: Claim, evidence_index: dict[str, EvidenceItem]) -> ClaimVerification:
    supporting_ids = list(claim.supporting_evidence_ids)
    contradicting_ids = list(claim.contradicting_evidence_ids)

    if not supporting_ids:
        return ClaimVerification(
            claim_id=claim.claim_id,
            verdict=ClaimVerdict.UNSUPPORTED,
            supporting_ids_checked=[],
            contradicting_ids_checked=contradicting_ids,
            reasoning="Claim references no supporting evidence IDs.",
        )

    missing_support_ids = [evidence_id for evidence_id in supporting_ids if evidence_id not in evidence_index]
    missing_contradicting_ids = [
        evidence_id for evidence_id in contradicting_ids if evidence_id not in evidence_index
    ]
    if missing_support_ids or missing_contradicting_ids:
        details = []
        if missing_support_ids:
            details.append(f"missing supporting evidence IDs: {', '.join(missing_support_ids)}")
        if missing_contradicting_ids:
            details.append(f"missing contradicting evidence IDs: {', '.join(missing_contradicting_ids)}")
        return ClaimVerification(
            claim_id=claim.claim_id,
            verdict=ClaimVerdict.INSUFFICIENT,
            supporting_ids_checked=[evidence_id for evidence_id in supporting_ids if evidence_id in evidence_index],
            contradicting_ids_checked=[evidence_id for evidence_id in contradicting_ids if evidence_id in evidence_index],
            reasoning="Claim references invalid evidence: " + "; ".join(details) + ".",
        )

    support_matches = [
        _lexical_match(claim.text, _evidence_text(evidence_index[evidence_id]))
        for evidence_id in supporting_ids
    ]
    contradiction_matches = [
        _lexical_match(claim.text, _evidence_text(evidence_index[evidence_id]))
        for evidence_id in contradicting_ids
    ]

    if any(match.is_supported for match in contradiction_matches):
        strongest = _strongest_match(contradiction_matches)
        return ClaimVerification(
            claim_id=claim.claim_id,
            verdict=ClaimVerdict.CONTRADICTED,
            supporting_ids_checked=supporting_ids,
            contradicting_ids_checked=contradicting_ids,
            reasoning=(
                "Claim has valid contradicting evidence with lexical overlap "
                f"({', '.join(strongest.overlap_tokens)})."
            ),
        )

    if any(match.is_supported for match in support_matches):
        strongest = _strongest_match(support_matches)
        return ClaimVerification(
            claim_id=claim.claim_id,
            verdict=ClaimVerdict.SUPPORTED,
            supporting_ids_checked=supporting_ids,
            contradicting_ids_checked=contradicting_ids,
            reasoning=(
                "Claim has weak lexical support from referenced evidence "
                f"({', '.join(strongest.overlap_tokens)})."
            ),
        )

    strongest = _strongest_match(support_matches)
    return ClaimVerification(
        claim_id=claim.claim_id,
        verdict=ClaimVerdict.INSUFFICIENT,
        supporting_ids_checked=supporting_ids,
        contradicting_ids_checked=contradicting_ids,
        reasoning=(
            "Referenced evidence did not meet the lexical support threshold. "
            f"Strongest overlap was {strongest.overlap_count} informative tokens."
        ),
    )


class _LexicalMatch:
    def __init__(self, *, overlap_tokens: list[str], threshold: int) -> None:
        self.overlap_tokens = overlap_tokens
        self.overlap_count = len(overlap_tokens)
        self.threshold = threshold

    @property
    def is_supported(self) -> bool:
        return self.overlap_count >= self.threshold


def _lexical_match(claim_text: str, evidence_text: str) -> _LexicalMatch:
    claim_tokens = _tokenize(claim_text)
    evidence_tokens = _tokenize(evidence_text)
    overlap_tokens = sorted(claim_tokens & evidence_tokens)
    threshold = 1 if len(claim_tokens) <= 3 else 2
    return _LexicalMatch(overlap_tokens=overlap_tokens, threshold=threshold)


def _tokenize(text: str) -> set[str]:
    return {
        token
        for token in _TOKEN_PATTERN.findall(text.lower())
        if token not in _STOPWORDS
    }


def _evidence_text(evidence: EvidenceItem) -> str:
    if evidence.source.raw_snippet:
        return evidence.source.raw_snippet
    return evidence.content


def _strongest_match(matches: list[_LexicalMatch]) -> _LexicalMatch:
    if not matches:
        return _LexicalMatch(overlap_tokens=[], threshold=2)
    return max(matches, key=lambda match: (match.overlap_count, -match.threshold))


def _build_summary(verdicts: list[ClaimVerification]) -> str:
    counts = Counter(verdict.verdict.value for verdict in verdicts)
    return (
        f"supported={counts.get(ClaimVerdict.SUPPORTED.value, 0)}, "
        f"unsupported={counts.get(ClaimVerdict.UNSUPPORTED.value, 0)}, "
        f"insufficient={counts.get(ClaimVerdict.INSUFFICIENT.value, 0)}, "
        f"contradicted={counts.get(ClaimVerdict.CONTRADICTED.value, 0)}"
    )

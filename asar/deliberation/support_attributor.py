"""
Deterministic support attribution for candidate claims.

This helper stays local to deliberation for the first v1.1 step. It does not
introduce a new broad schema or a full grounding layer. Its job is simply to
attribute the strongest support evidence to each generated candidate so later
selection can rely on explicit support signals instead of raw plausibility
alone.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from schemas.candidate_claim_set import CandidateClaim, CandidateClaimSet
from schemas.evidence_item import EvidenceItem

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
    "did",
    "for",
    "from",
    "how",
    "in",
    "into",
    "is",
    "it",
    "its",
    "main",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "these",
    "this",
    "those",
    "to",
    "was",
    "were",
    "what",
    "which",
    "why",
}
_GENERIC_CAUSAL_TOKENS = {
    "amplified",
    "caused",
    "causes",
    "contributed",
    "contribute",
    "crash",
    "crisis",
    "deepened",
    "driver",
    "drivers",
    "factor",
    "factors",
    "led",
    "main",
    "reasons",
    "responsible",
    "role",
    "sparked",
    "triggered",
    "worsened",
}
_GENERIC_EVENT_TOKENS = {
    "bubble",
    "collapse",
    "crash",
    "crisis",
    "depression",
    "recession",
    "slump",
}
_TOKEN_FAMILY_LABELS = {
    "backed": "securitization",
    "borrower": "lending",
    "borrowers": "lending",
    "deregulated": "deregulation",
    "derivative": "derivatives",
    "derivatives": "derivatives",
    "instrument": "securitization",
    "instruments": "securitization",
    "lending": "lending",
    "otc": "derivatives",
    "regulation": "deregulation",
    "regulatory": "deregulation",
    "securitization": "securitization",
    "securities": "securitization",
    "security": "securitization",
}


@dataclass(frozen=True)
class SupportAttribution:
    """Compact attributed-support view for one candidate claim."""

    candidate_claim_id: str
    attributed_supporting_evidence_ids: tuple[str, ...]
    best_supporting_evidence_ids: tuple[str, ...]
    total_support_score: float
    best_evidence_score: float
    support_overlap_count: int
    support_event_overlap_count: int
    supported_mechanism_tokens: frozenset[str]
    unsupported_specificity_tokens: frozenset[str]
    support_concentration: float


@dataclass(frozen=True)
class _EvidenceAttribution:
    """Internal scored attribution for a single evidence item."""

    evidence_id: str
    score: float
    claim_overlap_tokens: frozenset[str]
    mechanism_overlap_tokens: frozenset[str]
    event_overlap_tokens: frozenset[str]


class SupportAttributor:
    """Deterministically attribute support evidence to candidate claims."""

    def attribute(
        self,
        *,
        candidate_claim_set: CandidateClaimSet,
        evidence: list[EvidenceItem],
        goal: str | None = None,
    ) -> dict[str, SupportAttribution]:
        """Return support metadata keyed by candidate claim id."""

        evidence_by_id = {item.evidence_id: item for item in evidence}
        goal_anchor_tokens = _goal_anchor_tokens(goal)
        goal_event_tokens = _goal_event_tokens(goal)
        return {
            claim.candidate_claim_id: self._attribute_candidate(
                candidate=claim,
                evidence_by_id=evidence_by_id,
                goal_anchor_tokens=goal_anchor_tokens,
                goal_event_tokens=goal_event_tokens,
            )
            for claim in candidate_claim_set.claims
        }

    def _attribute_candidate(
        self,
        *,
        candidate: CandidateClaim,
        evidence_by_id: dict[str, EvidenceItem],
        goal_anchor_tokens: set[str],
        goal_event_tokens: set[str],
    ) -> SupportAttribution:
        claim_tokens = _informative_tokens(candidate.text)
        mechanism_tokens = _mechanism_tokens(candidate.text, goal_anchor_tokens)
        mechanism_family_tokens = _family_tokens(mechanism_tokens)
        evidence_attributions: list[_EvidenceAttribution] = []

        for evidence_id in candidate.supporting_evidence_ids:
            item = evidence_by_id.get(evidence_id)
            if item is None:
                continue
            attributed_evidence = _attribute_evidence(
                evidence_id=evidence_id,
                evidence_text=_evidence_text(item),
                claim_tokens=claim_tokens,
                mechanism_family_tokens=mechanism_family_tokens,
                goal_event_tokens=goal_event_tokens,
            )
            if attributed_evidence.score <= 0:
                continue
            evidence_attributions.append(attributed_evidence)

        evidence_attributions.sort(
            key=lambda item: (item.score, len(item.mechanism_overlap_tokens), item.evidence_id),
            reverse=True,
        )

        attributed_supporting_evidence_ids = tuple(
            item.evidence_id for item in evidence_attributions
        )
        best_supporting_evidence_ids = attributed_supporting_evidence_ids[:2]
        total_support_score = sum(item.score for item in evidence_attributions)
        best_evidence_score = evidence_attributions[0].score if evidence_attributions else 0.0
        supported_claim_tokens = frozenset().union(
            *(item.claim_overlap_tokens for item in evidence_attributions)
        )
        supported_mechanism_tokens = frozenset().union(
            *(item.mechanism_overlap_tokens for item in evidence_attributions)
        )
        supported_event_tokens = frozenset().union(
            *(item.event_overlap_tokens for item in evidence_attributions)
        )
        unsupported_specificity_tokens = frozenset(
            token for token in mechanism_family_tokens if token not in supported_mechanism_tokens
        )
        support_concentration = (
            best_evidence_score / total_support_score if total_support_score > 0 else 0.0
        )
        support_overlap_count = len(supported_claim_tokens) + len(
            supported_mechanism_tokens - supported_claim_tokens
        )

        return SupportAttribution(
            candidate_claim_id=candidate.candidate_claim_id,
            attributed_supporting_evidence_ids=attributed_supporting_evidence_ids,
            best_supporting_evidence_ids=best_supporting_evidence_ids,
            total_support_score=total_support_score,
            best_evidence_score=best_evidence_score,
            support_overlap_count=support_overlap_count,
            support_event_overlap_count=len(supported_event_tokens),
            supported_mechanism_tokens=supported_mechanism_tokens,
            unsupported_specificity_tokens=unsupported_specificity_tokens,
            support_concentration=support_concentration,
        )


def _attribute_evidence(
    *,
    evidence_id: str,
    evidence_text: str,
    claim_tokens: set[str],
    mechanism_family_tokens: set[str],
    goal_event_tokens: set[str],
) -> _EvidenceAttribution:
    evidence_tokens = _informative_tokens(evidence_text)
    evidence_family_tokens = _family_tokens(evidence_tokens)
    claim_overlap_tokens = frozenset(claim_tokens & evidence_tokens)
    mechanism_overlap_tokens = frozenset(mechanism_family_tokens & evidence_family_tokens)
    event_overlap_tokens = frozenset((goal_event_tokens - _GENERIC_EVENT_TOKENS) & evidence_tokens)
    score = (
        (2.0 * len(mechanism_overlap_tokens))
        + (1.5 * len(event_overlap_tokens))
        + (1.0 * len(claim_overlap_tokens))
    )
    return _EvidenceAttribution(
        evidence_id=evidence_id,
        score=score,
        claim_overlap_tokens=claim_overlap_tokens,
        mechanism_overlap_tokens=mechanism_overlap_tokens,
        event_overlap_tokens=event_overlap_tokens,
    )


def _evidence_text(item: EvidenceItem) -> str:
    title = item.source.title or ""
    return f"{title} {item.content}".lower()


def _goal_anchor_tokens(goal: str | None) -> set[str]:
    return {
        token
        for token in _informative_tokens(goal or "")
        if token not in {"cause", "causes", "factor", "factors", "reason", "reasons"}
    }


def _goal_event_tokens(goal: str | None) -> set[str]:
    return _goal_anchor_tokens(goal) - _GENERIC_CAUSAL_TOKENS


def _informative_tokens(text: str) -> set[str]:
    return {
        token
        for token in _TOKEN_PATTERN.findall(text.lower())
        if token not in _STOPWORDS and len(token) > 2
    }


def _mechanism_tokens(text: str, goal_anchor_tokens: set[str]) -> set[str]:
    return {
        token
        for token in _informative_tokens(text)
        if token not in _GENERIC_CAUSAL_TOKENS and token not in goal_anchor_tokens
    }


def _family_tokens(tokens: set[str]) -> set[str]:
    return {_family_label(token) for token in tokens}


def _family_label(token: str) -> str:
    return _TOKEN_FAMILY_LABELS.get(token, token)

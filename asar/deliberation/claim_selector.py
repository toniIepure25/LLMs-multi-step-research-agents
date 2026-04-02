"""
Deterministic claim selection for v1-minimal deliberation.

This component ranks and filters generated candidate claims using only typed
inputs. It is intentionally non-generative and small: support quality,
question relevance, non-duplication, and specificity are handled with simple
inspectable heuristics.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from asar.deliberation.support_attributor import SupportAttribution, SupportAttributor
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
_BROAD_MECHANISM_TOKENS = {
    "conditions",
    "economic",
    "economy",
    "financial",
    "industry",
    "institutions",
    "market",
    "markets",
    "products",
    "sector",
    "services",
    "system",
}
_VAGUE_MARKERS = (
    "perfect storm",
    "various factors",
    "multiple factors",
    "combination of factors",
    "other causes",
    "systemic flaws",
    "several factors",
    "broad factors",
)
_CAUSAL_MARKERS = (
    "caused",
    "contributed",
    "led to",
    "triggered",
    "deepened",
    "worsened",
    "amplified",
    "factor",
    "driver",
    "responsible for",
)


@dataclass(frozen=True)
class _ScoredCandidate:
    """Internal scored view of a candidate claim."""

    candidate: CandidateClaim
    support_attribution: SupportAttribution
    total_score: float
    support_score: float
    support_sufficiency_penalty: float
    relevance_score: float
    event_fidelity_score: float
    specificity_score: float
    overreach_penalty: float
    support_overlap_count: int
    support_event_overlap_count: int
    target_tokens: set[str]
    mechanism_tokens: set[str]
    supported_mechanism_tokens: set[str]
    supported_specific_mechanism_tokens: set[str]
    mechanism_family_tokens: set[str]
    supported_mechanism_family_tokens: set[str]
    supported_specific_family_tokens: set[str]


class ClaimSelector:
    """Deterministically choose the strongest final claim set."""

    def __init__(
        self,
        *,
        max_selected_claims: int = 3,
        support_attributor: SupportAttributor | None = None,
    ) -> None:
        self._max_selected_claims = max_selected_claims
        self._support_attributor = support_attributor or SupportAttributor()

    def select(
        self,
        *,
        candidate_claim_set: CandidateClaimSet,
        evidence: list[EvidenceItem],
        goal: str | None = None,
    ) -> CandidateClaimSet:
        """Return a filtered, reranked candidate set for final packaging."""

        if not candidate_claim_set.claims:
            return candidate_claim_set

        evidence_by_id = {item.evidence_id: item for item in evidence}
        goal_anchor_tokens = _goal_anchor_tokens(goal)
        goal_event_tokens = _goal_event_tokens(goal)
        support_attributions = self._support_attributor.attribute(
            candidate_claim_set=candidate_claim_set,
            evidence=evidence,
            goal=goal,
        )
        scored_candidates = [
            self._score_candidate(
                candidate=claim,
                evidence_by_id=evidence_by_id,
                goal_anchor_tokens=goal_anchor_tokens,
                goal_event_tokens=goal_event_tokens,
                support_attribution=support_attributions[claim.candidate_claim_id],
            )
            for claim in candidate_claim_set.claims
        ]
        ranked_candidates = self._apply_sharper_mechanism_penalties(scored_candidates)
        ranked_candidates = sorted(
            ranked_candidates,
            key=lambda item: (
                item.total_score,
                item.support_score,
                item.relevance_score,
                item.event_fidelity_score,
                len(item.candidate.supporting_evidence_ids),
                -item.candidate.source_claim_index,
            ),
            reverse=True,
        )

        selected: list[CandidateClaim] = []
        selected_scored: list[_ScoredCandidate] = []
        deferred_for_diversity: list[_ScoredCandidate] = []
        for scored_candidate in ranked_candidates:
            candidate = scored_candidate.candidate
            if any(
                _is_lower_fidelity_same_family_variant(scored_candidate, other)
                and other.support_score >= scored_candidate.support_score - 4.5
                for other in ranked_candidates
                if other is not scored_candidate
            ):
                continue
            if any(
                _is_broader_same_family_claim(scored_candidate, existing)
                and existing.support_score >= scored_candidate.support_score - 4.5
                and existing.event_fidelity_score >= scored_candidate.event_fidelity_score
                for existing in selected_scored
            ):
                continue
            if _is_vague_claim(candidate.text) and selected:
                continue
            if any(_are_near_duplicates(candidate, existing) for existing in selected):
                continue
            if _should_defer_for_support_diversity(
                candidate=scored_candidate,
                selected=selected_scored,
                remaining=ranked_candidates,
            ):
                deferred_for_diversity.append(scored_candidate)
                continue
            selected.append(candidate)
            selected_scored.append(scored_candidate)
            if len(selected) >= self._max_selected_claims:
                break

        if len(selected) < self._max_selected_claims:
            for scored_candidate in deferred_for_diversity:
                candidate = scored_candidate.candidate
                if any(_are_near_duplicates(candidate, existing) for existing in selected):
                    continue
                if any(
                    _is_broader_same_family_claim(scored_candidate, existing)
                    and existing.support_score >= scored_candidate.support_score - 4.5
                    and existing.event_fidelity_score >= scored_candidate.event_fidelity_score
                    for existing in selected_scored
                ):
                    continue
                selected.append(candidate)
                selected_scored.append(scored_candidate)
                if len(selected) >= self._max_selected_claims:
                    break

        if not selected:
            selected = [ranked_candidates[0].candidate]

        selected.sort(key=lambda candidate: candidate.source_claim_index)
        return candidate_claim_set.model_copy(update={"claims": selected})

    def _score_candidate(
        self,
        *,
        candidate: CandidateClaim,
        evidence_by_id: dict[str, EvidenceItem],
        goal_anchor_tokens: set[str],
        goal_event_tokens: set[str],
        support_attribution: SupportAttribution,
    ) -> _ScoredCandidate:
        claim_tokens = _informative_tokens(candidate.text)
        mechanism_tokens = _mechanism_tokens(candidate.text, goal_anchor_tokens)
        target_tokens = _claim_target_tokens(candidate.text)
        support_overlap_count = support_attribution.support_overlap_count
        support_event_overlap_count = support_attribution.support_event_overlap_count
        supported_mechanism_tokens = set(support_attribution.supported_mechanism_tokens)
        supported_specific_mechanism_tokens = supported_mechanism_tokens - _BROAD_MECHANISM_TOKENS
        mechanism_family_tokens = _normalized_family_tokens(mechanism_tokens)
        supported_mechanism_family_tokens = _normalized_family_tokens(supported_mechanism_tokens)
        supported_specific_family_tokens = _normalized_family_tokens(
            supported_specific_mechanism_tokens
        )

        support_score = (
            (3.0 * len(support_attribution.attributed_supporting_evidence_ids))
            + (1.25 * support_overlap_count)
            + (0.75 * support_attribution.total_support_score)
            - (3.0 * len(candidate.contradicting_evidence_ids))
        )
        relevance_score = (
            (2.0 * len(claim_tokens & goal_anchor_tokens))
            + (1.0 if _has_causal_language(candidate.text) else 0.0)
        )
        event_fidelity_score = _event_fidelity_score(
            target_tokens=target_tokens,
            goal_event_tokens=goal_event_tokens,
        )
        unsupported_mechanism_tokens = set(support_attribution.unsupported_specificity_tokens)
        overreach_penalty = float(len(unsupported_mechanism_tokens))
        support_sufficiency_penalty = _support_sufficiency_penalty(
            support_count=len(support_attribution.attributed_supporting_evidence_ids),
            support_overlap_count=support_overlap_count,
            support_event_overlap_count=support_event_overlap_count,
            event_fidelity_score=event_fidelity_score,
        )
        specificity_score = (
            (0.75 * len(supported_specific_mechanism_tokens))
            + (0.2 * len(supported_mechanism_tokens & _BROAD_MECHANISM_TOKENS))
            + (0.1 * len(mechanism_tokens - supported_mechanism_tokens))
        )
        if _is_vague_claim(candidate.text):
            specificity_score -= 3.0

        total_score = (
            support_score
            + relevance_score
            + event_fidelity_score
            + specificity_score
            - overreach_penalty
            - support_sufficiency_penalty
        )
        return _ScoredCandidate(
            candidate=candidate,
            support_attribution=support_attribution,
            total_score=total_score,
            support_score=support_score,
            support_sufficiency_penalty=support_sufficiency_penalty,
            relevance_score=relevance_score,
            event_fidelity_score=event_fidelity_score,
            specificity_score=specificity_score,
            overreach_penalty=overreach_penalty,
            support_overlap_count=support_overlap_count,
            support_event_overlap_count=support_event_overlap_count,
            target_tokens=target_tokens,
            mechanism_tokens=mechanism_tokens,
            supported_mechanism_tokens=supported_mechanism_tokens,
            supported_specific_mechanism_tokens=supported_specific_mechanism_tokens,
            mechanism_family_tokens=mechanism_family_tokens,
            supported_mechanism_family_tokens=supported_mechanism_family_tokens,
            supported_specific_family_tokens=supported_specific_family_tokens,
        )

    def _apply_sharper_mechanism_penalties(
        self,
        scored_candidates: list[_ScoredCandidate],
    ) -> list[_ScoredCandidate]:
        adjusted: list[_ScoredCandidate] = []
        for candidate in scored_candidates:
            total_score = candidate.total_score
            if any(
                _is_broader_same_family_claim(candidate, other)
                and other.support_score >= candidate.support_score - 4.5
                and other.event_fidelity_score >= candidate.event_fidelity_score
                for other in scored_candidates
                if other is not candidate
            ):
                total_score -= 2.5
            if any(
                _is_weakly_supported_same_family_variant(candidate, other)
                and other.event_fidelity_score >= candidate.event_fidelity_score
                for other in scored_candidates
                if other is not candidate
            ):
                total_score -= 3.5
            adjusted.append(
                _ScoredCandidate(
                    candidate=candidate.candidate,
                    support_attribution=candidate.support_attribution,
                    total_score=total_score,
                    support_score=candidate.support_score,
                    support_sufficiency_penalty=candidate.support_sufficiency_penalty,
                    relevance_score=candidate.relevance_score,
                    event_fidelity_score=candidate.event_fidelity_score,
                    specificity_score=candidate.specificity_score,
                    overreach_penalty=candidate.overreach_penalty,
                    support_overlap_count=candidate.support_overlap_count,
                    support_event_overlap_count=candidate.support_event_overlap_count,
                    target_tokens=candidate.target_tokens,
                    mechanism_tokens=candidate.mechanism_tokens,
                    supported_mechanism_tokens=candidate.supported_mechanism_tokens,
                    supported_specific_mechanism_tokens=(
                        candidate.supported_specific_mechanism_tokens
                    ),
                    mechanism_family_tokens=candidate.mechanism_family_tokens,
                    supported_mechanism_family_tokens=(
                        candidate.supported_mechanism_family_tokens
                    ),
                    supported_specific_family_tokens=(
                        candidate.supported_specific_family_tokens
                    ),
                )
            )
        return adjusted


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


def _claim_target_tokens(text: str) -> set[str]:
    lowered = text.lower()
    for marker in _CAUSAL_MARKERS:
        if marker not in lowered:
            continue
        _, _, tail = lowered.partition(marker)
        target_tokens = _informative_tokens(tail)
        if target_tokens:
            return target_tokens
    return set()


def _support_overlap(claim_tokens: set[str], support_text: str) -> int:
    return len({token for token in claim_tokens if token in support_text})


def _has_causal_language(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in _CAUSAL_MARKERS)


def _is_vague_claim(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in _VAGUE_MARKERS)


def _event_fidelity_score(*, target_tokens: set[str], goal_event_tokens: set[str]) -> float:
    if not target_tokens or not goal_event_tokens:
        return 0.0

    normalized_target_tokens = target_tokens - _GENERIC_EVENT_TOKENS
    normalized_goal_tokens = goal_event_tokens - _GENERIC_EVENT_TOKENS
    overlap = normalized_target_tokens & normalized_goal_tokens
    alternate_tokens = normalized_target_tokens - normalized_goal_tokens

    if not normalized_target_tokens:
        return 0.0
    return (3.0 * len(overlap)) - (3.5 * len(alternate_tokens))


def _event_support_overlap(*, goal_event_tokens: set[str], support_text: str) -> int:
    normalized_goal_tokens = goal_event_tokens - _GENERIC_EVENT_TOKENS
    return len({token for token in normalized_goal_tokens if token in support_text})


def _support_sufficiency_penalty(
    *,
    support_count: int,
    support_overlap_count: int,
    support_event_overlap_count: int,
    event_fidelity_score: float,
) -> float:
    penalty = 0.0
    if support_count <= 1 and support_overlap_count <= 2:
        penalty += 2.5
    if (
        support_count <= 1
        and support_overlap_count <= 2
        and event_fidelity_score > 0
        and support_event_overlap_count <= 1
    ):
        penalty += 1.5
    return penalty


def _normalized_family_tokens(tokens: set[str]) -> set[str]:
    return {_normalize_family_token(token) for token in tokens}


def _normalize_family_token(token: str) -> str:
    family_aliases = {
        "deregulated": "deregulation",
        "regulatory": "regulation",
        "derivative": "derivatives",
        "mortgages": "mortgage",
        "instruments": "instrument",
    }
    return family_aliases.get(token, token)


def _is_broader_same_family_claim(
    candidate: _ScoredCandidate,
    other: _ScoredCandidate,
) -> bool:
    if (
        not candidate.supported_mechanism_family_tokens
        or not other.supported_mechanism_family_tokens
    ):
        return False
    if candidate.target_tokens != other.target_tokens:
        return False
    shared_family_tokens = (
        candidate.supported_mechanism_family_tokens & other.supported_mechanism_family_tokens
    )
    if not shared_family_tokens:
        return False

    candidate_specific = candidate.supported_specific_family_tokens
    other_specific = other.supported_specific_family_tokens
    if not other_specific:
        return False
    if not shared_family_tokens & other_specific:
        return False
    if not candidate_specific.issubset(other_specific):
        return False
    return len(other_specific) > len(candidate_specific)


def _is_lower_fidelity_same_family_variant(
    candidate: _ScoredCandidate,
    other: _ScoredCandidate,
) -> bool:
    if (
        candidate.event_fidelity_score >= 0
        or other.event_fidelity_score <= candidate.event_fidelity_score
    ):
        return False

    shared_family_tokens = (
        candidate.supported_mechanism_family_tokens & other.supported_mechanism_family_tokens
    )
    if not shared_family_tokens:
        return False
    return True


def _is_weakly_supported_same_family_variant(
    candidate: _ScoredCandidate,
    other: _ScoredCandidate,
) -> bool:
    if candidate.target_tokens != other.target_tokens:
        return False
    shared_family_tokens = (
        candidate.mechanism_family_tokens & other.mechanism_family_tokens
    )
    if not shared_family_tokens:
        return False
    if candidate.support_sufficiency_penalty <= 0:
        return False
    if other.support_score <= candidate.support_score:
        return False
    if other.support_overlap_count <= candidate.support_overlap_count:
        return False
    return True


def _should_defer_for_support_diversity(
    *,
    candidate: _ScoredCandidate,
    selected: list[_ScoredCandidate],
    remaining: list[_ScoredCandidate],
) -> bool:
    if not selected:
        return False

    candidate_support_ids = set(candidate.support_attribution.attributed_supporting_evidence_ids)
    if len(candidate_support_ids) != 1:
        return False

    used_support_ids = {
        evidence_id
        for existing in selected
        for evidence_id in existing.support_attribution.attributed_supporting_evidence_ids
    }
    if candidate_support_ids - used_support_ids:
        return False

    for other in remaining:
        if other is candidate:
            continue
        other_support_ids = set(other.support_attribution.attributed_supporting_evidence_ids)
        if not (other_support_ids - used_support_ids):
            continue
        if _shares_mechanism_family(candidate, other):
            continue
        if other.event_fidelity_score + 0.5 < candidate.event_fidelity_score:
            continue
        if other.support_score + 2.0 < candidate.support_score:
            continue
        if other.total_score + 3.0 < candidate.total_score:
            continue
        return True

    return False


def _shares_mechanism_family(left: _ScoredCandidate, right: _ScoredCandidate) -> bool:
    shared_specific = left.supported_specific_family_tokens & right.supported_specific_family_tokens
    if shared_specific:
        return True
    shared_supported = (
        left.supported_mechanism_family_tokens & right.supported_mechanism_family_tokens
    )
    return bool(shared_supported)


def _are_near_duplicates(left: CandidateClaim, right: CandidateClaim) -> bool:
    left_tokens = _informative_tokens(left.text)
    right_tokens = _informative_tokens(right.text)
    if not left_tokens or not right_tokens:
        return False

    token_overlap = len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
    shared_support = bool(
        set(left.supporting_evidence_ids) & set(right.supporting_evidence_ids)
    )
    return token_overlap >= 0.75 or (shared_support and token_overlap >= 0.55)

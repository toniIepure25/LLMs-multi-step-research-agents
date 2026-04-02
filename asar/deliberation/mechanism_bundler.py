"""
Deterministic mechanism-oriented evidence bundling for v1.2.

This helper stays local to deliberation for the first v1.2 step. It does not
introduce a new schema or a full grounding layer. Its job is to compress raw
EvidenceItems into a few stable mechanism-family slices before final claim
generation so the prompt is less sensitive to live budget pressure and wording
variance.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

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
    "reason",
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
_MAX_BUNDLE_CONTENT_CHARS = 360
_MAX_MEMBER_CONTENT_CHARS = 120
_MAX_FALLBACK_LABEL_TOKENS = 3
_FAMILY_DEFINITIONS = (
    (
        "securitization",
        "Securitization and mortgage-backed lending",
        frozenset(
            {
                "backed",
                "borrower",
                "borrowers",
                "loan",
                "loans",
                "mbs",
                "mortgage",
                "mortgages",
                "securitization",
                "security",
                "securities",
                "subprime",
                "underwriting",
            }
        ),
    ),
    (
        "otc_derivatives",
        "OTC derivatives and deregulation",
        frozenset(
            {
                "counterparties",
                "counterparty",
                "deregulated",
                "deregulation",
                "derivative",
                "derivatives",
                "glass",
                "otc",
                "regulation",
                "regulatory",
                "steagall",
                "swap",
                "swaps",
            }
        ),
    ),
    (
        "monetary_policy",
        "Monetary policy and low interest rates",
        frozenset(
            {
                "credit",
                "federal",
                "interest",
                "liquidity",
                "monetary",
                "policies",
                "policy",
                "rate",
                "rates",
                "reserve",
            }
        ),
    ),
    (
        "banking_panic",
        "Bank failures and banking panics",
        frozenset(
            {
                "bank",
                "bankers",
                "banking",
                "banks",
                "credit",
                "failure",
                "failures",
                "panic",
                "panics",
            }
        ),
    ),
    (
        "stock_crash",
        "Stock market crash",
        frozenset(
            {
                "1929",
                "crash",
                "equities",
                "market",
                "shares",
                "stock",
                "street",
                "wall",
            }
        ),
    ),
    (
        "trade_protectionism",
        "Protectionism and world trade collapse",
        frozenset(
            {
                "hawley",
                "protectionism",
                "smoot",
                "tariff",
                "tariffs",
                "trade",
                "world",
            }
        ),
    ),
    (
        "reparations",
        "War reparations",
        frozenset({"reparation", "reparations", "war"}),
    ),
    (
        "dotcom_speculation",
        "Dot-com speculation",
        frozenset(
            {
                "bubble",
                "com",
                "dot",
                "dotcom",
                "internet",
                "speculation",
                "speculative",
                "speculators",
            }
        ),
    ),
    (
        "dotcom_overvaluation",
        "Tech overvaluation",
        frozenset(
            {
                "companies",
                "overvaluation",
                "overvalued",
                "tech",
                "technology",
                "valuation",
                "valuations",
            }
        ),
    ),
    (
        "dotcom_regulation",
        "Tech regulation",
        frozenset(
            {
                "industry",
                "oversight",
                "regulation",
                "regulations",
                "regulatory",
                "tech",
                "technology",
            }
        ),
    ),
)


@dataclass(frozen=True)
class MechanismBundle:
    """Compact internal representation of a mechanism-family evidence slice."""

    bundle_id: str
    family_key: str
    mechanism_label: str
    evidence_ids: tuple[str, ...]
    source_titles: tuple[str, ...]
    merged_content: str
    support_diversity_count: int
    family_score: int
    goal_overlap_count: int


@dataclass(frozen=True)
class _ScoredEvidence:
    """Internal scored view of evidence before bundle assembly."""

    evidence: EvidenceItem
    family_key: str
    mechanism_label: str
    family_score: int
    goal_overlap_count: int
    bundle_text: str


class MechanismBundler:
    """Deterministically group evidence into compact mechanism-family bundles."""

    def bundle(
        self,
        evidence: list[EvidenceItem],
        *,
        goal: str | None = None,
    ) -> list[MechanismBundle]:
        if not evidence:
            return []

        goal_anchor_tokens = _goal_anchor_tokens(goal)
        scored_evidence = [
            self._score_evidence(item=item, goal_anchor_tokens=goal_anchor_tokens)
            for item in evidence
        ]

        grouped: dict[str, list[_ScoredEvidence]] = {}
        for scored in scored_evidence:
            grouped.setdefault(scored.family_key, []).append(scored)

        bundles: list[MechanismBundle] = []
        for family_key, members in grouped.items():
            members.sort(
                key=lambda member: (
                    member.family_score,
                    member.goal_overlap_count,
                    member.evidence.evidence_id,
                ),
                reverse=True,
            )
            evidence_ids = tuple(member.evidence.evidence_id for member in members)
            source_titles = tuple(
                dict.fromkeys(
                    (member.evidence.source.title or "")
                    for member in members
                    if (member.evidence.source.title or "")
                )
            )
            merged_content = _truncate_text(
                " ".join(member.bundle_text for member in members),
                _MAX_BUNDLE_CONTENT_CHARS,
            )
            bundles.append(
                MechanismBundle(
                    bundle_id=f"bundle_{family_key}",
                    family_key=family_key,
                    mechanism_label=members[0].mechanism_label,
                    evidence_ids=evidence_ids,
                    source_titles=source_titles,
                    merged_content=merged_content,
                    support_diversity_count=len(evidence_ids),
                    family_score=sum(member.family_score for member in members),
                    goal_overlap_count=sum(member.goal_overlap_count for member in members),
                )
            )

        bundles.sort(
            key=lambda bundle: (
                bundle.family_score,
                bundle.support_diversity_count,
                bundle.goal_overlap_count,
                bundle.bundle_id,
            ),
            reverse=True,
        )
        return bundles

    def _score_evidence(
        self,
        *,
        item: EvidenceItem,
        goal_anchor_tokens: set[str],
    ) -> _ScoredEvidence:
        evidence_text = _evidence_text(item)
        evidence_tokens = _informative_tokens(evidence_text)
        mechanism_tokens = evidence_tokens - goal_anchor_tokens - _GENERIC_CAUSAL_TOKENS
        family_key, mechanism_label, family_score = _best_family_match(mechanism_tokens)
        if not family_key:
            family_key, mechanism_label = _fallback_family(item=item, tokens=mechanism_tokens)
            family_score = 1
        goal_overlap_count = len(evidence_tokens & goal_anchor_tokens)
        bundle_text = (
            f"[{item.evidence_id}] "
            f"{_truncate_text(item.content, _MAX_MEMBER_CONTENT_CHARS)}"
        )
        return _ScoredEvidence(
            evidence=item,
            family_key=family_key,
            mechanism_label=mechanism_label,
            family_score=family_score,
            goal_overlap_count=goal_overlap_count,
            bundle_text=bundle_text,
        )


def _best_family_match(tokens: set[str]) -> tuple[str | None, str | None, int]:
    best: tuple[str | None, str | None, int] = (None, None, 0)
    for family_key, mechanism_label, family_tokens in _FAMILY_DEFINITIONS:
        score = len(tokens & family_tokens)
        if score > best[2]:
            best = (family_key, mechanism_label, score)
    return best


def _fallback_family(*, item: EvidenceItem, tokens: set[str]) -> tuple[str, str]:
    label_tokens = sorted(tokens)[:_MAX_FALLBACK_LABEL_TOKENS]
    if label_tokens:
        mechanism_label = " / ".join(label_tokens)
    else:
        mechanism_label = item.source.title or item.evidence_id
    return f"misc_{item.evidence_id}", mechanism_label


def _goal_anchor_tokens(goal: str | None) -> set[str]:
    return {
        token
        for token in _informative_tokens(goal or "")
        if token not in {"cause", "causes", "factor", "factors", "reason", "reasons"}
        and token not in _GENERIC_EVENT_TOKENS
    }


def _evidence_text(item: EvidenceItem) -> str:
    title = item.source.title or ""
    return f"{title} {item.content}".lower()


def _informative_tokens(text: str) -> set[str]:
    return {
        token
        for token in _TOKEN_PATTERN.findall(text.lower())
        if token not in _STOPWORDS and len(token) > 2
    }


def _truncate_text(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."

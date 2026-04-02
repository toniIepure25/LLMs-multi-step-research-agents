"""
Deterministic evidence-grounded mechanism sketching for v1.3.

This helper stays local to deliberation for the first v1.3 step. It does not
introduce a new public schema or change the external pipeline shape. Its job is
to turn raw evidence into a small set of compact mechanism sketches before
final claim wording so later integration can rely on a more stable intermediate
representation than a flat evidence list alone.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from asar.deliberation.mechanism_bundler import MechanismBundler
from schemas.evidence_item import EvidenceItem

_EVIDENCE_TAG_PATTERN = re.compile(r"\[evidence_[^\]]+\]\s*")
_MAX_GROUNDED_SUMMARY_CHARS = 220


@dataclass(frozen=True)
class MechanismSketch:
    """Compact internal representation of one evidence-grounded mechanism."""

    sketch_id: str
    family_key: str
    mechanism_label: str
    supporting_evidence_ids: tuple[str, ...]
    grounded_summary: str
    source_titles: tuple[str, ...]
    support_diversity_count: int
    family_score: int
    goal_overlap_count: int


class MechanismSketcher:
    """Deterministically convert evidence into a bounded sketch set."""

    def __init__(
        self,
        *,
        mechanism_bundler: MechanismBundler | None = None,
        max_sketches: int = 4,
    ) -> None:
        self._mechanism_bundler = mechanism_bundler or MechanismBundler()
        self._max_sketches = max_sketches

    def sketch(
        self,
        evidence: list[EvidenceItem],
        *,
        goal: str | None = None,
    ) -> list[MechanismSketch]:
        """Return a bounded list of deterministic mechanism sketches."""

        if not evidence:
            return []

        bundles = self._mechanism_bundler.bundle(evidence, goal=goal)
        sketches: list[MechanismSketch] = []
        for bundle in bundles[: self._max_sketches]:
            sketches.append(
                MechanismSketch(
                    sketch_id=f"sketch_{bundle.family_key}",
                    family_key=bundle.family_key,
                    mechanism_label=bundle.mechanism_label,
                    supporting_evidence_ids=bundle.evidence_ids,
                    grounded_summary=_build_grounded_summary(
                        bundle.mechanism_label,
                        bundle.merged_content,
                    ),
                    source_titles=bundle.source_titles,
                    support_diversity_count=bundle.support_diversity_count,
                    family_score=bundle.family_score,
                    goal_overlap_count=bundle.goal_overlap_count,
                )
            )
        return sketches


def _build_grounded_summary(mechanism_label: str, merged_content: str) -> str:
    content = _EVIDENCE_TAG_PATTERN.sub("", merged_content).strip()
    summary = f"{mechanism_label}: {content}" if content else mechanism_label
    if len(summary) <= _MAX_GROUNDED_SUMMARY_CHARS:
        return summary
    return summary[: _MAX_GROUNDED_SUMMARY_CHARS - 3].rstrip() + "..."

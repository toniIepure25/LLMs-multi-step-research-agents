"""
Safety-aware wrapper around the v0 orchestrator.

This wrapper is the **only** integration point between the safety layer and
the rest of the pipeline. It does three things:

1. **Pre-flight check** on the goal *before* invoking the orchestrator.
   If the goal is unsafe, the run is blocked and no plan / search / LLM
   call is ever made.
2. **Calls the orchestrator** normally.
3. **Post-flight check** on the produced evidence and claims. If a claim
   trips the safety filter, the corresponding `ResearchOutput` is returned
   *with the offending claim removed* and a `safety.json` artifact is
   written alongside `output.json` describing exactly what happened.

The orchestrator itself is not modified — this respects the v0 architectural
freeze while still adding a real safety surface to the pipeline.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from asar.safety import SafetyChecker, SafetyConfig, SafetyReport, build_safety_filter
from schemas.research_output import ResearchOutput


@dataclass(frozen=True)
class SafetyOutcome:
    """Result of a safety-aware run."""

    blocked_pre: bool
    blocked_post: bool
    pre_report: SafetyReport
    post_report: SafetyReport | None
    output: ResearchOutput | None
    blocked_reason: str | None = None


class SafetyAwareRunner:
    """Run the orchestrator with input + output safety checks."""

    def __init__(
        self,
        *,
        orchestrator: Any,
        checker: SafetyChecker | None = None,
        config: SafetyConfig | None = None,
    ) -> None:
        self._orchestrator = orchestrator
        self._checker = checker or build_safety_filter(config=config)
        self._config = config or SafetyConfig()

    async def run(self, goal: str, constraints: dict | None = None, **kwargs: Any) -> SafetyOutcome:
        # 1. Pre-flight check on the goal alone.
        pre_report = self._checker.report(goal=goal)
        if pre_report.blocked:
            return SafetyOutcome(
                blocked_pre=True,
                blocked_post=False,
                pre_report=pre_report,
                post_report=None,
                output=None,
                blocked_reason="goal_failed_safety_check",
            )

        # 2. Run the pipeline.
        output = await self._orchestrator.run(goal, constraints=constraints, **kwargs)

        # 3. Post-flight check on evidence + claims.
        evidence_pairs = [(ev.evidence_id, ev.content) for ev in output.evidence]
        claim_pairs = self._extract_claims(output)
        post_report = self._checker.report(
            goal=goal,
            evidence=evidence_pairs,
            claims=claim_pairs,
        )

        filtered_output = output
        if post_report.blocked:
            filtered_output = self._strip_unsafe_claims(output, post_report)

        # 4. Persist safety.json alongside the output artifact (best effort).
        self._persist_safety_artifact(output, pre_report, post_report)

        return SafetyOutcome(
            blocked_pre=False,
            blocked_post=post_report.blocked,
            pre_report=pre_report,
            post_report=post_report,
            output=filtered_output,
            blocked_reason="claim_failed_safety_check" if post_report.blocked else None,
        )

    # -- helpers ---------------------------------------------------------

    def _extract_claims(self, output: ResearchOutput) -> list[tuple[str, str]]:
        if output.decision is None:
            return []
        pairs: list[tuple[str, str]] = []
        for claim in output.decision.claims:
            claim_id = getattr(claim, "claim_id", None) or "claim"
            statement = getattr(claim, "statement", None) or ""
            if statement:
                pairs.append((claim_id, statement))
        return pairs

    def _strip_unsafe_claims(self, output: ResearchOutput, report: SafetyReport) -> ResearchOutput:
        unsafe_claim_ids = {v.text_id for v in report.verdicts if v.text_kind == "claim" and not v.is_safe}
        if not unsafe_claim_ids or output.decision is None:
            return output
        kept_claims = [c for c in output.decision.claims if c.claim_id not in unsafe_claim_ids]
        # Pydantic-immutable: rebuild via model_copy if available.
        new_decision = output.decision.model_copy(update={"claims": kept_claims})
        new_verification = output.verification
        if new_verification is not None and hasattr(new_verification, "claim_verdicts"):
            new_verification = new_verification.model_copy(
                update={
                    "claim_verdicts": [
                        v for v in new_verification.claim_verdicts
                        if v.claim_id not in unsafe_claim_ids
                    ]
                }
            )
        return output.model_copy(
            update={"decision": new_decision, "verification": new_verification},
        )

    def _persist_safety_artifact(
        self,
        output: ResearchOutput,
        pre_report: SafetyReport,
        post_report: SafetyReport | None,
    ) -> None:
        record = getattr(output, "experiment", None)
        if record is None or not record.artifacts:
            return
        try:
            output_path = Path(record.artifacts[0])
            run_dir = output_path.parent
            safety_path = run_dir / "safety.json"
            payload = {
                "pre_report": pre_report.to_dict(),
                "post_report": post_report.to_dict() if post_report is not None else None,
            }
            safety_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except OSError:
            return

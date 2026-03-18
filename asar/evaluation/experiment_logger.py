"""
Minimal v0 experiment logger and metric calculator.
"""

from __future__ import annotations

import json
import platform
import re
from pathlib import Path

import pydantic

from asar.common import ASARSettings, IDPrefix, generate_id, generate_trace_id, get_logger, setup_logging
from asar.core.errors import EvaluationError
from asar.core.result import OperationResult
from schemas.decision_packet import DecisionPacket
from schemas.evidence_item import EvidenceItem
from schemas.experiment_record import ExperimentRecord, ExperimentStatus
from schemas.research_output import ResearchOutput
from schemas.research_plan import ResearchPlan
from schemas.verification_result import ClaimVerdict, VerificationResult


class ExperimentLogger:
    """Compute v0 metrics and persist one run's artifacts to disk."""

    def __init__(self, settings: ASARSettings, *, output_dir: str | Path | None = None) -> None:
        self._settings = settings
        self._output_dir = self._resolve_output_dir(output_dir)
        setup_logging(settings.pipeline.logging)
        self._base_logger_name = "asar.evaluation.experiment_logger"

    async def evaluate(self, run_artifacts: dict) -> dict:
        """Compute v0 evaluation metrics from pipeline artifacts."""

        plan, evidence, decision, verification = self._parse_run_artifacts(run_artifacts)
        return self._compute_metrics(plan=plan, evidence=evidence, decision=decision, verification=verification)

    async def log_experiment(self, record: ExperimentRecord) -> None:
        """Persist an existing experiment record to disk."""

        run_dir = self._infer_run_dir(record)
        run_dir.mkdir(parents=True, exist_ok=True)
        self._write_json(run_dir / "experiment.json", record.model_dump(mode="json"))

    async def record_run(
        self,
        *,
        plan: ResearchPlan,
        evidence: list[EvidenceItem],
        decision: DecisionPacket,
        verification: VerificationResult,
        name: str | None = None,
        hypothesis: str | None = None,
        notes: str | None = None,
        git_commit: str | None = None,
    ) -> ExperimentRecord:
        """Build an `ExperimentRecord`, write run artifacts, and return the record."""

        result = await self.record_run_result(
            plan=plan,
            evidence=evidence,
            decision=decision,
            verification=verification,
            name=name,
            hypothesis=hypothesis,
            notes=notes,
            git_commit=git_commit,
        )
        if result.is_error and result.error is not None:
            raise EvaluationError(
                result.error.message,
                details=result.error.details,
                retryable=result.error.retryable,
            )
        return result.unwrap()

    async def record_run_result(
        self,
        *,
        plan: ResearchPlan,
        evidence: list[EvidenceItem],
        decision: DecisionPacket,
        verification: VerificationResult,
        name: str | None = None,
        hypothesis: str | None = None,
        notes: str | None = None,
        git_commit: str | None = None,
    ) -> OperationResult[ExperimentRecord]:
        """Build and persist a run record while keeping failures inspectable."""

        trace_id = generate_trace_id()
        logger = get_logger(self._base_logger_name, trace_id=trace_id)

        try:
            metrics = self._compute_metrics(
                plan=plan,
                evidence=evidence,
                decision=decision,
                verification=verification,
            )
            experiment_id = generate_id(IDPrefix.EXPERIMENT)
            run_dir = self._build_run_dir(
                completed_at=verification.created_at,
                goal=plan.goal,
                experiment_id=experiment_id,
            )
            artifacts = [
                str((run_dir / "output.json").resolve()),
                str((run_dir / "experiment.json").resolve()),
            ]
            record = ExperimentRecord(
                experiment_id=experiment_id,
                name=name or f"asar-v0-{_slugify(plan.goal)}",
                hypothesis=hypothesis or _DEFAULT_HYPOTHESIS,
                status=ExperimentStatus.COMPLETED,
                git_commit=git_commit,
                config_snapshot=self._settings.model_dump(mode="json"),
                seed=self._settings.experiments.defaults.seed,
                python_version=platform.python_version(),
                dependency_versions={"pydantic": pydantic.__version__},
                started_at=plan.created_at,
                completed_at=verification.created_at,
                metrics=metrics,
                artifacts=artifacts,
                notes=notes,
            )
            output = ResearchOutput(
                goal=plan.goal,
                plan=plan,
                evidence=evidence,
                decision=decision,
                verification=verification,
                experiment=record,
            )
            self._write_run_artifacts(run_dir=run_dir, output=output, record=record)
        except EvaluationError as exc:
            logger.error("Experiment logging failed")
            return OperationResult.fail(
                "evaluation_invalid_input",
                exc.message,
                details={**exc.details, "trace_id": trace_id},
            )
        except OSError as exc:
            logger.error("Experiment artifact write failed")
            return OperationResult.fail(
                "evaluation_write_failed",
                "Unable to write experiment artifacts",
                details={"trace_id": trace_id, "error": str(exc)},
            )

        logger.info("Experiment artifacts written")
        return OperationResult.ok(record)

    def _parse_run_artifacts(
        self,
        run_artifacts: dict,
    ) -> tuple[ResearchPlan, list[EvidenceItem], DecisionPacket, VerificationResult]:
        try:
            plan = ResearchPlan.model_validate(run_artifacts["plan"])
            evidence = [EvidenceItem.model_validate(item) for item in run_artifacts["evidence"]]
            decision = DecisionPacket.model_validate(run_artifacts["decision"])
            verification = VerificationResult.model_validate(run_artifacts["verification"])
        except KeyError as exc:
            raise EvaluationError(
                "Run artifacts were missing a required key",
                details={"missing_key": str(exc)},
            ) from exc
        except Exception as exc:
            raise EvaluationError(
                "Run artifacts could not be validated",
                details={"error": str(exc)},
            ) from exc
        return plan, evidence, decision, verification

    def _compute_metrics(
        self,
        *,
        plan: ResearchPlan,
        evidence: list[EvidenceItem],
        decision: DecisionPacket,
        verification: VerificationResult,
    ) -> dict[str, float]:
        self._validate_consistency(plan=plan, evidence=evidence, decision=decision, verification=verification)

        claim_ids = [claim.claim_id for claim in decision.claims]
        supported_claim_count = sum(
            1 for verdict in verification.claim_verdicts if verdict.verdict is ClaimVerdict.SUPPORTED
        )
        referenced_evidence_ids = _collect_referenced_evidence_ids(decision)
        evidence_ids = {item.evidence_id for item in evidence}
        covered_step_ids = _collect_covered_step_ids(plan=plan, evidence=evidence)

        groundedness = supported_claim_count / len(claim_ids) if claim_ids else 0.0
        evidence_utilization = (
            len(referenced_evidence_ids & evidence_ids) / len(evidence_ids) if evidence_ids else 0.0
        )
        plan_coverage = len(covered_step_ids) / len(plan.steps) if plan.steps else 0.0

        return {
            "groundedness": groundedness,
            "evidence_utilization": evidence_utilization,
            "plan_coverage": plan_coverage,
            "number_of_claims": float(len(claim_ids)),
            "number_of_evidence_items": float(len(evidence_ids)),
            "number_of_supported_claims": float(supported_claim_count),
        }

    def _validate_consistency(
        self,
        *,
        plan: ResearchPlan,
        evidence: list[EvidenceItem],
        decision: DecisionPacket,
        verification: VerificationResult,
    ) -> None:
        if decision.plan_id != plan.plan_id:
            raise EvaluationError(
                "DecisionPacket plan_id did not match ResearchPlan",
                details={"plan_id": plan.plan_id, "decision_plan_id": decision.plan_id},
            )
        if verification.decision_id != decision.decision_id:
            raise EvaluationError(
                "VerificationResult decision_id did not match DecisionPacket",
                details={"decision_id": decision.decision_id, "verification_decision_id": verification.decision_id},
            )

        step_ids = [step.step_id for step in plan.steps]
        if len(step_ids) != len(set(step_ids)):
            raise EvaluationError("ResearchPlan step IDs must be unique")

        evidence_ids = [item.evidence_id for item in evidence]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise EvaluationError("Evidence IDs must be unique for evaluation")

        claim_ids = [claim.claim_id for claim in decision.claims]
        if len(claim_ids) != len(set(claim_ids)):
            raise EvaluationError("Claim IDs must be unique for evaluation")

        verdict_ids = [verdict.claim_id for verdict in verification.claim_verdicts]
        if len(verdict_ids) != len(set(verdict_ids)):
            raise EvaluationError("Verification claim IDs must be unique for evaluation")
        if set(verdict_ids) != set(claim_ids):
            raise EvaluationError(
                "VerificationResult claim verdicts must match DecisionPacket claims exactly",
                details={"decision_claim_ids": sorted(claim_ids), "verification_claim_ids": sorted(verdict_ids)},
            )

    def _resolve_output_dir(self, output_dir: str | Path | None) -> Path:
        if output_dir is None:
            configured = Path(self._settings.experiments.defaults.output_dir)
            if configured.is_absolute():
                return configured
            return (self._settings.config_dir.parent / configured).resolve()

        resolved = Path(output_dir)
        if resolved.is_absolute():
            return resolved
        return resolved.resolve()

    def _build_run_dir(self, *, completed_at, goal: str, experiment_id: str) -> Path:
        timestamp = completed_at.strftime("%Y%m%dT%H%M%SZ")
        slug = _slugify(goal)
        return self._output_dir / f"{timestamp}_{slug}_{experiment_id}"

    def _infer_run_dir(self, record: ExperimentRecord) -> Path:
        if record.artifacts:
            return Path(record.artifacts[0]).resolve().parent
        return self._output_dir / record.experiment_id

    def _write_run_artifacts(
        self,
        *,
        run_dir: Path,
        output: ResearchOutput,
        record: ExperimentRecord,
    ) -> None:
        run_dir.mkdir(parents=True, exist_ok=False)
        self._write_json(run_dir / "output.json", output.model_dump(mode="json"))
        self._write_json(run_dir / "experiment.json", record.model_dump(mode="json"))

    def _write_json(self, path: Path, payload: dict) -> None:
        path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


_DEFAULT_HYPOTHESIS = "The frozen v0 ASAR pipeline can produce grounded single-goal research artifacts."


def _collect_referenced_evidence_ids(decision: DecisionPacket) -> set[str]:
    referenced_ids: set[str] = set()
    for claim in decision.claims:
        referenced_ids.update(claim.supporting_evidence_ids)
        referenced_ids.update(claim.contradicting_evidence_ids)
    return referenced_ids


def _collect_covered_step_ids(plan: ResearchPlan, evidence: list[EvidenceItem]) -> set[str]:
    known_step_ids = {step.step_id for step in plan.steps}
    covered_step_ids: set[str] = set()
    for item in evidence:
        explicit_step_id = item.source.additional.get("step_id")
        if isinstance(explicit_step_id, str) and explicit_step_id in known_step_ids:
            covered_step_ids.add(explicit_step_id)
            continue
        if item.task_id in known_step_ids:
            covered_step_ids.add(item.task_id)
    return covered_step_ids


def _slugify(text: str) -> str:
    collapsed = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return collapsed[:40] or "run"

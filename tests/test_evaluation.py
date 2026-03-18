"""
Unit tests for the v0 `ExperimentLogger`.
"""

from __future__ import annotations

import io
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from asar.common import load_settings, setup_logging
from asar.evaluation import ExperimentLogger
from schemas.decision_packet import Claim, DecisionPacket, EpistemicStatus
from schemas.evidence_item import EvidenceItem, SourceMetadata, SourceType
from schemas.experiment_record import ExperimentRecord
from schemas.research_plan import PlanStep, ResearchPlan, StepDependencyType
from schemas.verification_result import ClaimVerdict, ClaimVerification, VerificationResult


CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
FIXED_TIME = datetime(2026, 3, 17, 10, 0, 0, tzinfo=timezone.utc)


def _plan() -> ResearchPlan:
    return ResearchPlan(
        plan_id="plan_123",
        goal="Assess battery storage cost trends in 2024",
        steps=[
            PlanStep(
                step_id="step_1",
                description="Find current market reports",
                expected_output="A set of current market reports",
                success_criteria="At least one recent report is found",
                dependency_type=StepDependencyType.SEQUENTIAL,
                depends_on=[],
            ),
            PlanStep(
                step_id="step_2",
                description="Compare regional price movements",
                expected_output="Regional comparisons",
                success_criteria="At least two regions are compared",
                dependency_type=StepDependencyType.SEQUENTIAL,
                depends_on=["step_1"],
            ),
            PlanStep(
                step_id="step_3",
                description="Summarize the key cost drivers",
                expected_output="A short driver summary",
                success_criteria="Key drivers are named",
                dependency_type=StepDependencyType.SEQUENTIAL,
                depends_on=["step_2"],
            ),
        ],
        created_at=FIXED_TIME,
    )


def _evidence(
    evidence_id: str,
    content: str,
    *,
    step_id: str | None = None,
) -> EvidenceItem:
    additional = {}
    if step_id is not None:
        additional["step_id"] = step_id
    return EvidenceItem(
        evidence_id=evidence_id,
        task_id=f"task_{evidence_id}",
        content=content,
        source=SourceMetadata(
            source_type=SourceType.WEB_SEARCH,
            url=f"https://example.com/{evidence_id}",
            title=f"Source for {evidence_id}",
            raw_snippet=content,
            additional=additional,
        ),
    )


def _decision(*claims: Claim) -> DecisionPacket:
    return DecisionPacket(
        decision_id="decision_123",
        plan_id="plan_123",
        claims=list(claims),
        conflicts=[],
        synthesis="Concise synthesis.",
        information_gaps=[],
        created_at=FIXED_TIME,
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


def _verification(*verdicts: ClaimVerification) -> VerificationResult:
    return VerificationResult(
        decision_id="decision_123",
        claim_verdicts=list(verdicts),
        summary="summary",
        created_at=FIXED_TIME,
    )


def _verdict(claim_id: str, verdict: ClaimVerdict) -> ClaimVerification:
    return ClaimVerification(
        claim_id=claim_id,
        verdict=verdict,
        supporting_ids_checked=[],
        contradicting_ids_checked=[],
        reasoning="deterministic check",
    )


@pytest.mark.asyncio
async def test_experiment_logger_happy_path_returns_valid_record_and_writes_artifacts(tmp_path: Path) -> None:
    settings = load_settings(CONFIG_DIR)
    setup_logging(settings.pipeline.logging, force=True, stream=io.StringIO())
    logger = ExperimentLogger(settings, output_dir=tmp_path)

    record = await logger.record_run(
        plan=_plan(),
        evidence=[
            _evidence("evidence_1", "Battery costs fell in 2024.", step_id="step_1"),
            _evidence("evidence_2", "Regional prices diverged in 2024.", step_id="step_2"),
        ],
        decision=_decision(
            _claim("claim_1", "Battery costs fell in 2024.", supporting_ids=["evidence_1"]),
            _claim("claim_2", "Regional prices diverged in 2024.", supporting_ids=["evidence_2"]),
        ),
        verification=_verification(
            _verdict("claim_1", ClaimVerdict.SUPPORTED),
            _verdict("claim_2", ClaimVerdict.SUPPORTED),
        ),
    )

    assert isinstance(record, ExperimentRecord)
    assert record.experiment_id.startswith("experiment_")
    assert record.status.value == "completed"
    assert len(record.artifacts) == 2
    assert Path(record.artifacts[0]).name == "output.json"
    assert Path(record.artifacts[1]).name == "experiment.json"
    assert Path(record.artifacts[0]).exists()
    assert Path(record.artifacts[1]).exists()


@pytest.mark.asyncio
async def test_experiment_logger_computes_groundedness() -> None:
    settings = load_settings(CONFIG_DIR)
    logger = ExperimentLogger(settings)

    metrics = await logger.evaluate(
        {
            "plan": _plan(),
            "evidence": [
                _evidence("evidence_1", "Battery costs fell in 2024.", step_id="step_1"),
                _evidence("evidence_2", "Regional prices diverged in 2024.", step_id="step_2"),
            ],
            "decision": _decision(
                _claim("claim_1", "Battery costs fell in 2024.", supporting_ids=["evidence_1"]),
                _claim("claim_2", "Regional prices diverged in 2024.", supporting_ids=["evidence_2"]),
            ),
            "verification": _verification(
                _verdict("claim_1", ClaimVerdict.SUPPORTED),
                _verdict("claim_2", ClaimVerdict.INSUFFICIENT),
            ),
        }
    )

    assert metrics["groundedness"] == 0.5
    assert metrics["number_of_supported_claims"] == 1.0


@pytest.mark.asyncio
async def test_experiment_logger_computes_evidence_utilization() -> None:
    settings = load_settings(CONFIG_DIR)
    logger = ExperimentLogger(settings)

    metrics = await logger.evaluate(
        {
            "plan": _plan(),
            "evidence": [
                _evidence("evidence_1", "Battery costs fell in 2024.", step_id="step_1"),
                _evidence("evidence_2", "Regional prices diverged in 2024.", step_id="step_2"),
                _evidence("evidence_3", "A third source.", step_id="step_3"),
            ],
            "decision": _decision(
                _claim("claim_1", "Battery costs fell in 2024.", supporting_ids=["evidence_1"]),
                _claim("claim_2", "Regional prices diverged in 2024.", supporting_ids=["evidence_2"]),
            ),
            "verification": _verification(
                _verdict("claim_1", ClaimVerdict.SUPPORTED),
                _verdict("claim_2", ClaimVerdict.SUPPORTED),
            ),
        }
    )

    assert metrics["evidence_utilization"] == pytest.approx(2 / 3)


@pytest.mark.asyncio
async def test_experiment_logger_computes_plan_coverage_from_explicit_step_linkage() -> None:
    settings = load_settings(CONFIG_DIR)
    logger = ExperimentLogger(settings)

    metrics = await logger.evaluate(
        {
            "plan": _plan(),
            "evidence": [
                _evidence("evidence_1", "Battery costs fell in 2024.", step_id="step_1"),
                _evidence("evidence_2", "Regional prices diverged in 2024.", step_id="step_2"),
            ],
            "decision": _decision(
                _claim("claim_1", "Battery costs fell in 2024.", supporting_ids=["evidence_1"]),
                _claim("claim_2", "Regional prices diverged in 2024.", supporting_ids=["evidence_2"]),
            ),
            "verification": _verification(
                _verdict("claim_1", ClaimVerdict.SUPPORTED),
                _verdict("claim_2", ClaimVerdict.SUPPORTED),
            ),
        }
    )

    assert metrics["plan_coverage"] == pytest.approx(2 / 3)


@pytest.mark.asyncio
async def test_experiment_logger_writes_stable_json_artifacts(tmp_path: Path) -> None:
    settings = load_settings(CONFIG_DIR)
    logger = ExperimentLogger(settings, output_dir=tmp_path)

    record = await logger.record_run(
        plan=_plan(),
        evidence=[_evidence("evidence_1", "Battery costs fell in 2024.", step_id="step_1")],
        decision=_decision(_claim("claim_1", "Battery costs fell in 2024.", supporting_ids=["evidence_1"])),
        verification=_verification(_verdict("claim_1", ClaimVerdict.SUPPORTED)),
    )

    output_payload = json.loads(Path(record.artifacts[0]).read_text(encoding="utf-8"))
    experiment_payload = json.loads(Path(record.artifacts[1]).read_text(encoding="utf-8"))

    assert output_payload["goal"] == "Assess battery storage cost trends in 2024"
    assert experiment_payload["experiment_id"] == record.experiment_id
    assert experiment_payload["metrics"]["groundedness"] == 1.0


@pytest.mark.asyncio
async def test_experiment_logger_uses_utc_timestamps_and_schema_valid_record(tmp_path: Path) -> None:
    settings = load_settings(CONFIG_DIR)
    logger = ExperimentLogger(settings, output_dir=tmp_path)

    record = await logger.record_run(
        plan=_plan(),
        evidence=[_evidence("evidence_1", "Battery costs fell in 2024.", step_id="step_1")],
        decision=_decision(_claim("claim_1", "Battery costs fell in 2024.", supporting_ids=["evidence_1"])),
        verification=_verification(_verdict("claim_1", ClaimVerdict.SUPPORTED)),
    )

    assert record.started_at is not None
    assert record.completed_at is not None
    assert record.started_at.utcoffset() is not None
    assert record.completed_at.utcoffset() is not None


@pytest.mark.asyncio
async def test_experiment_logger_returns_typed_failure_for_inconsistent_inputs(tmp_path: Path) -> None:
    settings = load_settings(CONFIG_DIR)
    logger = ExperimentLogger(settings, output_dir=tmp_path)
    bad_decision = DecisionPacket(
        decision_id="decision_123",
        plan_id="plan_other",
        claims=[],
        conflicts=[],
        synthesis="bad",
        information_gaps=[],
        created_at=FIXED_TIME,
    )

    result = await logger.record_run_result(
        plan=_plan(),
        evidence=[],
        decision=bad_decision,
        verification=_verification(),
    )

    assert result.is_error
    assert result.error is not None
    assert result.error.code == "evaluation_invalid_input"
    assert result.error.details["trace_id"].startswith("trace_")


@pytest.mark.asyncio
async def test_experiment_logger_handles_empty_evidence_and_empty_claims() -> None:
    settings = load_settings(CONFIG_DIR)
    logger = ExperimentLogger(settings)

    metrics = await logger.evaluate(
        {
            "plan": _plan(),
            "evidence": [],
            "decision": _decision(),
            "verification": _verification(),
        }
    )

    assert metrics["groundedness"] == 0.0
    assert metrics["evidence_utilization"] == 0.0
    assert metrics["plan_coverage"] == 0.0
    assert metrics["number_of_claims"] == 0.0


@pytest.mark.asyncio
async def test_experiment_logger_repeated_runs_create_separate_directories(tmp_path: Path) -> None:
    settings = load_settings(CONFIG_DIR)
    logger = ExperimentLogger(settings, output_dir=tmp_path)

    first = await logger.record_run(
        plan=_plan(),
        evidence=[_evidence("evidence_1", "Battery costs fell in 2024.", step_id="step_1")],
        decision=_decision(_claim("claim_1", "Battery costs fell in 2024.", supporting_ids=["evidence_1"])),
        verification=_verification(_verdict("claim_1", ClaimVerdict.SUPPORTED)),
    )
    second = await logger.record_run(
        plan=_plan(),
        evidence=[_evidence("evidence_1", "Battery costs fell in 2024.", step_id="step_1")],
        decision=_decision(_claim("claim_1", "Battery costs fell in 2024.", supporting_ids=["evidence_1"])),
        verification=_verification(_verdict("claim_1", ClaimVerdict.SUPPORTED)),
    )

    assert Path(first.artifacts[0]).parent != Path(second.artifacts[0]).parent

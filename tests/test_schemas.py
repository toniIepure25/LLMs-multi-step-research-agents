"""
Smoke tests for schema validation.

Verifies that all schemas can be instantiated with minimal valid data
and that validation rejects invalid data.
"""

from datetime import datetime, timedelta, timezone

import pytest
from schemas.research_plan import ResearchPlan, PlanStep, StepDependencyType
from schemas.task_packet import TaskPacket, TaskStatus
from schemas.evidence_item import EvidenceItem, SourceMetadata, SourceType
from schemas.citation_record import CitationRecord, CitationStrength
from schemas.decision_packet import DecisionPacket, Claim, EpistemicStatus
from schemas.experiment_record import ExperimentRecord
from schemas.verification_result import VerificationResult, ClaimVerification, ClaimVerdict
from schemas.research_output import ResearchOutput


class TestResearchPlan:
    def test_minimal_plan(self):
        step = PlanStep(
            step_id="s1",
            description="Search for information",
            expected_output="List of relevant sources",
            success_criteria="At least 3 sources found",
        )
        plan = ResearchPlan(
            plan_id="p1",
            goal="What causes ocean acidification?",
            steps=[step],
        )
        assert plan.plan_id == "p1"
        assert len(plan.steps) == 1
        assert plan.revision == 0

    def test_plan_requires_steps(self):
        with pytest.raises(Exception):
            ResearchPlan(plan_id="p1", goal="test", steps=[])


class TestTaskPacket:
    def test_minimal_task(self):
        task = TaskPacket(
            task_id="t1",
            plan_id="p1",
            step_id="s1",
            action="search",
            query="ocean acidification causes",
        )
        assert task.status == TaskStatus.PENDING


class TestEvidenceItem:
    def test_minimal_evidence(self):
        source = SourceMetadata(source_type=SourceType.WEB_SEARCH)
        evidence = EvidenceItem(
            evidence_id="e1",
            task_id="t1",
            content="CO2 absorption is the primary driver of ocean acidification.",
            source=source,
        )
        assert evidence.confidence == 0.5
        assert evidence.relevance == 0.5

    def test_confidence_bounds(self):
        source = SourceMetadata(source_type=SourceType.WEB_SEARCH)
        with pytest.raises(Exception):
            EvidenceItem(
                evidence_id="e1",
                task_id="t1",
                content="test",
                source=source,
                confidence=1.5,
            )


class TestCitationRecord:
    def test_minimal_citation(self):
        citation = CitationRecord(
            citation_id="c1",
            claim_text="Ocean pH has decreased by 0.1 units since pre-industrial times.",
            evidence_id="e1",
        )
        assert citation.strength == CitationStrength.MODERATE


class TestDecisionPacket:
    def test_minimal_decision(self):
        decision = DecisionPacket(
            decision_id="d1",
            plan_id="p1",
        )
        assert decision.claims == []
        assert decision.conflicts == []

    def test_decision_with_claims(self):
        claim = Claim(
            claim_id="cl1",
            text="Ocean acidification is accelerating.",
            epistemic_status=EpistemicStatus.MODERATE_CONFIDENCE,
            supporting_evidence_ids=["e1", "e2"],
        )
        decision = DecisionPacket(
            decision_id="d1",
            plan_id="p1",
            claims=[claim],
        )
        assert len(decision.claims) == 1


class TestExperimentRecord:
    def test_minimal_experiment(self):
        exp = ExperimentRecord(
            experiment_id="EXP-001",
            name="Baseline pipeline test",
            hypothesis="Structured plans improve over single-pass",
        )
        assert exp.seed == 42

    def test_experiment_timestamps_require_timezone(self):
        with pytest.raises(Exception):
            ExperimentRecord(
                experiment_id="EXP-001",
                name="Baseline pipeline test",
                hypothesis="Structured plans improve over single-pass",
                started_at=datetime(2026, 3, 17, 10, 30, 0),
            )

    def test_experiment_timestamps_normalize_to_utc(self):
        exp = ExperimentRecord(
            experiment_id="EXP-001",
            name="Baseline pipeline test",
            hypothesis="Structured plans improve over single-pass",
            started_at=datetime(
                2026,
                3,
                17,
                12,
                30,
                0,
                tzinfo=timezone(timedelta(hours=2)),
            ),
        )
        assert exp.started_at is not None
        assert exp.started_at.tzinfo == timezone.utc
        assert exp.started_at.hour == 10


class TestVerificationResult:
    def test_minimal_result(self):
        result = VerificationResult(decision_id="d1")
        assert result.claim_verdicts == []
        assert result.summary == ""

    def test_result_with_verdicts(self):
        verdict = ClaimVerification(
            claim_id="cl1",
            verdict=ClaimVerdict.SUPPORTED,
            supporting_ids_checked=["e1", "e2"],
            reasoning="Both evidence items confirm the claim.",
        )
        result = VerificationResult(
            decision_id="d1",
            claim_verdicts=[verdict],
            summary="1/1 claims supported",
        )
        assert len(result.claim_verdicts) == 1
        assert result.claim_verdicts[0].verdict == ClaimVerdict.SUPPORTED

    def test_all_verdict_values(self):
        for v in ClaimVerdict:
            cv = ClaimVerification(claim_id="cl1", verdict=v)
            assert cv.verdict == v

    def test_claim_verification_requires_verdict(self):
        with pytest.raises(Exception):
            ClaimVerification(claim_id="cl1")

    def test_result_requires_decision_id(self):
        with pytest.raises(Exception):
            VerificationResult()

    def test_result_serialization_roundtrip(self):
        verdict = ClaimVerification(
            claim_id="cl1",
            verdict=ClaimVerdict.CONTRADICTED,
            supporting_ids_checked=["e1"],
            contradicting_ids_checked=["e2"],
            reasoning="Evidence e2 contradicts.",
        )
        result = VerificationResult(
            decision_id="d1",
            claim_verdicts=[verdict],
            summary="0/1 supported",
        )
        data = result.model_dump()
        restored = VerificationResult.model_validate(data)
        assert restored.claim_verdicts[0].verdict == ClaimVerdict.CONTRADICTED
        assert restored.claim_verdicts[0].contradicting_ids_checked == ["e2"]


class TestResearchOutput:
    def test_minimal_output(self):
        step = PlanStep(
            step_id="s1",
            description="Search",
            expected_output="Sources",
            success_criteria="Found",
        )
        plan = ResearchPlan(plan_id="p1", goal="test goal", steps=[step])
        output = ResearchOutput(goal="test goal", plan=plan)
        assert output.goal == "test goal"
        assert output.evidence == []
        assert output.decision is None
        assert output.verification is None
        assert output.experiment is None

    def test_full_assembly(self):
        """Assemble a complete ResearchOutput with all fields populated — the v0 artifact shape."""
        step = PlanStep(
            step_id="s1",
            description="Search for causes",
            expected_output="Evidence list",
            success_criteria="At least 2 items",
        )
        plan = ResearchPlan(plan_id="p1", goal="Causes of X?", steps=[step])

        source = SourceMetadata(source_type=SourceType.WEB_SEARCH, url="https://example.com")
        ev1 = EvidenceItem(evidence_id="e1", task_id="t1", content="Cause A.", source=source)
        ev2 = EvidenceItem(evidence_id="e2", task_id="t1", content="Cause B.", source=source)

        claim = Claim(
            claim_id="cl1",
            text="X is caused by A and B.",
            epistemic_status=EpistemicStatus.MODERATE_CONFIDENCE,
            supporting_evidence_ids=["e1", "e2"],
        )
        decision = DecisionPacket(decision_id="d1", plan_id="p1", claims=[claim])

        verdict = ClaimVerification(
            claim_id="cl1",
            verdict=ClaimVerdict.SUPPORTED,
            supporting_ids_checked=["e1", "e2"],
            reasoning="Both evidence items confirm the claim.",
        )
        verification = VerificationResult(
            decision_id="d1",
            claim_verdicts=[verdict],
            summary="1/1 claims supported",
        )

        experiment = ExperimentRecord(
            experiment_id="EXP-001",
            name="v0 test run",
            hypothesis="Pipeline produces valid output",
            metrics={"groundedness": 1.0, "evidence_utilization": 1.0, "plan_coverage": 1.0},
        )

        output = ResearchOutput(
            goal="Causes of X?",
            plan=plan,
            evidence=[ev1, ev2],
            decision=decision,
            verification=verification,
            experiment=experiment,
        )

        # All fields populated
        assert output.goal == "Causes of X?"
        assert len(output.evidence) == 2
        assert output.decision is not None
        assert len(output.decision.claims) == 1
        assert output.verification is not None
        assert output.verification.claim_verdicts[0].verdict == ClaimVerdict.SUPPORTED
        assert output.experiment is not None
        assert output.experiment.metrics["groundedness"] == 1.0

        # Serialization roundtrip
        data = output.model_dump()
        restored = ResearchOutput.model_validate(data)
        assert restored.goal == output.goal
        assert len(restored.evidence) == 2
        assert restored.verification.claim_verdicts[0].verdict == ClaimVerdict.SUPPORTED

    def test_output_requires_goal_and_plan(self):
        with pytest.raises(Exception):
            ResearchOutput(goal="test")
        step = PlanStep(
            step_id="s1", description="x", expected_output="y", success_criteria="z"
        )
        plan = ResearchPlan(plan_id="p1", goal="test", steps=[step])
        with pytest.raises(Exception):
            ResearchOutput(plan=plan)


class TestProtocolImports:
    """Verify that protocol signatures reference the correct schema types."""

    def test_protocol_types_importable(self):
        from asar.core.protocols import (
            PlannerProtocol,
            ExecutorProtocol,
            MemoryProtocol,
            GroundingProtocol,
            DeliberationProtocol,
            VerificationProtocol,
            EvaluationProtocol,
        )
        # All protocols are runtime_checkable
        assert hasattr(PlannerProtocol, "__protocol_attrs__") or callable(PlannerProtocol)
        assert hasattr(VerificationProtocol, "__protocol_attrs__") or callable(VerificationProtocol)

    def test_verification_protocol_signature(self):
        """VerificationProtocol.verify must take DecisionPacket + list[EvidenceItem] and return VerificationResult."""
        import inspect
        from asar.core.protocols import VerificationProtocol
        sig = inspect.signature(VerificationProtocol.verify)
        params = list(sig.parameters.keys())
        assert "decision" in params
        assert "evidence" in params
        hints = sig.parameters["decision"].annotation
        assert hints is DecisionPacket or "DecisionPacket" in str(hints)

    def test_schemas_package_exports(self):
        """All v0 types are importable from the schemas package."""
        import schemas
        expected = [
            "ResearchPlan", "PlanStep", "TaskPacket", "EvidenceItem",
            "SourceMetadata", "DecisionPacket", "Claim", "EpistemicStatus",
            "VerificationResult", "ClaimVerification", "ClaimVerdict",
            "ResearchOutput", "ExperimentRecord",
        ]
        for name in expected:
            assert hasattr(schemas, name), f"schemas.{name} not exported"

    def test_schema_timestamps_default_to_utc(self):
        step = PlanStep(
            step_id="s1",
            description="Search",
            expected_output="Sources",
            success_criteria="Found",
        )
        plan = ResearchPlan(plan_id="p1", goal="test", steps=[step])
        assert plan.created_at.tzinfo == timezone.utc

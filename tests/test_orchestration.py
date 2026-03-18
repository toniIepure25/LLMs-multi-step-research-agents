"""
Integration-style tests for the v0 `SequentialOrchestrator`.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from asar.common import load_settings, setup_logging
from asar.core.errors import OrchestrationError
from asar.core.result import OperationResult
from asar.evaluation import ExperimentLogger
from asar.memory.working_memory import WorkingMemory
from asar.orchestration import SequentialOrchestrator
from asar.verification import EvidenceChecker
from schemas.decision_packet import Claim, DecisionPacket, EpistemicStatus
from schemas.evidence_item import EvidenceItem, SourceMetadata, SourceType
from schemas.research_plan import PlanStep, ResearchPlan, StepDependencyType


CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def _plan() -> ResearchPlan:
    return ResearchPlan(
        plan_id="plan_123",
        goal="Assess battery storage cost trends in 2024",
        steps=[
            PlanStep(
                step_id="step_1",
                description="Find current battery storage market reports",
                expected_output="A set of current reports",
                success_criteria="At least one report is found",
                dependency_type=StepDependencyType.SEQUENTIAL,
                depends_on=[],
                tool_hint="web_search",
                priority=1,
            ),
            PlanStep(
                step_id="step_2",
                description="Compare regional price movements in 2024",
                expected_output="Regional price comparisons",
                success_criteria="At least two regions are compared",
                dependency_type=StepDependencyType.SEQUENTIAL,
                depends_on=["step_1"],
                tool_hint="web_search",
                priority=2,
            ),
        ],
    )


def _evidence(evidence_id: str, content: str) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        task_id="task_placeholder",
        content=content,
        source=SourceMetadata(
            source_type=SourceType.WEB_SEARCH,
            url=f"https://example.com/{evidence_id}",
            title=f"Source for {evidence_id}",
            raw_snippet=content,
        ),
    )


class RecordingWorkingMemory(WorkingMemory):
    def __init__(self, max_items: int = 50) -> None:
        super().__init__(max_items=max_items)
        self.store_calls: list[str] = []
        self.retrieve_calls: list[tuple[str, int]] = []

    async def store(self, item: EvidenceItem) -> str:
        self.store_calls.append(item.evidence_id)
        return await super().store(item)

    async def retrieve(self, query: str, limit: int = 10) -> list[EvidenceItem]:
        self.retrieve_calls.append((query, limit))
        return await super().retrieve(query, limit=limit)


class StubPlanner:
    def __init__(self, plan: ResearchPlan | None = None, failure: OperationResult[ResearchPlan] | None = None) -> None:
        self.plan_to_return = plan or _plan()
        self.failure = failure
        self.calls: list[tuple[str, dict | None]] = []

    async def plan_result(self, goal: str, constraints: dict | None = None) -> OperationResult[ResearchPlan]:
        self.calls.append((goal, constraints))
        if self.failure is not None:
            return self.failure
        return OperationResult.ok(self.plan_to_return)


class StubExecutor:
    def __init__(self, responses: dict[str, list[EvidenceItem]]) -> None:
        self.responses = responses
        self.calls: list[str] = []

    async def execute(self, task) -> list[EvidenceItem]:
        self.calls.append(task.step_id)
        return list(self.responses.get(task.step_id, []))


class StubSynthesizer:
    def __init__(self) -> None:
        self.calls: list[tuple[list[EvidenceItem], str | None]] = []

    async def deliberate(self, evidence: list[EvidenceItem], context: str | None = None) -> DecisionPacket:
        self.calls.append((list(evidence), context))
        context_payload = json.loads(context or "{}")
        claims = [
            Claim(
                claim_id=f"claim_{index}",
                text=item.content,
                epistemic_status=EpistemicStatus.MODERATE_CONFIDENCE,
                supporting_evidence_ids=[item.evidence_id],
                contradicting_evidence_ids=[],
            )
            for index, item in enumerate(evidence, start=1)
        ]
        return DecisionPacket(
            decision_id="decision_123",
            plan_id=context_payload["plan_id"],
            claims=claims,
            conflicts=[],
            synthesis="Concise synthesis.",
            information_gaps=[],
        )


@pytest.mark.asyncio
async def test_sequential_orchestrator_happy_path_returns_research_output(tmp_path: Path) -> None:
    settings = load_settings(CONFIG_DIR)
    setup_logging(settings.pipeline.logging, force=True, stream=io.StringIO())
    planner = StubPlanner()
    executor = StubExecutor(
        {
            "step_1": [_evidence("evidence_1", "Battery storage costs fell in 2024.")],
            "step_2": [_evidence("evidence_2", "Regional battery prices diverged in 2024.")],
        }
    )
    memory = RecordingWorkingMemory()
    synthesizer = StubSynthesizer()
    verifier = EvidenceChecker(settings)
    evaluator = ExperimentLogger(settings, output_dir=tmp_path)
    orchestrator = SequentialOrchestrator(
        planner=planner,
        executor=executor,
        memory=memory,
        synthesizer=synthesizer,
        verifier=verifier,
        evaluator=evaluator,
        settings=settings,
    )

    output = await orchestrator.run("Assess battery storage cost trends in 2024")

    assert output.goal == "Assess battery storage cost trends in 2024"
    assert output.plan.plan_id == "plan_123"
    assert len(output.evidence) == 2
    assert output.decision is not None
    assert output.verification is not None
    assert output.experiment is not None
    assert output.created_at.utcoffset() is not None


@pytest.mark.asyncio
async def test_sequential_orchestrator_planner_failure_uses_typed_path(tmp_path: Path) -> None:
    settings = load_settings(CONFIG_DIR)
    planner = StubPlanner(
        failure=OperationResult.fail(
            "planner_llm_error",
            "Planner LLM call failed",
            details={"goal": "broken"},
        )
    )
    orchestrator = SequentialOrchestrator(
        planner=planner,
        executor=StubExecutor({}),
        memory=RecordingWorkingMemory(),
        synthesizer=StubSynthesizer(),
        verifier=EvidenceChecker(settings),
        evaluator=ExperimentLogger(settings, output_dir=tmp_path),
        settings=settings,
    )

    result = await orchestrator.run_result("broken")

    assert result.is_error
    assert result.error is not None
    assert result.error.code == "orchestration_stage_failed"
    assert result.error.details["stage"] == "planning"


@pytest.mark.asyncio
async def test_sequential_orchestrator_handles_one_empty_execution_step_explicitly(tmp_path: Path) -> None:
    settings = load_settings(CONFIG_DIR)
    orchestrator = SequentialOrchestrator(
        planner=StubPlanner(),
        executor=StubExecutor(
            {
                "step_1": [],
                "step_2": [_evidence("evidence_2", "Regional battery prices diverged in 2024.")],
            }
        ),
        memory=RecordingWorkingMemory(),
        synthesizer=StubSynthesizer(),
        verifier=EvidenceChecker(settings),
        evaluator=ExperimentLogger(settings, output_dir=tmp_path),
        settings=settings,
    )

    output = await orchestrator.run("Assess battery storage cost trends in 2024")

    assert len(output.evidence) == 1
    assert output.experiment is not None
    assert output.experiment.metrics["plan_coverage"] == 0.5


@pytest.mark.asyncio
async def test_sequential_orchestrator_aggregates_multiple_steps_and_uses_memory(tmp_path: Path) -> None:
    settings = load_settings(CONFIG_DIR)
    memory = RecordingWorkingMemory()
    executor = StubExecutor(
        {
            "step_1": [_evidence("evidence_1", "Battery storage costs fell in 2024.")],
            "step_2": [
                _evidence("evidence_2", "Regional battery prices diverged in 2024."),
                _evidence("evidence_3", "Policy incentives remained important in 2024."),
            ],
        }
    )
    orchestrator = SequentialOrchestrator(
        planner=StubPlanner(),
        executor=executor,
        memory=memory,
        synthesizer=StubSynthesizer(),
        verifier=EvidenceChecker(settings),
        evaluator=ExperimentLogger(settings, output_dir=tmp_path),
        settings=settings,
    )

    output = await orchestrator.run("Assess battery storage cost trends in 2024")

    assert len(output.evidence) == 3
    assert len(memory.store_calls) == 3
    assert memory.retrieve_calls == [("", 3)]
    assert executor.calls == ["step_1", "step_2"]


@pytest.mark.asyncio
async def test_sequential_orchestrator_attaches_verification_and_writes_run_artifacts(tmp_path: Path) -> None:
    settings = load_settings(CONFIG_DIR)
    orchestrator = SequentialOrchestrator(
        planner=StubPlanner(),
        executor=StubExecutor(
            {"step_1": [_evidence("evidence_1", "Battery storage costs fell in 2024.")], "step_2": []}
        ),
        memory=RecordingWorkingMemory(),
        synthesizer=StubSynthesizer(),
        verifier=EvidenceChecker(settings),
        evaluator=ExperimentLogger(settings, output_dir=tmp_path),
        settings=settings,
    )

    output = await orchestrator.run("Assess battery storage cost trends in 2024")

    assert output.verification is not None
    assert output.verification.decision_id == output.decision.decision_id if output.decision is not None else False
    assert output.experiment is not None
    assert all(Path(path).exists() for path in output.experiment.artifacts)


@pytest.mark.asyncio
async def test_sequential_orchestrator_preserves_step_linkage_for_plan_coverage(tmp_path: Path) -> None:
    settings = load_settings(CONFIG_DIR)
    orchestrator = SequentialOrchestrator(
        planner=StubPlanner(),
        executor=StubExecutor(
            {
                "step_1": [_evidence("evidence_1", "Battery storage costs fell in 2024.")],
                "step_2": [_evidence("evidence_2", "Regional battery prices diverged in 2024.")],
            }
        ),
        memory=RecordingWorkingMemory(),
        synthesizer=StubSynthesizer(),
        verifier=EvidenceChecker(settings),
        evaluator=ExperimentLogger(settings, output_dir=tmp_path),
        settings=settings,
    )

    output = await orchestrator.run("Assess battery storage cost trends in 2024")

    assert {item.source.additional["step_id"] for item in output.evidence} == {"step_1", "step_2"}
    assert output.experiment is not None
    assert output.experiment.metrics["plan_coverage"] == 1.0


@pytest.mark.asyncio
async def test_sequential_orchestrator_raises_typed_error_on_failure(tmp_path: Path) -> None:
    settings = load_settings(CONFIG_DIR)
    planner = StubPlanner(
        failure=OperationResult.fail(
            "planner_invalid_goal",
            "Planner goal must not be empty",
        )
    )
    orchestrator = SequentialOrchestrator(
        planner=planner,
        executor=StubExecutor({}),
        memory=RecordingWorkingMemory(),
        synthesizer=StubSynthesizer(),
        verifier=EvidenceChecker(settings),
        evaluator=ExperimentLogger(settings, output_dir=tmp_path),
        settings=settings,
    )

    with pytest.raises(OrchestrationError):
        await orchestrator.run("Assess battery storage cost trends in 2024")


@pytest.mark.asyncio
async def test_sequential_orchestrator_can_skip_experiment_recording(tmp_path: Path) -> None:
    settings = load_settings(CONFIG_DIR)
    orchestrator = SequentialOrchestrator(
        planner=StubPlanner(),
        executor=StubExecutor(
            {"step_1": [_evidence("evidence_1", "Battery storage costs fell in 2024.")], "step_2": []}
        ),
        memory=RecordingWorkingMemory(),
        synthesizer=StubSynthesizer(),
        verifier=EvidenceChecker(settings),
        evaluator=ExperimentLogger(settings, output_dir=tmp_path),
        settings=settings,
    )

    output = await orchestrator.run("Assess battery storage cost trends in 2024", record_run=False)

    assert output.experiment is None

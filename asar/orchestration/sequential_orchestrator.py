"""
Minimal sequential v0 orchestrator.
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from typing import Any

from asar.common import ASARSettings, IDPrefix, generate_id, generate_trace_id, get_logger, setup_logging
from asar.core.errors import MemoryStoreError, OrchestrationError
from asar.core.protocols import (
    DeliberationProtocol,
    EvaluationProtocol,
    ExecutorProtocol,
    MemoryProtocol,
    PlannerProtocol,
    VerificationProtocol,
)
from asar.core.result import OperationResult
from schemas.evidence_item import EvidenceItem
from schemas.experiment_record import ExperimentRecord
from schemas.research_output import ResearchOutput
from schemas.research_plan import PlanStep, ResearchPlan
from schemas.task_packet import TaskPacket


class SequentialOrchestrator:
    """Wire the frozen v0 layers into one explicit sequential pipeline."""

    def __init__(
        self,
        *,
        planner: PlannerProtocol,
        executor: ExecutorProtocol,
        memory: MemoryProtocol,
        synthesizer: DeliberationProtocol,
        verifier: VerificationProtocol,
        evaluator: EvaluationProtocol | Any | None,
        settings: ASARSettings,
    ) -> None:
        self._planner = planner
        self._executor = executor
        self._memory = memory
        self._synthesizer = synthesizer
        self._verifier = verifier
        self._evaluator = evaluator
        self._settings = settings
        setup_logging(settings.pipeline.logging)
        self._base_logger_name = "asar.orchestration.sequential_orchestrator"

    async def run(
        self,
        goal: str,
        constraints: dict | None = None,
        *,
        record_run: bool = True,
        experiment_name: str | None = None,
        hypothesis: str | None = None,
        notes: str | None = None,
        git_commit: str | None = None,
    ) -> ResearchOutput:
        """Run the full v0 pipeline or raise a typed orchestration error."""

        result = await self.run_result(
            goal,
            constraints=constraints,
            record_run=record_run,
            experiment_name=experiment_name,
            hypothesis=hypothesis,
            notes=notes,
            git_commit=git_commit,
        )
        if result.is_error and result.error is not None:
            raise OrchestrationError(
                result.error.message,
                details=result.error.details,
                retryable=result.error.retryable,
            )
        return result.unwrap()

    async def run_result(
        self,
        goal: str,
        constraints: dict | None = None,
        *,
        record_run: bool = True,
        experiment_name: str | None = None,
        hypothesis: str | None = None,
        notes: str | None = None,
        git_commit: str | None = None,
    ) -> OperationResult[ResearchOutput]:
        """Run the v0 pipeline while keeping failure paths inspectable."""

        normalized_goal = goal.strip()
        if not normalized_goal:
            return OperationResult.fail(
                "orchestration_invalid_goal",
                "Research goal must not be empty",
            )

        trace_id = generate_trace_id()
        logger = get_logger(self._base_logger_name, trace_id=trace_id)
        logger.info("Starting sequential v0 pipeline")

        plan_result = await self._invoke_result_stage(
            stage="planning",
            trace_id=trace_id,
            callback=lambda: self._plan(normalized_goal, constraints),
        )
        if plan_result.is_error:
            return plan_result
        plan = plan_result.unwrap()

        collected_evidence: list[EvidenceItem] = []
        for step in plan.steps:
            task = self._build_task_packet(plan=plan, step=step, constraints=constraints)
            logger.info("Executing plan step", extra={"step_id": step.step_id, "task_id": task.task_id})

            step_result = await self._invoke_result_stage(
                stage="execution",
                trace_id=trace_id,
                callback=lambda task=task: self._execute(task),
                details={"step_id": step.step_id, "task_id": task.task_id},
            )
            if step_result.is_error:
                return step_result

            step_evidence = [
                self._attach_step_linkage(item, plan=plan, step=step, task=task)
                for item in step_result.unwrap()
            ]

            store_result = await self._store_step_evidence(
                step_evidence,
                trace_id=trace_id,
                step_id=step.step_id,
                task_id=task.task_id,
            )
            if store_result.is_error:
                return store_result

            collected_evidence.extend(step_evidence)

        memory_evidence = await self._load_memory_snapshot(collected_evidence, trace_id=trace_id)
        if memory_evidence.is_error:
            return memory_evidence

        evidence_for_downstream = memory_evidence.unwrap()
        synthesis_context = json.dumps(
            {"plan_id": plan.plan_id, "goal": plan.goal},
            sort_keys=True,
        )

        decision_result = await self._invoke_result_stage(
            stage="deliberation",
            trace_id=trace_id,
            callback=lambda: self._deliberate(evidence_for_downstream, synthesis_context),
            details={"plan_id": plan.plan_id, "evidence_count": len(evidence_for_downstream)},
        )
        if decision_result.is_error:
            return decision_result
        decision = decision_result.unwrap()

        verification_result = await self._invoke_result_stage(
            stage="verification",
            trace_id=trace_id,
            callback=lambda: self._verify(decision, evidence_for_downstream),
            details={"decision_id": decision.decision_id, "evidence_count": len(evidence_for_downstream)},
        )
        if verification_result.is_error:
            return verification_result
        verification = verification_result.unwrap()

        experiment: ExperimentRecord | None = None
        if record_run:
            experiment_result = await self._record_experiment(
                plan=plan,
                evidence=evidence_for_downstream,
                decision=decision,
                verification=verification,
                trace_id=trace_id,
                experiment_name=experiment_name,
                hypothesis=hypothesis,
                notes=notes,
                git_commit=git_commit,
            )
            if experiment_result.is_error:
                return experiment_result
            experiment = experiment_result.unwrap()

        logger.info("Sequential v0 pipeline complete")
        return OperationResult.ok(
            ResearchOutput(
                goal=normalized_goal,
                plan=plan,
                evidence=evidence_for_downstream,
                decision=decision,
                verification=verification,
                experiment=experiment,
            )
        )

    async def _plan(self, goal: str, constraints: dict | None) -> ResearchPlan:
        if hasattr(self._planner, "plan_result"):
            result = await self._planner.plan_result(goal, constraints=constraints)
            if result.is_error and result.error is not None:
                raise OrchestrationError(
                    "Planning failed",
                    details=result.error.details,
                    retryable=result.error.retryable,
                )
            return result.unwrap()
        return await self._planner.plan(goal, constraints=constraints)

    async def _execute(self, task: TaskPacket) -> list[EvidenceItem]:
        if hasattr(self._executor, "execute_result"):
            result = await self._executor.execute_result(task)
            if result.is_error and result.error is not None:
                raise OrchestrationError(
                    "Execution failed",
                    details=result.error.details,
                    retryable=result.error.retryable,
                )
            return result.unwrap()
        return await self._executor.execute(task)

    async def _deliberate(self, evidence: list[EvidenceItem], context: str) -> Any:
        if hasattr(self._synthesizer, "deliberate_result"):
            result = await self._synthesizer.deliberate_result(evidence, context=context)
            if result.is_error and result.error is not None:
                raise OrchestrationError(
                    "Deliberation failed",
                    details=result.error.details,
                    retryable=result.error.retryable,
                )
            return result.unwrap()
        return await self._synthesizer.deliberate(evidence, context=context)

    async def _verify(self, decision: Any, evidence: list[EvidenceItem]) -> Any:
        if hasattr(self._verifier, "verify_result"):
            result = await self._verifier.verify_result(decision, evidence)
            if result.is_error and result.error is not None:
                raise OrchestrationError(
                    "Verification failed",
                    details=result.error.details,
                    retryable=result.error.retryable,
                )
            return result.unwrap()
        return await self._verifier.verify(decision, evidence)

    async def _record_experiment(
        self,
        *,
        plan: ResearchPlan,
        evidence: list[EvidenceItem],
        decision: Any,
        verification: Any,
        trace_id: str,
        experiment_name: str | None,
        hypothesis: str | None,
        notes: str | None,
        git_commit: str | None,
    ) -> OperationResult[ExperimentRecord]:
        if self._evaluator is None:
            return OperationResult.fail(
                "orchestration_missing_evaluator",
                "Run recording was requested but no evaluation layer was provided",
                details={"trace_id": trace_id},
            )

        if hasattr(self._evaluator, "record_run_result"):
            result = await self._evaluator.record_run_result(
                plan=plan,
                evidence=evidence,
                decision=decision,
                verification=verification,
                name=experiment_name,
                hypothesis=hypothesis,
                notes=notes,
                git_commit=git_commit,
            )
            if result.is_error:
                return OperationResult.fail(
                    "orchestration_evaluation_failed",
                    result.error.message if result.error is not None else "Evaluation failed",
                    details={
                        **(result.error.details if result.error is not None else {}),
                        "trace_id": trace_id,
                    },
                    retryable=result.error.retryable if result.error is not None else False,
                )
            return OperationResult.ok(result.unwrap())

        if hasattr(self._evaluator, "record_run"):
            try:
                record = await self._evaluator.record_run(
                    plan=plan,
                    evidence=evidence,
                    decision=decision,
                    verification=verification,
                    name=experiment_name,
                    hypothesis=hypothesis,
                    notes=notes,
                    git_commit=git_commit,
                )
            except Exception as exc:
                return OperationResult.fail(
                    "orchestration_evaluation_failed",
                    "Evaluation failed",
                    details={"trace_id": trace_id, "error": str(exc)},
                )
            return OperationResult.ok(record)

        return OperationResult.fail(
            "orchestration_missing_record_run",
            "Evaluation layer does not support run recording",
            details={"trace_id": trace_id},
        )

    async def _store_step_evidence(
        self,
        evidence: list[EvidenceItem],
        *,
        trace_id: str,
        step_id: str,
        task_id: str,
    ) -> OperationResult[int]:
        for item in evidence:
            try:
                await self._memory.store(item)
            except MemoryStoreError as exc:
                return OperationResult.fail(
                    "orchestration_memory_failed",
                    "Working memory failed while storing evidence",
                    details={
                        "trace_id": trace_id,
                        "step_id": step_id,
                        "task_id": task_id,
                        "evidence_id": item.evidence_id,
                        **exc.details,
                    },
                )
        return OperationResult.ok(len(evidence))

    async def _load_memory_snapshot(
        self,
        collected_evidence: list[EvidenceItem],
        *,
        trace_id: str,
    ) -> OperationResult[list[EvidenceItem]]:
        if not collected_evidence:
            return OperationResult.ok([])

        try:
            memory_items = await self._memory.retrieve("", limit=len(collected_evidence))
        except Exception as exc:
            return OperationResult.fail(
                "orchestration_memory_failed",
                "Working memory failed while retrieving evidence",
                details={"trace_id": trace_id, "error": str(exc)},
            )

        if len(memory_items) != len(collected_evidence):
            return OperationResult.ok(list(collected_evidence))
        return OperationResult.ok(memory_items)

    async def _invoke_result_stage(
        self,
        *,
        stage: str,
        trace_id: str,
        callback: Callable[[], Awaitable[Any]],
        details: dict[str, Any] | None = None,
    ) -> OperationResult[Any]:
        try:
            value = await callback()
        except Exception as exc:
            stage_details = {"trace_id": trace_id, "stage": stage, "error": str(exc)}
            if isinstance(exc, OrchestrationError):
                stage_details.update(exc.details)
                retryable = exc.retryable
                message = exc.message
            else:
                retryable = False
                message = f"{stage.capitalize()} stage failed"
            if details:
                stage_details.update(details)
            return OperationResult.fail(
                "orchestration_stage_failed",
                message,
                retryable=retryable,
                details=stage_details,
            )

        return OperationResult.ok(value)

    def _build_task_packet(
        self,
        *,
        plan: ResearchPlan,
        step: PlanStep,
        constraints: dict | None,
    ) -> TaskPacket:
        task_constraints = dict(constraints or {})
        task_constraints["tool_hint"] = step.tool_hint or "web_search"
        task_constraints["step_priority"] = step.priority

        return TaskPacket(
            task_id=generate_id(IDPrefix.TASK),
            plan_id=plan.plan_id,
            step_id=step.step_id,
            action="search",
            query=step.description,
            context=json.dumps(
                {
                    "goal": plan.goal,
                    "expected_output": step.expected_output,
                    "success_criteria": step.success_criteria,
                    "depends_on": step.depends_on,
                },
                sort_keys=True,
            ),
            expected_output_type="evidence",
            constraints=task_constraints,
        )

    def _attach_step_linkage(
        self,
        item: EvidenceItem,
        *,
        plan: ResearchPlan,
        step: PlanStep,
        task: TaskPacket,
    ) -> EvidenceItem:
        additional = {
            **item.source.additional,
            "plan_id": plan.plan_id,
            "step_id": step.step_id,
            "step_description": step.description,
            "task_id": task.task_id,
        }
        source = item.source.model_copy(update={"additional": additional})
        tags = list(dict.fromkeys([*item.tags, step.step_id, plan.plan_id]))
        return item.model_copy(
            update={
                "task_id": task.task_id,
                "source": source,
                "tags": tags,
            }
        )

"""
Minimal v0 planner backed by a typed LLM abstraction.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from asar.common import ASARSettings, IDPrefix, generate_id, generate_trace_id, get_logger, setup_logging
from asar.core.errors import LLMClientError, PlanningError
from asar.core.llm import LLMClientProtocol, LLMGenerationRequest, LLMMessage, MessageRole
from asar.core.result import OperationResult
from schemas.research_plan import PlanStep, ResearchPlan, StepDependencyType


class _PlannerStepDraft(BaseModel):
    """Structured step draft expected from the LLM."""

    description: str = Field(..., min_length=10)
    expected_output: str = Field(..., min_length=5)
    success_criteria: str = Field(..., min_length=5)


class _PlannerResponse(BaseModel):
    """Structured planner response expected from the LLM."""

    steps: list[_PlannerStepDraft] = Field(..., min_length=3, max_length=5)


class SimplePlanner:
    """Generate a v0 `ResearchPlan` from one research goal."""

    def __init__(self, llm_client: LLMClientProtocol, settings: ASARSettings) -> None:
        self._llm_client = llm_client
        self._settings = settings
        setup_logging(settings.pipeline.logging)
        self._base_logger_name = "asar.planning.simple_planner"

    async def plan(self, goal: str, constraints: dict | None = None) -> ResearchPlan:
        """Generate a valid v0 research plan or raise a typed planning error."""

        result = await self.plan_result(goal, constraints=constraints)
        if result.is_error and result.error is not None:
            raise PlanningError(
                result.error.message,
                details=result.error.details,
                retryable=result.error.retryable,
            )
        return result.unwrap()

    async def plan_result(
        self,
        goal: str,
        constraints: dict | None = None,
    ) -> OperationResult[ResearchPlan]:
        """Generate a plan and keep malformed-output failures inspectable."""

        normalized_goal = goal.strip()
        if not normalized_goal:
            return OperationResult.fail(
                "planner_invalid_goal",
                "Planner goal must not be empty",
            )

        trace_id = generate_trace_id()
        logger = get_logger(self._base_logger_name, trace_id=trace_id)
        model_settings = self._settings.models.route_for("planning")
        request = self._build_request(
            goal=normalized_goal,
            constraints=constraints,
            model=model_settings.model,
            temperature=model_settings.temperature,
            max_tokens=model_settings.max_tokens,
            trace_id=trace_id,
        )

        logger.info("Generating v0 research plan")
        try:
            response = await self._llm_client.generate(request)
        except Exception as exc:
            error_details = {
                "goal": normalized_goal,
                "trace_id": trace_id,
                "error": str(exc),
            }
            if isinstance(exc, LLMClientError) and exc.details:
                error_details["llm_error_details"] = exc.details
            return OperationResult.fail(
                "planner_llm_error",
                "Planner LLM call failed",
                retryable=isinstance(exc, LLMClientError),
                details=error_details,
            )

        try:
            parsed = self._parse_response(response.output_text)
            plan = self._build_plan(
                goal=normalized_goal,
                constraints=constraints,
                step_drafts=parsed.steps,
            )
        except PlanningError as exc:
            logger.error("Planner response validation failed")
            return OperationResult.fail(
                "planner_response_invalid",
                exc.message,
                details={**exc.details, "trace_id": trace_id},
            )

        logger.info("Research plan generated")
        return OperationResult.ok(plan)

    async def replan(self, plan_id: str, feedback: str) -> ResearchPlan:
        """v0 does not implement the re-planning loop."""

        raise NotImplementedError("v0 does not implement re-planning")

    def _build_request(
        self,
        *,
        goal: str,
        constraints: dict | None,
        model: str,
        temperature: float,
        max_tokens: int,
        trace_id: str,
    ) -> LLMGenerationRequest:
        constraints_text = json.dumps(constraints, sort_keys=True) if constraints else "none"
        prompt = (
            "Create a research plan for the goal below.\n"
            "Return JSON only with this shape:\n"
            '{"steps":[{"description":"...","expected_output":"...","success_criteria":"..."}]}\n'
            "Requirements:\n"
            "- 3 to 5 steps exactly\n"
            "- steps must be sequential\n"
            "- each step must be a concrete sub-question or research action\n"
            "- no parallel branches, no debate, no re-planning\n"
            f"Goal: {goal}\n"
            f"Constraints: {constraints_text}"
        )

        return LLMGenerationRequest(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                LLMMessage(
                    role=MessageRole.SYSTEM,
                    content=(
                        "You are ASAR's v0 planner. Produce compact JSON only. "
                        "Plan for a web-search based research workflow."
                    ),
                ),
                LLMMessage(role=MessageRole.USER, content=prompt),
            ],
            metadata={
                "component": "planning",
                "trace_id": trace_id,
            },
        )

    def _parse_response(self, output_text: str) -> _PlannerResponse:
        raw_payload = _strip_code_fences(output_text)
        try:
            decoded = json.loads(raw_payload)
        except json.JSONDecodeError as exc:
            raise PlanningError(
                "Planner response was not valid JSON",
                details={"response": output_text},
            ) from exc

        try:
            parsed = _PlannerResponse.model_validate(decoded)
        except ValidationError as exc:
            raise PlanningError(
                "Planner response did not match the expected schema",
                details={"response": decoded, "errors": exc.errors()},
            ) from exc

        if not 3 <= len(parsed.steps) <= 5:
            raise PlanningError(
                "Planner must return between 3 and 5 steps",
                details={"step_count": len(parsed.steps)},
            )

        return parsed

    def _build_plan(
        self,
        *,
        goal: str,
        constraints: dict | None,
        step_drafts: list[_PlannerStepDraft],
    ) -> ResearchPlan:
        plan_id = generate_id(IDPrefix.PLAN)
        steps: list[PlanStep] = []
        previous_step_id: str | None = None

        for index, draft in enumerate(step_drafts, start=1):
            step_id = generate_id(IDPrefix.STEP)
            steps.append(
                PlanStep(
                    step_id=step_id,
                    description=draft.description.strip(),
                    expected_output=draft.expected_output.strip(),
                    success_criteria=draft.success_criteria.strip(),
                    dependency_type=StepDependencyType.SEQUENTIAL,
                    depends_on=[] if previous_step_id is None else [previous_step_id],
                    tool_hint="web_search",
                    priority=index,
                )
            )
            previous_step_id = step_id

        constraints_text = json.dumps(constraints, sort_keys=True) if constraints else None
        try:
            return ResearchPlan(
                plan_id=plan_id,
                goal=goal,
                steps=steps,
                constraints=constraints_text,
            )
        except ValidationError as exc:
            raise PlanningError(
                "Planner produced an invalid ResearchPlan",
                details={"errors": exc.errors()},
            ) from exc


def _strip_code_fences(output_text: str) -> str:
    text = output_text.strip()
    if not text.startswith("```"):
        return text

    lines = text.splitlines()
    if len(lines) >= 3 and lines[0].startswith("```") and lines[-1].startswith("```"):
        return "\n".join(lines[1:-1]).strip()
    return text

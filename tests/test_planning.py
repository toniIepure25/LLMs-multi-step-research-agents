"""
Unit tests for the v0 `SimplePlanner`.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from asar.common import load_settings, setup_logging
from asar.core.errors import LLMClientError, PlanningError
from asar.core.llm import LLMGenerationRequest, LLMGenerationResponse, LLMMessage, MessageRole, TokenUsage
from asar.planning import SimplePlanner
from schemas.research_plan import StepDependencyType


CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


class StubLLMClient:
    """Small fake LLM client that records requests and returns fixed output."""

    def __init__(self, output_text: str) -> None:
        self._output_text = output_text
        self.requests: list[LLMGenerationRequest] = []

    async def generate(self, request: LLMGenerationRequest) -> LLMGenerationResponse:
        self.requests.append(request)
        return LLMGenerationResponse(
            model=request.model,
            output_text=self._output_text,
            usage=TokenUsage(input_tokens=10, output_tokens=20),
        )


@pytest.mark.asyncio
async def test_simple_planner_happy_path_returns_valid_plan() -> None:
    settings = load_settings(CONFIG_DIR)
    setup_logging(settings.pipeline.logging, force=True, stream=io.StringIO())
    llm_client = StubLLMClient(
        """
        {
          "steps": [
            {
              "description": "Identify the main sub-topics that shape the research question.",
              "expected_output": "A short list of the main facets to investigate.",
              "success_criteria": "The list covers the core aspects of the goal."
            },
            {
              "description": "Search for high-quality sources covering each core facet.",
              "expected_output": "A set of sources and notes for each facet.",
              "success_criteria": "Each facet has at least one relevant source to examine."
            },
            {
              "description": "Extract the strongest findings and open disagreements from the sources.",
              "expected_output": "Structured notes on findings, conflicts, and gaps.",
              "success_criteria": "Key claims and disagreements are captured for synthesis."
            }
          ]
        }
        """
    )
    planner = SimplePlanner(llm_client, settings)

    plan = await planner.plan("What caused the 2008 financial crisis?")

    assert plan.goal == "What caused the 2008 financial crisis?"
    assert plan.plan_id.startswith("plan_")
    assert len(plan.steps) == 3
    assert all(step.step_id.startswith("step_") for step in plan.steps)
    assert all(step.dependency_type is StepDependencyType.SEQUENTIAL for step in plan.steps)
    assert plan.steps[0].depends_on == []
    assert plan.steps[1].depends_on == [plan.steps[0].step_id]
    assert plan.steps[2].depends_on == [plan.steps[1].step_id]
    assert llm_client.requests[0].model == settings.models.route_for("planning").model


@pytest.mark.asyncio
async def test_simple_planner_malformed_output_returns_typed_failure() -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient("not-json")
    planner = SimplePlanner(llm_client, settings)

    result = await planner.plan_result("Explain causes of ocean acidification.")

    assert result.is_error
    assert result.error is not None
    assert result.error.code == "planner_response_invalid"
    assert result.error.details["trace_id"].startswith("trace_")


@pytest.mark.asyncio
async def test_simple_planner_wrong_number_of_steps_fails_validation() -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        """
        {
          "steps": [
            {
              "description": "Find one source relevant to the goal.",
              "expected_output": "A single source.",
              "success_criteria": "The source is on topic."
            },
            {
              "description": "Summarize the source findings.",
              "expected_output": "A short summary.",
              "success_criteria": "The summary is readable."
            }
          ]
        }
        """
    )
    planner = SimplePlanner(llm_client, settings)

    with pytest.raises(PlanningError):
        await planner.plan("What are the causes of inflation?")


@pytest.mark.asyncio
async def test_simple_planner_generated_steps_are_sequential_and_schema_valid() -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        """
        {
          "steps": [
            {
              "description": "Clarify what aspect of solar adoption the goal is asking about.",
              "expected_output": "A clarified research focus.",
              "success_criteria": "The research focus is specific enough to search."
            },
            {
              "description": "Gather recent evidence about economic drivers and barriers.",
              "expected_output": "Evidence notes on drivers and barriers.",
              "success_criteria": "Both drivers and barriers are covered."
            },
            {
              "description": "Gather recent evidence about policy and regulatory factors.",
              "expected_output": "Evidence notes on policy factors.",
              "success_criteria": "Relevant policy constraints or enablers are captured."
            },
            {
              "description": "Compare the collected factors and identify the most important ones.",
              "expected_output": "A prioritized comparison of factors.",
              "success_criteria": "The comparison is grounded in the earlier evidence collection."
            }
          ]
        }
        """
    )
    planner = SimplePlanner(llm_client, settings)

    plan = await planner.plan("Why is residential solar adoption uneven across regions?")

    assert len(plan.steps) == 4
    for index, step in enumerate(plan.steps):
        assert step.dependency_type is StepDependencyType.SEQUENTIAL
        assert step.tool_hint == "web_search"
        assert step.priority == index + 1
        if index == 0:
            assert step.depends_on == []
        else:
            assert step.depends_on == [plan.steps[index - 1].step_id]


@pytest.mark.asyncio
async def test_simple_planner_uses_shared_metadata_and_ids_consistently() -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        """
        {
          "steps": [
            {
              "description": "Identify the main public-health outcomes discussed in the literature.",
              "expected_output": "A list of relevant public-health outcomes.",
              "success_criteria": "The list captures the outcomes most often discussed."
            },
            {
              "description": "Search for evidence linking the intervention to those outcomes.",
              "expected_output": "Evidence notes on the intervention and outcomes.",
              "success_criteria": "The search yields relevant evidence for the listed outcomes."
            },
            {
              "description": "Separate consistent findings from contested findings.",
              "expected_output": "A split between consistent and contested findings.",
              "success_criteria": "The split is based on the evidence gathered in prior steps."
            }
          ]
        }
        """
    )
    planner = SimplePlanner(llm_client, settings)

    plan = await planner.plan("What are the public-health impacts of congestion pricing?")
    request = llm_client.requests[0]

    assert request.metadata["component"] == "planning"
    assert request.metadata["trace_id"].startswith("trace_")
    assert request.messages[0] == LLMMessage(
        role=MessageRole.SYSTEM,
        content="You are ASAR's v0 planner. Produce compact JSON only. Plan for a web-search based research workflow.",
    )
    assert plan.plan_id.startswith("plan_")
    assert all(step.step_id.startswith("step_") for step in plan.steps)


@pytest.mark.asyncio
async def test_simple_planner_wraps_llm_failures() -> None:
    settings = load_settings(CONFIG_DIR)

    class BrokenLLMClient:
        async def generate(self, request: LLMGenerationRequest) -> LLMGenerationResponse:
            raise LLMClientError("provider timeout", retryable=True)

    planner = SimplePlanner(BrokenLLMClient(), settings)

    result = await planner.plan_result("Why do heat pumps vary in performance by climate?")

    assert result.is_error
    assert result.error is not None
    assert result.error.code == "planner_llm_error"
    assert result.error.retryable is True

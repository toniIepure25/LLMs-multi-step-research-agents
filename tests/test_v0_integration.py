"""
Canonical mocked end-to-end integration target for the frozen v0 pipeline.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from asar.common import load_settings, setup_logging
from asar.core.llm import LLMGenerationRequest, LLMGenerationResponse, TokenUsage
from asar.core.search import SearchRequest, SearchResponse, SearchResultItem
from asar.deliberation import SimpleSynthesizer
from asar.evaluation import ExperimentLogger
from asar.execution import WebSearchExecutor
from asar.memory import WorkingMemory
from asar.orchestration import SequentialOrchestrator
from asar.planning import SimplePlanner
from asar.verification import EvidenceChecker
from schemas.research_output import ResearchOutput
from schemas.verification_result import ClaimVerdict


CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
QUESTION = "What were the main causes of the 2008 financial crisis?"
STEP_1 = "Identify the broad structural causes most often named in retrospective analyses of the 2008 financial crisis."
STEP_2 = "Gather evidence about housing leverage, subprime lending, and mortgage securitization before the 2008 financial crisis."
STEP_3 = "Gather evidence about regulation, risk models, and contagion across financial institutions during the 2008 financial crisis."


class DeterministicMockLLMClient:
    """One mock LLM client that serves both planning and deliberation deterministically."""

    def __init__(self) -> None:
        self.requests: list[LLMGenerationRequest] = []

    async def generate(self, request: LLMGenerationRequest) -> LLMGenerationResponse:
        self.requests.append(request)
        component = request.metadata.get("component")

        if component == "planning":
            output_text = json.dumps(
                {
                    "steps": [
                        {
                            "description": STEP_1,
                            "expected_output": "A concise list of the most-cited structural drivers.",
                            "success_criteria": "The list captures the main structural causes repeatedly named in retrospectives.",
                        },
                        {
                            "description": STEP_2,
                            "expected_output": "Evidence notes on mortgage market leverage and securitization.",
                            "success_criteria": "The notes cover leverage, subprime lending, and securitization mechanisms.",
                        },
                        {
                            "description": STEP_3,
                            "expected_output": "Evidence notes on regulatory weakness, risk models, and contagion.",
                            "success_criteria": "The notes explain how regulation, risk models, and contagion worsened the crisis.",
                        },
                    ]
                },
                sort_keys=True,
            )
        elif component == "deliberation":
            evidence_payload = _extract_evidence_payload(request.messages[-1].content)
            claims = [
                {
                    "text": item["content"],
                    "supporting_evidence_ids": [item["evidence_id"]],
                    "contradicting_evidence_ids": [],
                    "epistemic_status": "high_confidence",
                    "reasoning_trace": f"Claim mirrors {item['evidence_id']} exactly for deterministic verification.",
                }
                for item in evidence_payload
            ]
            output_text = json.dumps(
                {
                    "synthesis": "The evidence points to leverage, securitization, and regulatory contagion as the main crisis drivers.",
                    "claims": claims,
                    "information_gaps": [],
                    "conflicts": [],
                },
                sort_keys=True,
            )
        else:
            raise AssertionError(f"Unexpected LLM component: {component}")

        return LLMGenerationResponse(
            model=request.model,
            output_text=output_text,
            usage=TokenUsage(input_tokens=50, output_tokens=80),
        )


class DeterministicMockSearchClient:
    """Query-keyed mock search client for the canonical Tier 1 integration run."""

    def __init__(self) -> None:
        self.requests: list[SearchRequest] = []
        self._responses = {
            STEP_1: SearchResponse(
                results=[
                    SearchResultItem(
                        url="https://example.com/structural-causes",
                        title="Retrospective on the Crisis",
                        snippet="Retrospective analyses named a housing bubble and excessive leverage as core structural causes of the 2008 financial crisis.",
                        rank=1,
                        score=0.95,
                        source_name="Example Review",
                    )
                ]
            ),
            STEP_2: SearchResponse(
                results=[
                    SearchResultItem(
                        url="https://example.com/mortgage-market",
                        title="Mortgage Market Breakdown",
                        snippet="Reviews linked the crisis to subprime lending, mortgage securitization, and highly leveraged balance sheets before 2008.",
                        rank=1,
                        score=0.93,
                        source_name="Example Finance Journal",
                    )
                ]
            ),
            STEP_3: SearchResponse(
                results=[
                    SearchResultItem(
                        url="https://example.com/regulation-contagion",
                        title="Regulation and Contagion",
                        snippet="Post-crisis reviews highlighted weak regulation, flawed risk models, and contagion through interconnected financial institutions.",
                        rank=1,
                        score=0.92,
                        source_name="Example Economics Review",
                    )
                ]
            ),
        }

    async def search(self, request: SearchRequest) -> SearchResponse:
        self.requests.append(request)
        try:
            return self._responses[request.query]
        except KeyError as exc:
            raise AssertionError(f"Unexpected search query: {request.query}") from exc


def _extract_evidence_payload(prompt: str) -> list[dict[str, str]]:
    return json.loads(prompt.split("Evidence: ", 1)[1])


@pytest.mark.asyncio
async def test_mocked_v0_pipeline_end_to_end_for_financial_crisis_question(tmp_path: Path) -> None:
    settings = load_settings(CONFIG_DIR)
    setup_logging(settings.pipeline.logging, force=True, stream=io.StringIO())
    llm_client = DeterministicMockLLMClient()
    search_client = DeterministicMockSearchClient()

    orchestrator = SequentialOrchestrator(
        planner=SimplePlanner(llm_client, settings),
        executor=WebSearchExecutor(search_client, settings),
        memory=WorkingMemory(max_items=10),
        synthesizer=SimpleSynthesizer(llm_client, settings),
        verifier=EvidenceChecker(settings),
        evaluator=ExperimentLogger(settings, output_dir=tmp_path),
        settings=settings,
    )

    output = await orchestrator.run(QUESTION)

    validated_output = ResearchOutput.model_validate(output.model_dump(mode="json"))
    assert validated_output.goal == QUESTION
    assert len(validated_output.plan.steps) == 3
    assert len(validated_output.evidence) == 3
    assert validated_output.decision is not None
    assert validated_output.verification is not None
    assert validated_output.experiment is not None
    assert validated_output.created_at.utcoffset() is not None

    assert [request.metadata["component"] for request in llm_client.requests] == ["planning", "deliberation"]
    assert [request.query for request in search_client.requests] == [STEP_1, STEP_2, STEP_3]
    assert all(request.metadata["step_id"] == step.step_id for request, step in zip(search_client.requests, output.plan.steps))

    assert all(item.source.additional["step_id"] == step.step_id for item, step in zip(output.evidence, output.plan.steps))
    assert output.experiment.metrics["plan_coverage"] == 1.0
    assert output.experiment.metrics["evidence_utilization"] == 1.0
    assert output.experiment.metrics["groundedness"] == 1.0

    verdicts = [claim_verdict.verdict for claim_verdict in output.verification.claim_verdicts]
    assert verdicts == [ClaimVerdict.SUPPORTED, ClaimVerdict.SUPPORTED, ClaimVerdict.SUPPORTED]
    assert output.verification.summary == "supported=3, unsupported=0, insufficient=0, contradicted=0"

    artifact_paths = [Path(path) for path in output.experiment.artifacts]
    assert [path.name for path in artifact_paths] == ["output.json", "experiment.json"]
    assert all(path.exists() for path in artifact_paths)

    output_payload = json.loads(artifact_paths[0].read_text(encoding="utf-8"))
    experiment_payload = json.loads(artifact_paths[1].read_text(encoding="utf-8"))
    assert output_payload["goal"] == QUESTION
    assert experiment_payload["metrics"]["plan_coverage"] == 1.0
    assert experiment_payload["metrics"]["groundedness"] == 1.0

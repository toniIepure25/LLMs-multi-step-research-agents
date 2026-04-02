"""
Deterministic mock clients for local v0 demos.
"""

from __future__ import annotations

import json
import re

from asar.core.llm import (
    LLMGenerationRequest,
    LLMGenerationResponse,
    TokenUsage,
)
from asar.core.search import SearchRequest, SearchResponse, SearchResultItem

DEFAULT_DEMO_GOAL = "What were the main causes of the 2008 financial crisis?"
_DEFAULT_STEP_1 = (
    "Identify the broad structural causes most often named in retrospective "
    "analyses of the 2008 financial crisis."
)
_DEFAULT_STEP_2 = (
    "Gather evidence about housing leverage, subprime lending, and mortgage "
    "securitization before the 2008 financial crisis."
)
_DEFAULT_STEP_3 = (
    "Gather evidence about regulation, risk models, and contagion across "
    "financial institutions during the 2008 financial crisis."
)


class DeterministicDemoLLMClient:
    """Serve compact, deterministic planner and synthesizer outputs for demos."""

    async def generate(self, request: LLMGenerationRequest) -> LLMGenerationResponse:
        component = request.metadata.get("component")

        if component == "planning":
            goal = _extract_goal(request.messages[-1].content)
            output_text = json.dumps({"steps": _planner_steps_for_goal(goal)}, sort_keys=True)
        elif component == "deliberation":
            evidence_payload = _extract_evidence_payload(request.messages[-1].content)
            claims = [
                {
                    "text": item["content"],
                    "supporting_evidence_ids": item["supporting_evidence_ids"],
                    "contradicting_evidence_ids": [],
                    "epistemic_status": "high_confidence",
                    "reasoning_trace": (
                        "Claim mirrors "
                        f"{', '.join(item['supporting_evidence_ids'])} "
                        "for deterministic support checking."
                    ),
                }
                for item in evidence_payload[:4]
            ]
            output_text = json.dumps(
                {
                    "synthesis": "Deterministic demo synthesis over the collected evidence.",
                    "claims": claims,
                    "information_gaps": [],
                    "conflicts": [],
                },
                sort_keys=True,
            )
        else:
            raise ValueError(f"Unsupported demo LLM component: {component}")

        return LLMGenerationResponse(
            model=request.model,
            output_text=output_text,
            usage=TokenUsage(input_tokens=40, output_tokens=80),
        )


class DeterministicDemoSearchClient:
    """Return small, stable search results keyed by query text."""

    async def search(self, request: SearchRequest) -> SearchResponse:
        snippet = _search_snippet_for_query(request.query)
        return SearchResponse(
            results=[
                SearchResultItem(
                    url=f"https://example.com/demo/{_slugify(request.query)}",
                    title="ASAR deterministic demo source",
                    snippet=snippet,
                    rank=1,
                    score=0.95,
                    source_name="ASAR Demo Corpus",
                    raw_payload={"query": request.query},
                )
            ]
        )


def _planner_steps_for_goal(goal: str) -> list[dict[str, str]]:
    if goal == DEFAULT_DEMO_GOAL:
        return [
            {
                "description": _DEFAULT_STEP_1,
                "expected_output": "A concise list of the most-cited structural drivers.",
                "success_criteria": (
                    "The list captures the broad causes repeatedly named in "
                    "retrospectives."
                ),
            },
            {
                "description": _DEFAULT_STEP_2,
                "expected_output": (
                    "Evidence notes on mortgage market leverage and "
                    "securitization."
                ),
                "success_criteria": (
                    "The notes cover leverage, subprime lending, and "
                    "securitization mechanisms."
                ),
            },
            {
                "description": _DEFAULT_STEP_3,
                "expected_output": "Evidence notes on regulation, risk models, and contagion.",
                "success_criteria": (
                    "The notes explain how regulation, risk models, and "
                    "contagion worsened the crisis."
                ),
            },
        ]

    return [
        {
            "description": (
                "Identify the main factors most often cited in explanations "
                f"of {goal}."
            ),
            "expected_output": "A short list of the main factors to investigate.",
            "success_criteria": (
                "The list captures the major explanations relevant to the goal."
            ),
        },
        {
            "description": (
                "Gather evidence about the strongest direct causes or drivers "
                f"related to {goal}."
            ),
            "expected_output": "Evidence notes on direct causes or drivers.",
            "success_criteria": (
                "The notes include direct causes or mechanisms linked to the "
                "goal."
            ),
        },
        {
            "description": (
                "Gather evidence about amplifying conditions, disagreements, "
                f"or consequences related to {goal}."
            ),
            "expected_output": (
                "Evidence notes on amplifying conditions and disagreements."
            ),
            "success_criteria": (
                "The notes capture important amplifiers, disagreements, or "
                "consequences."
            ),
        },
    ]


def _extract_goal(prompt: str) -> str:
    match = re.search(r"Goal: (.+?)\nConstraints:", prompt, re.DOTALL)
    if match is None:
        raise ValueError("Demo planner prompt did not include a goal")
    return match.group(1).strip()


def _extract_evidence_payload(prompt: str) -> list[dict[str, object]]:
    if "Evidence Bundles: " in prompt:
        payload = json.loads(prompt.split("Evidence Bundles: ", 1)[1])
        return [
            {
                "content": str(item["content"]),
                "supporting_evidence_ids": [
                    str(evidence_id) for evidence_id in item["evidence_ids"]
                ],
            }
            for item in payload
        ]

    payload = json.loads(prompt.split("Evidence: ", 1)[1])
    return [
        {
            "content": str(item["content"]),
            "supporting_evidence_ids": [str(item["evidence_id"])],
        }
        for item in payload
    ]


def _search_snippet_for_query(query: str) -> str:
    if query == _DEFAULT_STEP_1:
        return (
            "Retrospective analyses named a housing bubble and excessive "
            "leverage as core structural "
            "causes of the 2008 financial crisis."
        )
    if query == _DEFAULT_STEP_2:
        return (
            "Reviews linked the crisis to subprime lending, mortgage securitization, and highly "
            "leveraged balance sheets before 2008."
        )
    if query == _DEFAULT_STEP_3:
        return (
            "Post-crisis reviews highlighted weak regulation, flawed risk models, and contagion "
            "through interconnected financial institutions."
        )
    return (
        f"Deterministic mock evidence for {query}. Analysts identified a main factor, an enabling "
        "mechanism, and a relevant downstream consequence."
    )


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "query"

"""
Unit tests for the v0 `SimpleSynthesizer`.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from asar.common import load_settings, setup_logging
from asar.core.errors import DeliberationError, LLMClientError
from asar.core.llm import (
    LLMGenerationRequest,
    LLMGenerationResponse,
    LLMMessage,
    MessageRole,
    TokenUsage,
)
from asar.deliberation import ClaimSelector, SimpleSynthesizer
from schemas.candidate_claim_set import CandidateClaimSet
from schemas.decision_packet import EpistemicStatus
from schemas.evidence_item import EvidenceItem, SourceMetadata, SourceType

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def _evidence(evidence_id: str, content: str) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        task_id="task_123",
        content=content,
        source=SourceMetadata(
            source_type=SourceType.WEB_SEARCH,
            url=f"https://example.com/{evidence_id}",
            title=f"Source for {evidence_id}",
            raw_snippet=content,
        ),
    )


def _context(*, plan_id: str = "plan_123", goal: str | None = None) -> str:
    payload: dict[str, str] = {"plan_id": plan_id}
    if goal is not None:
        payload["goal"] = goal
    return json.dumps(payload)


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
            usage=TokenUsage(input_tokens=20, output_tokens=40),
        )


@pytest.mark.asyncio
async def test_simple_synthesizer_happy_path_returns_valid_decision_packet() -> None:
    settings = load_settings(CONFIG_DIR)
    setup_logging(settings.pipeline.logging, force=True, stream=io.StringIO())
    llm_client = StubLLMClient(
        """
        {
          "synthesis": "The evidence points to two major drivers and one open disagreement.",
          "claims": [
            {
              "text": "Battery storage costs fell across multiple markets in 2024.",
              "supporting_evidence_ids": ["evidence_1"],
              "contradicting_evidence_ids": [],
              "epistemic_status": "high_confidence",
              "reasoning_trace": "Evidence_1 states the trend directly."
            },
            {
              "text": "Policy incentives remained an important factor in deployment decisions.",
              "supporting_evidence_ids": ["evidence_2"],
              "contradicting_evidence_ids": [],
              "epistemic_status": "moderate_confidence",
              "reasoning_trace": "Evidence_2 ties incentives to deployment decisions."
            }
          ],
          "information_gaps": ["Long-term effects remain uncertain."],
          "conflicts": []
        }
        """
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)

    decision = await synthesizer.deliberate(
        [
            _evidence("evidence_1", "Battery storage costs fell across multiple markets in 2024."),
            _evidence("evidence_2", "Policy incentives influenced deployment decisions."),
        ],
        context="plan_123",
    )

    assert decision.plan_id == "plan_123"
    assert decision.decision_id.startswith("decision_")
    assert len(decision.claims) == 2
    assert all(claim.claim_id.startswith("claim_") for claim in decision.claims)
    assert decision.claims[0].epistemic_status is EpistemicStatus.HIGH_CONFIDENCE


@pytest.mark.asyncio
async def test_simple_synthesizer_can_emit_typed_candidate_claims() -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        json.dumps(
            {
                "synthesis": "Two candidate claims stand out.",
                "claims": [
                    {
                        "text": "Securitization contributed to the 2008 financial crisis.",
                        "supporting_evidence_ids": ["evidence_1"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                        "reasoning_trace": "Evidence_1 ties securitization to systemic risk.",
                    },
                    {
                        "text": (
                            "Deregulation of the OTC derivatives market contributed to "
                            "the 2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_2"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                        "reasoning_trace": "Evidence_2 links deregulation to rising leverage.",
                    },
                ],
                "information_gaps": ["Relative weight of each cause remains uncertain."],
                "conflicts": [],
            }
        )
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)

    candidate_set = await synthesizer.generate_candidate_claims(
        [
            _evidence("evidence_1", "Securitization spread mortgage risk through the system."),
            _evidence("evidence_2", "Deregulation of OTC derivatives increased systemic risk."),
        ],
        context=_context(goal="What were the main causes of the 2008 financial crisis?"),
    )

    assert isinstance(candidate_set, CandidateClaimSet)
    assert candidate_set.candidate_set_id.startswith("candidate_set_")
    assert candidate_set.plan_id == "plan_123"
    assert candidate_set.draft_synthesis == "Two candidate claims stand out."
    assert candidate_set.information_gaps == ["Relative weight of each cause remains uncertain."]
    assert [claim.text for claim in candidate_set.claims] == [
        "Securitization contributed to the 2008 financial crisis.",
        "Deregulation of the OTC derivatives market contributed to the 2008 financial crisis.",
    ]
    assert [claim.source_claim_index for claim in candidate_set.claims] == [1, 2]
    assert all(
        claim.candidate_claim_id.startswith("candidate_claim_")
        for claim in candidate_set.claims
    )


@pytest.mark.asyncio
async def test_simple_synthesizer_candidate_claims_preserve_evidence_references() -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        json.dumps(
            {
                "claims": [
                    {
                        "text": "Securitization contributed to the 2008 financial crisis.",
                        "supporting_evidence_ids": ["evidence_1", "evidence_2"],
                        "contradicting_evidence_ids": ["evidence_3"],
                        "epistemic_status": "moderate_confidence",
                    }
                ],
                "information_gaps": [],
                "conflicts": [],
            }
        )
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)

    candidate_set = await synthesizer.generate_candidate_claims(
        [
            _evidence("evidence_1", "Securitization spread risk."),
            _evidence("evidence_2", "Securitization weakened underwriting discipline."),
            _evidence("evidence_3", "Some evidence disputes the magnitude of the effect."),
        ],
        context=_context(goal="What were the main causes of the 2008 financial crisis?"),
    )

    assert candidate_set.claims[0].supporting_evidence_ids == ["evidence_1", "evidence_2"]
    assert candidate_set.claims[0].contradicting_evidence_ids == ["evidence_3"]


@pytest.mark.asyncio
async def test_simple_synthesizer_candidate_generation_keeps_v0_decision_contract_intact() -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        json.dumps(
            {
                "claims": [
                    {
                        "text": "Securitization contributed to the 2008 financial crisis.",
                        "supporting_evidence_ids": ["evidence_1"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    }
                ],
                "information_gaps": [],
                "conflicts": [],
            }
        )
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)

    decision = await synthesizer.deliberate(
        [_evidence("evidence_1", "Securitization spread risk.")],
        context=_context(goal="What were the main causes of the 2008 financial crisis?"),
    )

    assert decision.decision_id.startswith("decision_")
    assert len(decision.claims) == 1
    assert decision.claims[0].claim_id.startswith("claim_")


@pytest.mark.asyncio
async def test_simple_synthesizer_uses_selector_to_prefer_supported_final_claims() -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        json.dumps(
            {
                "claims": [
                    {
                        "text": (
                            "Securitization of subprime mortgages contributed to the "
                            "2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_1"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "Securitization contributed to the 2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_1", "evidence_2"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                ],
                "information_gaps": [],
                "conflicts": [],
            }
        )
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)

    decision = await synthesizer.deliberate(
        [
            _evidence(
                "evidence_1",
                "Securitization spread mortgage risk through the financial system.",
            ),
            _evidence(
                "evidence_2",
                "Securitization weakened underwriting discipline before 2008.",
            ),
        ],
        context=_context(goal="What were the main causes of the 2008 financial crisis?"),
    )

    assert [claim.text for claim in decision.claims] == [
        "Securitization contributed to the 2008 financial crisis."
    ]


@pytest.mark.asyncio
async def test_simple_synthesizer_uses_selector_to_prefer_exact_goal_event_claims() -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        json.dumps(
            {
                "claims": [
                    {
                        "text": (
                            "Securitization of subprime mortgages contributed to the "
                            "housing crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_1", "evidence_2"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "Securitization contributed to the 2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_1", "evidence_3"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                ],
                "information_gaps": [],
                "conflicts": [],
            }
        )
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)

    decision = await synthesizer.deliberate(
        [
            _evidence("evidence_1", "Securitization spread mortgage risk."),
            _evidence("evidence_2", "Subprime mortgages intensified the housing crisis."),
            _evidence("evidence_3", "Securitization contributed to the 2008 crisis."),
        ],
        context=_context(goal="What were the main causes of the 2008 financial crisis?"),
    )

    assert [claim.text for claim in decision.claims] == [
        "Securitization contributed to the 2008 financial crisis."
    ]


@pytest.mark.asyncio
async def test_simple_synthesizer_uses_selector_to_drop_thin_same_family_claim() -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        json.dumps(
            {
                "claims": [
                    {
                        "text": (
                            "Securitization contributed to the 2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_1"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "Mortgage securitization contributed to the 2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_1", "evidence_2"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "Deregulation of the OTC derivatives market contributed to "
                            "the 2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_3"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                ],
                "information_gaps": [],
                "conflicts": [],
            }
        )
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)

    decision = await synthesizer.deliberate(
        [
            _evidence(
                "evidence_1",
                "Securitization of financial instruments packaged loans into securities.",
            ),
            _evidence(
                "evidence_2",
                "Mortgage securitization weakened underwriting discipline before the crisis.",
            ),
            _evidence(
                "evidence_3",
                "Deregulation of the OTC derivatives market increased leverage before 2008.",
            ),
        ],
        context=_context(goal="What were the main causes of the 2008 financial crisis?"),
    )

    assert [claim.text for claim in decision.claims] == [
        "Mortgage securitization contributed to the 2008 financial crisis.",
        "Deregulation of the OTC derivatives market contributed to the 2008 financial crisis.",
    ]


@pytest.mark.asyncio
async def test_simple_synthesizer_backfills_missing_supported_2008_mechanism_families() -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        json.dumps(
            {
                "claims": [
                    {
                        "text": (
                            "Deregulation of the Financial System contributed to the "
                            "2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_1"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "Securitization of subprime mortgages contributed to the "
                            "2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_2"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                ],
                "information_gaps": [],
                "conflicts": [],
            }
        )
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)
    context = _context(goal="What were the main causes of the 2008 financial crisis?")
    evidence = [
        _evidence(
            "evidence_1",
            "Deregulation allowed OTC derivatives counterparties to expand risk "
            "before the 2008 financial crisis.",
        ),
        _evidence(
            "evidence_2",
            "Securitization packaged loans into securities and weakened "
            "underwriting discipline before the crisis.",
        ),
        _evidence(
            "evidence_3",
            "Banks issued mortgages to subprime borrowers before the 2008 financial crisis.",
        ),
        _evidence(
            "evidence_4",
            "Monetary policy kept interest rates low and encouraged excessive "
            "risk-taking before the 2008 financial crisis.",
        ),
    ]

    candidate_set = await synthesizer.generate_candidate_claims(evidence, context=context)

    assert [claim.text for claim in candidate_set.claims] == [
        "Deregulation of the Financial System contributed to the 2008 financial crisis.",
        "Securitization contributed to the 2008 financial crisis.",
        "Deregulation of the OTC derivatives market contributed to the 2008 financial crisis.",
        "Monetary policy contributed to the 2008 financial crisis.",
    ]

    decision = await synthesizer.deliberate(evidence, context=context)

    assert [claim.text for claim in decision.claims] == [
        "Securitization contributed to the 2008 financial crisis.",
        "Deregulation of the OTC derivatives market contributed to the 2008 financial crisis.",
        "Monetary policy contributed to the 2008 financial crisis.",
    ]


@pytest.mark.asyncio
async def test_simple_synthesizer_backfills_subprime_family_from_mbs_evidence(
) -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        json.dumps(
            {
                "claims": [
                    {
                        "text": "Securitization contributed to the 2008 financial crisis.",
                        "supporting_evidence_ids": ["evidence_1"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "Deregulation of the OTC derivatives market contributed to "
                            "the 2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_2"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                ],
                "information_gaps": [],
                "conflicts": [],
            }
        )
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)
    context = _context(goal="What were the main causes of the 2008 financial crisis?")
    evidence = [
        _evidence(
            "evidence_1",
            "Securitization pooled loans into securities sold to investors before 2008.",
        ),
        _evidence(
            "evidence_2",
            "Deregulation of the OTC derivatives market increased leverage before 2008.",
        ),
        _evidence(
            "evidence_3",
            "The failure of subprime mortgage-backed securities destabilized bank balance "
            "sheets before the 2008 financial crisis.",
        ),
    ]

    candidate_set = await synthesizer.generate_candidate_claims(evidence, context=context)

    assert [claim.text for claim in candidate_set.claims] == [
        "Securitization contributed to the 2008 financial crisis.",
        "Deregulation of the OTC derivatives market contributed to the 2008 financial crisis.",
        "Subprime lending contributed to the 2008 financial crisis.",
    ]


@pytest.mark.asyncio
async def test_simple_synthesizer_backfills_mbs_family_from_thin_2008_candidates(
) -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        json.dumps(
            {
                "claims": [
                    {
                        "text": "Securitization contributed to the 2008 financial crisis.",
                        "supporting_evidence_ids": ["evidence_1"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "Deregulation of the OTC derivatives market contributed to "
                            "the 2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_2"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                ],
                "information_gaps": [],
                "conflicts": [],
            }
        )
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)
    context = _context(goal="What were the main causes of the 2008 financial crisis?")
    evidence = [
        _evidence(
            "evidence_1",
            "Securitization pooled loans into securities sold to investors before 2008.",
        ),
        _evidence(
            "evidence_2",
            "Deregulation of the OTC derivatives market increased leverage before 2008.",
        ),
        _evidence(
            "evidence_3",
            "Mortgage-backed debt and other mortgage-backed products amplified losses "
            "during the 2008 financial crisis.",
        ),
    ]

    candidate_set = await synthesizer.generate_candidate_claims(evidence, context=context)

    assert [claim.text for claim in candidate_set.claims] == [
        "Securitization contributed to the 2008 financial crisis.",
        "Deregulation of the OTC derivatives market contributed to the 2008 financial crisis.",
        "Mortgage-backed securities contributed to the 2008 financial crisis.",
    ]

    decision = await synthesizer.deliberate(evidence, context=context)
    selected_texts = [claim.text for claim in decision.claims]

    assert selected_texts == [
        "Deregulation of the OTC derivatives market contributed to the 2008 financial crisis.",
        "Mortgage-backed securities contributed to the 2008 financial crisis.",
    ]
    assert "Securitization contributed to the 2008 financial crisis." not in selected_texts


@pytest.mark.asyncio
async def test_simple_synthesizer_prefers_stronger_attributed_2008_claim_in_selector_path(
) -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        json.dumps(
            {
                "claims": [
                    {
                        "text": "Monetary policy contributed to the 2008 financial crisis.",
                        "supporting_evidence_ids": ["evidence_1", "evidence_2"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": "Subprime lending contributed to the 2008 financial crisis.",
                        "supporting_evidence_ids": ["evidence_3"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                ],
                "information_gaps": [],
                "conflicts": [],
            }
        )
    )
    synthesizer = SimpleSynthesizer(
        llm_client,
        settings,
        claim_selector=ClaimSelector(max_selected_claims=1),
    )
    context = _context(goal="What were the main causes of the 2008 financial crisis?")
    evidence = [
        _evidence(
            "evidence_1",
            "Interest rates stayed low before the 2008 financial crisis.",
        ),
        _evidence(
            "evidence_2",
            "Banks packaged loans into securities before the crisis.",
        ),
        _evidence(
            "evidence_3",
            "Banks issued mortgages to subprime borrowers, and subprime lending "
            "expanded before the 2008 financial crisis.",
        ),
    ]

    decision = await synthesizer.deliberate(evidence, context=context)

    assert [claim.text for claim in decision.claims] == [
        "Subprime lending contributed to the 2008 financial crisis."
    ]


@pytest.mark.asyncio
async def test_simple_synthesizer_restores_third_supported_2008_mechanism_under_v1_1(
) -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        json.dumps(
            {
                "claims": [
                    {
                        "text": "Securitization contributed to the 2008 financial crisis.",
                        "supporting_evidence_ids": ["evidence_1"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "Deregulation of the OTC derivatives market contributed to "
                            "the 2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_2"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": "Subprime lending contributed to the 2008 financial crisis.",
                        "supporting_evidence_ids": ["evidence_3"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": "Monetary policy contributed to the 2008 financial crisis.",
                        "supporting_evidence_ids": ["evidence_4"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                ],
                "information_gaps": [],
                "conflicts": [],
            }
        )
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)
    context = _context(goal="What were the main causes of the 2008 financial crisis?")
    evidence = [
        _evidence(
            "evidence_1",
            "Securitization pooled loans into securities and spread mortgage risk.",
        ),
        _evidence(
            "evidence_2",
            "Deregulation of the OTC derivatives market increased leverage before 2008.",
        ),
        _evidence(
            "evidence_3",
            "Subprime mortgage-backed securities and subprime borrowers destabilized "
            "banks before the 2008 financial crisis.",
        ),
        _evidence(
            "evidence_4",
            "Monetary policy kept interest rates low and encouraged risk-taking before "
            "the 2008 financial crisis.",
        ),
    ]

    decision = await synthesizer.deliberate(evidence, context=context)
    selected_texts = [claim.text for claim in decision.claims]

    assert len(decision.claims) == 3
    assert (
        "Deregulation of the OTC derivatives market contributed to the 2008 financial "
        "crisis."
    ) in selected_texts
    assert "Subprime lending contributed to the 2008 financial crisis." in selected_texts
    assert "Monetary policy contributed to the 2008 financial crisis." in selected_texts
    assert "Securitization contributed to the 2008 financial crisis." not in selected_texts


@pytest.mark.asyncio
async def test_simple_synthesizer_preserves_diverse_supported_set_in_full_v1_1_path(
) -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        json.dumps(
            {
                "claims": [
                    {
                        "text": "Bank failures contributed to the Great Depression.",
                        "supporting_evidence_ids": ["evidence_1"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": "Reduced consumer spending contributed to the Great Depression.",
                        "supporting_evidence_ids": ["evidence_1"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "The collapse of world trade due to the Smoot-Hawley Tariff "
                            "contributed to the Great Depression."
                        ),
                        "supporting_evidence_ids": ["evidence_2"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "The stock market crash of 1929 contributed to the Great "
                            "Depression."
                        ),
                        "supporting_evidence_ids": ["evidence_3"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                ],
                "information_gaps": [],
                "conflicts": [],
            }
        )
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)
    context = _context(goal="What were the main causes of the Great Depression?")
    evidence = [
        _evidence(
            "evidence_1",
            "A broad survey of the Great Depression highlights bank failures and "
            "reduced consumer spending as linked parts of the downturn.",
        ),
        _evidence(
            "evidence_2",
            "The Smoot-Hawley Tariff reduced world trade and deepened the Great Depression.",
        ),
        _evidence(
            "evidence_3",
            "The stock market crash of 1929 undermined confidence and spending.",
        ),
    ]

    decision = await synthesizer.deliberate(evidence, context=context)
    selected_texts = [claim.text for claim in decision.claims]

    assert len(decision.claims) == 3
    assert any(
        "world trade" in text.lower() or "smoot-hawley" in text.lower()
        for text in selected_texts
    )
    assert "The stock market crash of 1929 contributed to the Great Depression." in selected_texts
    assert sum(
        text in selected_texts
        for text in [
            "Bank failures contributed to the Great Depression.",
            "Reduced consumer spending contributed to the Great Depression.",
        ]
    ) == 1
    assert {
        evidence_id
        for claim in decision.claims
        for evidence_id in claim.supporting_evidence_ids
    } == {"evidence_1", "evidence_2", "evidence_3"}


@pytest.mark.asyncio
async def test_simple_synthesizer_backfills_stock_crash_family_for_thin_great_depression_candidates(
) -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        json.dumps(
            {
                "claims": [
                    {
                        "text": (
                            "Banking panics and monetary policies contributed to the "
                            "Great Depression."
                        ),
                        "supporting_evidence_ids": ["evidence_1"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "War reparations and protectionism triggered the Great "
                            "Depression."
                        ),
                        "supporting_evidence_ids": ["evidence_2"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                ],
                "information_gaps": [],
                "conflicts": [],
            }
        )
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)
    context = _context(goal="What were the main causes of the Great Depression?")
    evidence = [
        _evidence(
            "evidence_1",
            "Banking panics and tight monetary policies deepened the Great Depression.",
        ),
        _evidence(
            "evidence_2",
            "War reparations and protectionism reduced world trade during the Depression.",
        ),
        _evidence(
            "evidence_3",
            "The stock market crash of 1929 undermined confidence before the Great Depression.",
        ),
    ]

    candidate_set = await synthesizer.generate_candidate_claims(evidence, context=context)

    assert [claim.text for claim in candidate_set.claims] == [
        "Banking panics and monetary policies contributed to the Great Depression.",
        "War reparations and protectionism triggered the Great Depression.",
        "The stock market crash of 1929 contributed to the Great Depression.",
    ]

    decision = await synthesizer.deliberate(evidence, context=context)

    assert [claim.text for claim in decision.claims] == [
        "Banking panics and monetary policies contributed to the Great Depression.",
        "War reparations and protectionism triggered the Great Depression.",
        "The stock market crash of 1929 contributed to the Great Depression.",
    ]


@pytest.mark.asyncio
async def test_simple_synthesizer_filters_supported_but_off_question_claims_for_causal_goals(
) -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        json.dumps(
            {
                "synthesis": "The crisis had multiple drivers.",
                "claims": [
                    {
                        "text": "Deregulation contributed to the 2008 financial crisis.",
                        "supporting_evidence_ids": ["evidence_1"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "Subprime mortgage issuance was a major factor in the 2008 "
                            "financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_2"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "The Emergency Economic Stabilization Act of 2008 was passed "
                            "in response to the financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_3"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "high_confidence",
                    },
                ],
                "information_gaps": [],
                "conflicts": [],
            }
        )
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)

    decision = await synthesizer.deliberate(
        [
            _evidence("evidence_1", "Deregulation contributed to systemic risk."),
            _evidence("evidence_2", "Subprime mortgage issuance inflated the housing bubble."),
            _evidence(
                "evidence_3",
                "The Emergency Economic Stabilization Act of 2008 established a bailout fund.",
            ),
        ],
        context=_context(goal="What were the main causes of the 2008 financial crisis?"),
    )

    assert [claim.text for claim in decision.claims] == [
        "Deregulation contributed to the 2008 financial crisis.",
        "Subprime mortgage issuance was a major factor in the 2008 financial crisis.",
    ]
    assert all(claim.claim_id.startswith("claim_") for claim in decision.claims)
    assert decision.claims[0].supporting_evidence_ids == ["evidence_1"]
    assert decision.claims[1].supporting_evidence_ids == ["evidence_2"]


@pytest.mark.asyncio
async def test_simple_synthesizer_keeps_grounded_causal_claims_for_causal_goals() -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        """
        {
          "claims": [
            {
              "text": "Securitization amplified losses across the financial system.",
              "supporting_evidence_ids": ["evidence_1"],
              "contradicting_evidence_ids": [],
              "epistemic_status": "moderate_confidence"
            },
            {
              "text": "Weak underwriting standards contributed to the housing bubble.",
              "supporting_evidence_ids": ["evidence_2"],
              "contradicting_evidence_ids": [],
              "epistemic_status": "moderate_confidence"
            }
          ],
          "information_gaps": [],
          "conflicts": []
        }
        """
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)

    decision = await synthesizer.deliberate(
        [
            _evidence("evidence_1", "Securitization amplified losses across the financial system."),
            _evidence(
                "evidence_2",
                "Weak underwriting standards contributed to the housing bubble.",
            ),
        ],
        context=_context(goal="What were the main causes of the 2008 financial crisis?"),
    )

    assert len(decision.claims) == 2
    assert (
        decision.claims[0].text
        == "Securitization amplified losses across the financial system."
    )
    assert (
        decision.claims[1].text
        == "Weak underwriting standards contributed to the housing bubble."
    )


@pytest.mark.asyncio
async def test_simple_synthesizer_irrelevant_only_claims_fail_with_typed_details() -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        json.dumps(
            {
                "claims": [
                    {
                        "text": (
                            "The Emergency Economic Stabilization Act of 2008 was passed "
                            "in response to the financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_1"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "high_confidence",
                    }
                ],
                "information_gaps": [],
                "conflicts": [],
            }
        )
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)

    result = await synthesizer.deliberate_result(
        [
            _evidence(
                "evidence_1",
                "The Emergency Economic Stabilization Act of 2008 established a bailout fund.",
            ),
        ],
        context=_context(goal="What were the main causes of the 2008 financial crisis?"),
    )

    assert result.is_error
    assert result.error is not None
    assert result.error.code == "deliberation_response_invalid"
    assert result.error.details["goal"] == "What were the main causes of the 2008 financial crisis?"
    assert result.error.details["rejected_claims"] == [
        {
            "claim_index": 1,
            "text": (
                "The Emergency Economic Stabilization Act of 2008 was passed in response "
                "to the financial crisis."
            ),
            "reason": "claim_describes_response_not_cause",
        }
    ]


@pytest.mark.asyncio
async def test_simple_synthesizer_prompt_requires_answering_the_goal() -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        """
        {
          "claims": [
            {
              "text": "Deregulation contributed to the crisis.",
              "supporting_evidence_ids": ["evidence_1"],
              "contradicting_evidence_ids": [],
              "epistemic_status": "moderate_confidence"
            }
          ],
          "information_gaps": [],
          "conflicts": []
        }
        """
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)

    await synthesizer.deliberate(
        [_evidence("evidence_1", "Deregulation contributed to the crisis.")],
        context=_context(goal="What were the main causes of the 2008 financial crisis?"),
    )

    prompt = llm_client.requests[0].messages[1].content
    assert "every claim must directly answer the Goal" in prompt
    assert "must state a cause-like answer rather than a response" in prompt
    assert "prefer specific mechanism-level claims over vague umbrella summaries" in prompt
    assert "prefer the most directly supported version of a mechanism claim" in prompt
    assert "keep them as separate claims rather than collapsing them into one" in prompt
    assert "rewrite copied evidence phrasing into a short direct causal claim" in prompt
    assert "name the target event explicitly when possible" in prompt


@pytest.mark.asyncio
async def test_simple_synthesizer_prefers_specific_claims_over_vague_umbrella_claims() -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        json.dumps(
            {
                "synthesis": "The crash had several causes.",
                "claims": [
                    {
                        "text": "A perfect storm of unlucky factors caused the Great Depression.",
                        "supporting_evidence_ids": ["evidence_1"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "Bank failures contracted credit and worsened the Great "
                            "Depression."
                        ),
                        "supporting_evidence_ids": ["evidence_2"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": "Monetary contraction deepened the Great Depression.",
                        "supporting_evidence_ids": ["evidence_3"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                ],
                "information_gaps": [],
                "conflicts": [],
            }
        )
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)

    decision = await synthesizer.deliberate(
        [
            _evidence("evidence_1", "Broad summaries mention several causes."),
            _evidence("evidence_2", "Bank failures contracted credit and worsened the Depression."),
            _evidence("evidence_3", "Monetary contraction deepened the Depression."),
        ],
        context=_context(goal="What were the main causes of the Great Depression?"),
    )

    assert [claim.text for claim in decision.claims] == [
        "Bank failures contracted credit and worsened the Great Depression.",
        "Monetary contraction deepened the Great Depression.",
    ]


@pytest.mark.asyncio
async def test_simple_synthesizer_prefers_diverse_supported_great_depression_claims(
) -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        json.dumps(
            {
                "claims": [
                    {
                        "text": "Stock market crashes contributed to the Great Depression.",
                        "supporting_evidence_ids": ["evidence_1"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": "Bank failures contributed to the Great Depression.",
                        "supporting_evidence_ids": ["evidence_1"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "Reduced consumer spending contributed to the Great Depression."
                        ),
                        "supporting_evidence_ids": ["evidence_1"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "The collapse of world trade due to the Smoot-Hawley Tariff "
                            "contributed to the Great Depression."
                        ),
                        "supporting_evidence_ids": ["evidence_2"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                ],
                "information_gaps": [],
                "conflicts": [],
            }
        )
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)

    decision = await synthesizer.deliberate(
        [
            _evidence(
                "evidence_1",
                (
                    "Broad summaries list stock market crashes, bank failures, and reduced "
                    "consumer spending among several causes."
                ),
            ),
            _evidence(
                "evidence_2",
                (
                    "The collapse of world trade due to the Smoot-Hawley Tariff "
                    "deepened the Depression."
                ),
            ),
        ],
        context=_context(goal="What were the main causes of the Great Depression?"),
    )

    assert [claim.text for claim in decision.claims] == [
        "Stock market crashes contributed to the Great Depression.",
        "Reduced consumer spending contributed to the Great Depression.",
        (
            "The collapse of world trade due to the Smoot-Hawley Tariff "
            "contributed to the Great Depression."
        ),
    ]


@pytest.mark.asyncio
async def test_simple_synthesizer_keeps_vague_causal_claim_if_it_is_the_only_option() -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        json.dumps(
            {
                "claims": [
                    {
                        "text": "A perfect storm of unlucky factors caused the Great Depression.",
                        "supporting_evidence_ids": ["evidence_1"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "low_confidence",
                    }
                ],
                "information_gaps": [],
                "conflicts": [],
            }
        )
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)

    decision = await synthesizer.deliberate(
        [_evidence("evidence_1", "Some historical summaries describe several causes.")],
        context=_context(goal="What were the main causes of the Great Depression?"),
    )

    assert [claim.text for claim in decision.claims] == [
        "A perfect storm of unlucky factors caused the Great Depression."
    ]


@pytest.mark.asyncio
async def test_simple_synthesizer_rewrites_copied_causal_phrasing_into_direct_claims() -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        json.dumps(
            {
                "claims": [
                    {
                        "text": (
                            "The crash was caused by a number of factors, including "
                            "overvaluation of tech companies."
                        ),
                        "supporting_evidence_ids": ["evidence_1"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "A stock market bubble that was caused by speculation in "
                            "dotcom or internet-based businesses from 1995 to 2000."
                        ),
                        "supporting_evidence_ids": ["evidence_2"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                ],
                "information_gaps": [],
                "conflicts": [],
            }
        )
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)

    decision = await synthesizer.deliberate(
        [
            _evidence("evidence_1", "Overvaluation of tech companies contributed to the crash."),
            _evidence(
                "evidence_2",
                "Speculation in dotcom businesses inflated a stock market bubble.",
            ),
        ],
        context=_context(goal="What were the main causes of the dot-com crash?"),
    )

    assert [claim.text for claim in decision.claims] == [
        "Overvaluation of tech companies contributed to the dot-com crash.",
        "Speculation in dotcom or internet-based businesses contributed to the dot-com crash.",
    ]


@pytest.mark.asyncio
async def test_simple_synthesizer_backfills_missing_dotcom_regulation_under_thin_candidates(
) -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        json.dumps(
            {
                "claims": [
                    {
                        "text": (
                            "Speculation in dotcom or internet-based businesses from "
                            "1995 to 2000 caused the dotcom bubble."
                        ),
                        "supporting_evidence_ids": ["evidence_1"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "Overvaluation of tech companies contributed to the dot-com crash."
                        ),
                        "supporting_evidence_ids": ["evidence_2"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                ],
                "information_gaps": [],
                "conflicts": [],
            }
        )
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)
    context = _context(goal="What were the main causes of the dot-com crash?")
    evidence = [
        _evidence(
            "evidence_1",
            "Speculation in dotcom or internet-based businesses inflated a bubble "
            "between 1995 and 2000.",
        ),
        _evidence(
            "evidence_2",
            "The crash was driven in part by overvaluation of tech companies.",
        ),
        _evidence(
            "evidence_3",
            "The crash was also linked to a lack of regulation in the tech industry.",
        ),
    ]

    candidate_set = await synthesizer.generate_candidate_claims(evidence, context=context)

    assert [claim.text for claim in candidate_set.claims] == [
        (
            "Speculation in dotcom or internet-based businesses from 1995 to 2000 "
            "caused the dotcom bubble."
        ),
        "Overvaluation of tech companies contributed to the dot-com crash.",
        "Lack of regulation in the tech industry contributed to the dot-com crash.",
    ]

    decision = await synthesizer.deliberate(evidence, context=context)

    assert [claim.text for claim in decision.claims] == [
        (
            "Speculation in dotcom or internet-based businesses from 1995 to 2000 "
            "caused the dotcom bubble."
        ),
        "Overvaluation of tech companies contributed to the dot-com crash.",
        "Lack of regulation in the tech industry contributed to the dot-com crash.",
    ]


@pytest.mark.asyncio
async def test_simple_synthesizer_prefers_direct_causal_claims_over_descriptive_snippets() -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        json.dumps(
            {
                "claims": [
                    {
                        "text": (
                            "Securitization is more than just a capital markets innovation."
                        ),
                        "supporting_evidence_ids": ["evidence_1"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "Deregulation of the OTC derivatives market contributed to "
                            "the 2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_2"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                ],
                "information_gaps": [],
                "conflicts": [],
            }
        )
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)

    decision = await synthesizer.deliberate(
        [
            _evidence(
                "evidence_1",
                "Securitization connected originators with investors in capital markets.",
            ),
            _evidence(
                "evidence_2",
                "Deregulation of OTC derivatives increased systemic risk before 2008.",
            ),
        ],
        context=_context(goal="What were the main causes of the 2008 financial crisis?"),
    )

    assert [claim.text for claim in decision.claims] == [
        "Deregulation of the OTC derivatives market contributed to the 2008 financial crisis."
    ]


@pytest.mark.asyncio
async def test_simple_synthesizer_rewrites_descriptive_mechanism_claims_into_direct_causal_answers(
) -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        json.dumps(
            {
                "claims": [
                    {
                        "text": (
                            "The deregulated OTC derivatives market posed dangers to the "
                            "financial system."
                        ),
                        "supporting_evidence_ids": ["evidence_1"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "Securitization provided an additional funding source, "
                            "potentially eliminating assets from banks' balance sheets."
                        ),
                        "supporting_evidence_ids": ["evidence_2"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                ],
                "information_gaps": [],
                "conflicts": [],
            }
        )
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)

    decision = await synthesizer.deliberate(
        [
            _evidence(
                "evidence_1",
                "The deregulated OTC derivatives market posed dangers to the financial system.",
            ),
            _evidence(
                "evidence_2",
                (
                    "Securitization provided an additional funding source, potentially "
                    "eliminating assets from banks' balance sheets."
                ),
            ),
        ],
        context=_context(goal="What were the main causes of the 2008 financial crisis?"),
    )

    assert [claim.text for claim in decision.claims] == [
        "Deregulation of the OTC derivatives market contributed to the 2008 financial crisis.",
        "Securitization contributed to the 2008 financial crisis.",
    ]


@pytest.mark.asyncio
async def test_simple_synthesizer_prefers_direct_form_when_both_versions_exist(
) -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        json.dumps(
            {
                "claims": [
                    {
                        "text": (
                            "Securitization provided an additional funding source, "
                            "potentially eliminating assets from banks' balance sheets."
                        ),
                        "supporting_evidence_ids": ["evidence_1"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "Securitization contributed to the 2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_2"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "Deregulation of the OTC derivatives market contributed to "
                            "the financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_3"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                ],
                "information_gaps": [],
                "conflicts": [],
            }
        )
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)

    decision = await synthesizer.deliberate(
        [
            _evidence("evidence_1", "Securitization changed bank incentives."),
            _evidence(
                "evidence_2",
                "Securitization contributed to the 2008 financial crisis.",
            ),
            _evidence(
                "evidence_3",
                "Deregulation of the OTC derivatives market contributed to the financial crisis.",
            ),
        ],
        context=_context(goal="What were the main causes of the 2008 financial crisis?"),
    )

    assert [claim.text for claim in decision.claims] == [
        "Securitization contributed to the 2008 financial crisis.",
        "Deregulation of the OTC derivatives market contributed to the 2008 financial crisis.",
    ]


@pytest.mark.asyncio
async def test_simple_synthesizer_prefers_supported_direct_causal_claim_form() -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        json.dumps(
            {
                "claims": [
                    {
                        "text": (
                            "Securitization of subprime mortgages contributed to the "
                            "2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_1"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "The deregulated OTC derivatives market posed dangers to "
                            "the financial system."
                        ),
                        "supporting_evidence_ids": ["evidence_2"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                ],
                "information_gaps": [],
                "conflicts": [],
            }
        )
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)

    decision = await synthesizer.deliberate(
        [
            _evidence(
                "evidence_1",
                (
                    "Securitization provided an additional funding source and "
                    "potentially eliminated assets from banks' balance sheets."
                ),
            ),
            _evidence(
                "evidence_2",
                (
                    "The deregulated OTC derivatives market posed dangers to the "
                    "financial system."
                ),
            ),
        ],
        context=_context(goal="What were the main causes of the 2008 financial crisis?"),
    )

    assert [claim.text for claim in decision.claims] == [
        "Securitization contributed to the 2008 financial crisis.",
        "Deregulation of the OTC derivatives market contributed to the 2008 financial crisis.",
    ]


@pytest.mark.asyncio
async def test_simple_synthesizer_keeps_distinct_mechanism_claims_after_normalization() -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        json.dumps(
            {
                "claims": [
                    {
                        "text": (
                            "Securitization of subprime mortgages contributed to the "
                            "2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_1"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "The repeal of Glass-Steagall Act contributed to the "
                            "financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_2"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "The deregulated OTC derivatives market posed dangers to "
                            "the financial system."
                        ),
                        "supporting_evidence_ids": ["evidence_3"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                ],
                "information_gaps": [],
                "conflicts": [],
            }
        )
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)

    decision = await synthesizer.deliberate(
        [
            _evidence(
                "evidence_1",
                "Securitization pooled loans into securities sold to investors.",
            ),
            _evidence(
                "evidence_2",
                "Glass-Steagall Act: Did Its Repeal Cause the Financial Crisis?",
            ),
            _evidence(
                "evidence_3",
                "The deregulated OTC derivatives market posed dangers to the financial system.",
            ),
        ],
        context=_context(goal="What were the main causes of the 2008 financial crisis?"),
    )

    assert [claim.text for claim in decision.claims] == [
        "Securitization contributed to the 2008 financial crisis.",
        "The repeal of Glass-Steagall Act contributed to the 2008 financial crisis.",
        "Deregulation of the OTC derivatives market contributed to the 2008 financial crisis.",
    ]


@pytest.mark.asyncio
async def test_simple_synthesizer_caps_final_selection_after_wider_candidate_generation() -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        """
        {
          "claims": [
            {
              "text": "Claim one has enough detail to validate.",
              "supporting_evidence_ids": ["evidence_1"],
              "contradicting_evidence_ids": [],
              "epistemic_status": "moderate_confidence"
            },
            {
              "text": "Claim two has enough detail to validate.",
              "supporting_evidence_ids": ["evidence_2"],
              "contradicting_evidence_ids": [],
              "epistemic_status": "moderate_confidence"
            },
            {
              "text": "Claim three has enough detail to validate.",
              "supporting_evidence_ids": ["evidence_3"],
              "contradicting_evidence_ids": [],
              "epistemic_status": "moderate_confidence"
            },
            {
              "text": "Claim four has enough detail to validate.",
              "supporting_evidence_ids": ["evidence_4"],
              "contradicting_evidence_ids": [],
              "epistemic_status": "moderate_confidence"
            }
          ],
          "information_gaps": [],
          "conflicts": []
        }
        """
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)

    result = await synthesizer.deliberate_result(
        [
            _evidence("evidence_1", "First evidence."),
            _evidence("evidence_2", "Second evidence."),
            _evidence("evidence_3", "Third evidence."),
            _evidence("evidence_4", "Fourth evidence."),
        ],
        context="plan_123",
    )

    assert result.is_ok
    decision = result.unwrap()
    assert len(decision.claims) == 3


@pytest.mark.asyncio
async def test_simple_synthesizer_uses_mechanism_bundles_for_thin_2008_generation() -> None:
    settings = load_settings(CONFIG_DIR)

    class BundleAwareLLMClient:
        def __init__(self) -> None:
            self.requests: list[LLMGenerationRequest] = []

        async def generate(self, request: LLMGenerationRequest) -> LLMGenerationResponse:
            self.requests.append(request)
            prompt = request.messages[1].content
            has_expected_bundles = all(
                label in prompt
                for label in [
                    "Securitization and mortgage-backed lending",
                    "OTC derivatives and deregulation",
                    "Monetary policy and low interest rates",
                ]
            ) and '"evidence_ids": ["evidence_1", "evidence_2"]' in prompt

            claims = (
                [
                    {
                        "text": "Securitization contributed to the 2008 financial crisis.",
                        "supporting_evidence_ids": ["evidence_1", "evidence_2"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "Deregulation of the OTC derivatives market contributed to "
                            "the 2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_3"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": "Monetary policy contributed to the 2008 financial crisis.",
                        "supporting_evidence_ids": ["evidence_4"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                ]
                if has_expected_bundles
                else [
                    {
                        "text": "Securitization contributed to the 2008 financial crisis.",
                        "supporting_evidence_ids": ["evidence_1"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "Deregulation of the OTC derivatives market contributed to "
                            "the 2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_3"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                ]
            )
            return LLMGenerationResponse(
                model=request.model,
                output_text=json.dumps(
                    {
                        "claims": claims,
                        "information_gaps": [],
                        "conflicts": [],
                    }
                ),
                usage=TokenUsage(input_tokens=40, output_tokens=60),
            )

    llm_client = BundleAwareLLMClient()
    synthesizer = SimpleSynthesizer(llm_client, settings)
    context = _context(goal="What were the main causes of the 2008 financial crisis?")
    evidence = [
        _evidence(
            "evidence_1",
            "Securitization pooled loans into securities sold to investors before 2008.",
        ),
        _evidence(
            "evidence_2",
            "Subprime mortgage-backed securities destabilized banks during the crisis.",
        ),
        _evidence(
            "evidence_3",
            "Deregulation of the OTC derivatives market increased leverage before 2008.",
        ),
        _evidence(
            "evidence_4",
            "Monetary policy kept interest rates low and encouraged risk-taking before 2008.",
        ),
    ]

    candidate_set = await synthesizer.generate_candidate_claims(evidence, context=context)

    claim_texts = {claim.text for claim in candidate_set.claims}

    assert "Securitization contributed to the 2008 financial crisis." in claim_texts
    assert (
        "Deregulation of the OTC derivatives market contributed to the 2008 financial crisis."
        in claim_texts
    )
    assert "Monetary policy contributed to the 2008 financial crisis." in claim_texts
    assert len(candidate_set.claims) >= 3

    prompt = llm_client.requests[0].messages[1].content
    assert "Evidence Bundles:" in prompt
    assert "Securitization and mortgage-backed lending" in prompt
    assert "OTC derivatives and deregulation" in prompt
    assert "Monetary policy and low interest rates" in prompt
    assert '"evidence_ids": ["evidence_1", "evidence_2"]' in prompt or (
        '"evidence_ids": ["evidence_2", "evidence_1"]' in prompt
    )


@pytest.mark.asyncio
async def test_simple_synthesizer_deliberate_keeps_healthy_2008_bundled_mechanisms() -> None:
    settings = load_settings(CONFIG_DIR)

    class BundleAwareEndToEndLLMClient:
        def __init__(self) -> None:
            self.requests: list[LLMGenerationRequest] = []

        async def generate(self, request: LLMGenerationRequest) -> LLMGenerationResponse:
            self.requests.append(request)
            prompt = request.messages[1].content
            has_expected_bundles = all(
                label in prompt
                for label in [
                    "Securitization and mortgage-backed lending",
                    "OTC derivatives and deregulation",
                    "Monetary policy and low interest rates",
                ]
            ) and (
                '"evidence_ids": ["evidence_1", "evidence_2"]' in prompt
                or '"evidence_ids": ["evidence_2", "evidence_1"]' in prompt
            )

            claims = (
                [
                    {
                        "text": "Securitization contributed to the 2008 financial crisis.",
                        "supporting_evidence_ids": ["evidence_1", "evidence_2"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "Financial deregulation contributed to the 2008 "
                            "financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_3"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "low_confidence",
                    },
                    {
                        "text": (
                            "Deregulation of the OTC derivatives market contributed to "
                            "the 2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_3"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": "Monetary policy contributed to the 2008 financial crisis.",
                        "supporting_evidence_ids": ["evidence_4"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                ]
                if has_expected_bundles
                else [
                    {
                        "text": "Securitization contributed to the 2008 financial crisis.",
                        "supporting_evidence_ids": ["evidence_1"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "Deregulation of the OTC derivatives market contributed to "
                            "the 2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_3"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                ]
            )
            return LLMGenerationResponse(
                model=request.model,
                output_text=json.dumps(
                    {
                        "synthesis": (
                            "Bundled mechanism slices recover securitization, OTC "
                            "derivatives, and monetary policy."
                        ),
                        "claims": claims,
                        "information_gaps": [],
                        "conflicts": [],
                    }
                ),
                usage=TokenUsage(input_tokens=50, output_tokens=80),
            )

    llm_client = BundleAwareEndToEndLLMClient()
    synthesizer = SimpleSynthesizer(llm_client, settings)
    context = _context(goal="What were the main causes of the 2008 financial crisis?")
    evidence = [
        _evidence(
            "evidence_1",
            "Securitization pooled loans into securities sold to investors before 2008.",
        ),
        _evidence(
            "evidence_2",
            "Subprime mortgage-backed securities destabilized banks during the crisis.",
        ),
        _evidence(
            "evidence_3",
            "Deregulation of the OTC derivatives market increased leverage before 2008.",
        ),
        _evidence(
            "evidence_4",
            "Monetary policy kept interest rates low and encouraged risk-taking before 2008.",
        ),
    ]

    decision = await synthesizer.deliberate(evidence, context=context)

    claim_texts = {claim.text for claim in decision.claims}

    assert decision.plan_id == "plan_123"
    assert decision.decision_id.startswith("decision_")
    assert len(decision.claims) == 3
    assert "Securitization contributed to the 2008 financial crisis." in claim_texts
    assert (
        "Deregulation of the OTC derivatives market contributed to the 2008 financial crisis."
        in claim_texts
    )
    assert "Monetary policy contributed to the 2008 financial crisis." in claim_texts
    assert "Financial deregulation contributed to the 2008 financial crisis." not in claim_texts
    assert all(claim.claim_id.startswith("claim_") for claim in decision.claims)
    assert all(
        evidence_id in {"evidence_1", "evidence_2", "evidence_3", "evidence_4"}
        for claim in decision.claims
        for evidence_id in claim.supporting_evidence_ids
    )

    prompt = llm_client.requests[0].messages[1].content
    assert "Evidence Bundles:" in prompt
    assert "Securitization and mortgage-backed lending" in prompt
    assert "OTC derivatives and deregulation" in prompt
    assert "Monetary policy and low interest rates" in prompt


@pytest.mark.asyncio
async def test_simple_synthesizer_deliberate_keeps_healthy_2008_sketch_first_mechanisms() -> None:
    settings = load_settings(CONFIG_DIR)

    class SketchAwareEndToEndLLMClient:
        def __init__(self) -> None:
            self.requests: list[LLMGenerationRequest] = []

        async def generate(self, request: LLMGenerationRequest) -> LLMGenerationResponse:
            self.requests.append(request)
            prompt = request.messages[1].content
            has_expected_sketches = all(
                marker in prompt
                for marker in [
                    '"sketch_id": "sketch_securitization"',
                    '"sketch_id": "sketch_otc_derivatives"',
                    '"sketch_id": "sketch_monetary_policy"',
                    "Securitization and mortgage-backed lending:",
                    "OTC derivatives and deregulation:",
                    "Monetary policy and low interest rates:",
                ]
            ) and (
                '"evidence_ids": ["evidence_1", "evidence_2"]' in prompt
                or '"evidence_ids": ["evidence_2", "evidence_1"]' in prompt
            )

            claims = (
                [
                    {
                        "text": (
                            "Mortgage-backed securities contributed to the "
                            "2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_1", "evidence_2"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "Financial deregulation contributed to the "
                            "2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_3"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "low_confidence",
                    },
                    {
                        "text": (
                            "Deregulation of the OTC derivatives market contributed to "
                            "the 2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_3"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": "Monetary policy contributed to the 2008 financial crisis.",
                        "supporting_evidence_ids": ["evidence_4"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                ]
                if has_expected_sketches
                else [
                    {
                        "text": (
                            "Mortgage-backed securities contributed to the "
                            "2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_1"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "Deregulation of the OTC derivatives market contributed to "
                            "the 2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_3"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                ]
            )
            return LLMGenerationResponse(
                model=request.model,
                output_text=json.dumps(
                    {
                        "synthesis": (
                            "Sketch-first deliberation preserves mortgage-backed "
                            "securities, OTC derivatives, and monetary policy."
                        ),
                        "claims": claims,
                        "information_gaps": [],
                        "conflicts": [],
                    }
                ),
                usage=TokenUsage(input_tokens=50, output_tokens=80),
            )

    llm_client = SketchAwareEndToEndLLMClient()
    synthesizer = SimpleSynthesizer(llm_client, settings)
    context = _context(goal="What were the main causes of the 2008 financial crisis?")
    evidence = [
        _evidence(
            "evidence_1",
            "Securitization pooled loans into securities sold to investors before 2008.",
        ),
        _evidence(
            "evidence_2",
            "Subprime mortgage-backed securities destabilized banks during the crisis.",
        ),
        _evidence(
            "evidence_3",
            "Deregulation of the OTC derivatives market increased leverage before 2008.",
        ),
        _evidence(
            "evidence_4",
            "Monetary policy kept interest rates low and encouraged risk-taking before 2008.",
        ),
    ]

    decision = await synthesizer.deliberate(evidence, context=context)

    claim_texts = {claim.text for claim in decision.claims}

    assert decision.plan_id == "plan_123"
    assert decision.decision_id.startswith("decision_")
    assert len(decision.claims) == 3
    assert (
        "Mortgage-backed securities contributed to the 2008 financial crisis."
        in claim_texts
    )
    assert (
        "Deregulation of the OTC derivatives market contributed to the 2008 financial crisis."
        in claim_texts
    )
    assert "Monetary policy contributed to the 2008 financial crisis." in claim_texts
    assert "Financial deregulation contributed to the 2008 financial crisis." not in claim_texts
    assert all(claim.claim_id.startswith("claim_") for claim in decision.claims)
    assert all(
        claim.text.lower().endswith("the 2008 financial crisis.")
        for claim in decision.claims
    )
    assert all(
        evidence_id in {"evidence_1", "evidence_2", "evidence_3", "evidence_4"}
        for claim in decision.claims
        for evidence_id in claim.supporting_evidence_ids
    )

    prompt = llm_client.requests[0].messages[1].content
    assert "Evidence Bundles:" in prompt
    assert '"sketch_id": "sketch_securitization"' in prompt
    assert '"sketch_id": "sketch_otc_derivatives"' in prompt
    assert '"sketch_id": "sketch_monetary_policy"' in prompt
    assert "Securitization and mortgage-backed lending:" in prompt
    assert "OTC derivatives and deregulation:" in prompt
    assert "Monetary policy and low interest rates:" in prompt


@pytest.mark.asyncio
async def test_simple_synthesizer_deliberate_keeps_healthy_2008_slot_grounded_mechanisms(
) -> None:
    settings = load_settings(CONFIG_DIR)

    class SlotAwareEndToEndLLMClient:
        def __init__(self) -> None:
            self.requests: list[LLMGenerationRequest] = []

        async def generate(self, request: LLMGenerationRequest) -> LLMGenerationResponse:
            self.requests.append(request)
            prompt = request.messages[1].content
            has_expected_slots = all(
                marker in prompt
                for marker in [
                    '"slot_id": "slot_securitization"',
                    '"slot_id": "slot_otc_derivatives"',
                    '"slot_id": "slot_monetary_policy"',
                    '"target_event_anchor": "the 2008 financial crisis"',
                    "Securitization and mortgage-backed lending",
                    "OTC derivatives and deregulation",
                    "Monetary policy and low interest rates",
                ]
            ) and (
                '"evidence_ids": ["evidence_1", "evidence_2"]' in prompt
                or '"evidence_ids": ["evidence_2", "evidence_1"]' in prompt
            )

            claims = (
                [
                    {
                        "text": (
                            "Mortgage-backed securities contributed to the "
                            "2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_1", "evidence_2"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "Financial deregulation contributed to the "
                            "2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_3"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "low_confidence",
                    },
                    {
                        "text": (
                            "Deregulation of the OTC derivatives market contributed to "
                            "the 2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_3"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": "Monetary policy contributed to the 2008 financial crisis.",
                        "supporting_evidence_ids": ["evidence_4"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                ]
                if has_expected_slots
                else [
                    {
                        "text": (
                            "Mortgage-backed securities contributed to the "
                            "2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_1"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "Deregulation of the OTC derivatives market contributed to "
                            "the 2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_3"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                ]
            )
            return LLMGenerationResponse(
                model=request.model,
                output_text=json.dumps(
                    {
                        "synthesis": (
                            "Slot-grounded deliberation preserves mortgage-backed "
                            "securities, OTC derivatives, and monetary policy."
                        ),
                        "claims": claims,
                        "information_gaps": [],
                        "conflicts": [],
                    }
                ),
                usage=TokenUsage(input_tokens=50, output_tokens=80),
            )

    llm_client = SlotAwareEndToEndLLMClient()
    synthesizer = SimpleSynthesizer(llm_client, settings)
    context = _context(goal="What were the main causes of the 2008 financial crisis?")
    evidence = [
        _evidence(
            "evidence_1",
            "Securitization pooled loans into securities sold to investors before 2008.",
        ),
        _evidence(
            "evidence_2",
            "Subprime mortgage-backed securities destabilized banks during the crisis.",
        ),
        _evidence(
            "evidence_3",
            "Deregulation of the OTC derivatives market increased leverage before 2008.",
        ),
        _evidence(
            "evidence_4",
            "Monetary policy kept interest rates low and encouraged risk-taking before 2008.",
        ),
    ]

    decision = await synthesizer.deliberate(evidence, context=context)

    claim_texts = {claim.text for claim in decision.claims}

    assert decision.plan_id == "plan_123"
    assert decision.decision_id.startswith("decision_")
    assert len(decision.claims) == 3
    assert (
        "Mortgage-backed securities contributed to the 2008 financial crisis."
        in claim_texts
    )
    assert (
        "Deregulation of the OTC derivatives market contributed to the 2008 financial crisis."
        in claim_texts
    )
    assert "Monetary policy contributed to the 2008 financial crisis." in claim_texts
    assert "Financial deregulation contributed to the 2008 financial crisis." not in claim_texts
    assert all(claim.claim_id.startswith("claim_") for claim in decision.claims)
    assert all(
        claim.text.lower().endswith("the 2008 financial crisis.")
        for claim in decision.claims
    )
    assert all(
        evidence_id in {"evidence_1", "evidence_2", "evidence_3", "evidence_4"}
        for claim in decision.claims
        for evidence_id in claim.supporting_evidence_ids
    )

    prompt = llm_client.requests[0].messages[1].content
    assert "Evidence Bundles:" in prompt
    assert '"slot_id": "slot_securitization"' in prompt
    assert '"slot_id": "slot_otc_derivatives"' in prompt
    assert '"slot_id": "slot_monetary_policy"' in prompt
    assert '"target_event_anchor": "the 2008 financial crisis"' in prompt
    assert '"sketch_id": "sketch_securitization"' in prompt
    assert '"sketch_id": "sketch_otc_derivatives"' in prompt
    assert '"sketch_id": "sketch_monetary_policy"' in prompt


@pytest.mark.asyncio
async def test_simple_synthesizer_deliberate_keeps_healthy_2008_slate_grounded_mechanisms(
) -> None:
    settings = load_settings(CONFIG_DIR)

    class SlateAwareEndToEndLLMClient:
        def __init__(self) -> None:
            self.requests: list[LLMGenerationRequest] = []

        async def generate(self, request: LLMGenerationRequest) -> LLMGenerationResponse:
            self.requests.append(request)
            prompt = request.messages[1].content
            has_expected_slate = all(
                marker in prompt
                for marker in [
                    '"slate_entry_id": "slate_entry_securitization"',
                    '"slate_entry_id": "slate_entry_otc_derivatives"',
                    '"slate_entry_id": "slate_entry_monetary_policy"',
                    '"distinct_family_count": 3',
                    '"family_duplication_count": 0',
                    '"target_event_anchor": "the 2008 financial crisis"',
                ]
            ) and (
                '"evidence_ids": ["evidence_1", "evidence_2"]' in prompt
                or '"evidence_ids": ["evidence_2", "evidence_1"]' in prompt
            )

            claims = (
                [
                    {
                        "text": (
                            "Mortgage-backed lending contributed to the "
                            "2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_1", "evidence_2"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "Deregulation of the OTC derivatives market contributed to "
                            "the 2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_3"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": "Monetary policy contributed to the 2008 financial crisis.",
                        "supporting_evidence_ids": ["evidence_4"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                ]
                if has_expected_slate
                else [
                    {
                        "text": "Securitization contributed to the 2008 financial crisis.",
                        "supporting_evidence_ids": ["evidence_1"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "Mortgage-backed lending contributed to the "
                            "2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_2"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                    {
                        "text": (
                            "Deregulation of the OTC derivatives market contributed to "
                            "the 2008 financial crisis."
                        ),
                        "supporting_evidence_ids": ["evidence_3"],
                        "contradicting_evidence_ids": [],
                        "epistemic_status": "moderate_confidence",
                    },
                ]
            )
            return LLMGenerationResponse(
                model=request.model,
                output_text=json.dumps(
                    {
                        "synthesis": (
                            "Slate-grounded deliberation preserves one housing-finance "
                            "family plus OTC derivatives and monetary policy."
                        ),
                        "claims": claims,
                        "information_gaps": [],
                        "conflicts": [],
                    }
                ),
                usage=TokenUsage(input_tokens=50, output_tokens=80),
            )

    llm_client = SlateAwareEndToEndLLMClient()
    synthesizer = SimpleSynthesizer(llm_client, settings)
    context = _context(goal="What were the main causes of the 2008 financial crisis?")
    evidence = [
        _evidence(
            "evidence_1",
            "Securitization pooled loans into securities sold to investors before 2008.",
        ),
        _evidence(
            "evidence_2",
            "Subprime mortgage-backed securities destabilized banks during the crisis.",
        ),
        _evidence(
            "evidence_3",
            "Deregulation of the OTC derivatives market increased leverage before 2008.",
        ),
        _evidence(
            "evidence_4",
            "Monetary policy kept interest rates low and encouraged risk-taking before 2008.",
        ),
    ]

    decision = await synthesizer.deliberate(evidence, context=context)

    claim_texts = {claim.text for claim in decision.claims}
    housing_family_claims = {
        claim.text
        for claim in decision.claims
        if "mortgage" in claim.text.lower() or "securitization" in claim.text.lower()
    }

    assert decision.plan_id == "plan_123"
    assert decision.decision_id.startswith("decision_")
    assert len(decision.claims) == 3
    assert (
        "Deregulation of the OTC derivatives market contributed to the 2008 financial crisis."
        in claim_texts
    )
    assert "Monetary policy contributed to the 2008 financial crisis." in claim_texts
    assert housing_family_claims == {
        "Mortgage-backed securities contributed to the 2008 financial crisis."
    } or housing_family_claims == {
        "Mortgage-backed lending contributed to the 2008 financial crisis."
    }
    assert "Securitization contributed to the 2008 financial crisis." not in claim_texts
    assert all(claim.claim_id.startswith("claim_") for claim in decision.claims)
    assert all(
        claim.text.lower().endswith("the 2008 financial crisis.")
        for claim in decision.claims
    )
    assert all(
        evidence_id in {"evidence_1", "evidence_2", "evidence_3", "evidence_4"}
        for claim in decision.claims
        for evidence_id in claim.supporting_evidence_ids
    )
    assert len(housing_family_claims) == 1

    prompt = llm_client.requests[0].messages[1].content
    assert "Evidence Bundles:" in prompt
    assert '"slate_id": "slate_' in prompt
    assert '"slate_entry_id": "slate_entry_securitization"' in prompt
    assert '"slate_entry_id": "slate_entry_otc_derivatives"' in prompt
    assert '"slate_entry_id": "slate_entry_monetary_policy"' in prompt
    assert '"distinct_family_count": 3' in prompt
    assert '"family_duplication_count": 0' in prompt
    assert '"slot_id": "slot_securitization"' in prompt
    assert '"slot_id": "slot_otc_derivatives"' in prompt
    assert '"slot_id": "slot_monetary_policy"' in prompt
    assert '"sketch_id": "sketch_securitization"' in prompt
    assert '"sketch_id": "sketch_otc_derivatives"' in prompt
    assert '"sketch_id": "sketch_monetary_policy"' in prompt


@pytest.mark.asyncio
async def test_simple_synthesizer_malformed_output_returns_typed_failure() -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient("not-json")
    synthesizer = SimpleSynthesizer(llm_client, settings)

    result = await synthesizer.deliberate_result(
        [_evidence("evidence_1", "One piece of evidence.")],
        context="plan_123",
    )

    assert result.is_error
    assert result.error is not None
    assert result.error.code == "deliberation_response_invalid"
    assert result.error.details["trace_id"].startswith("trace_")


@pytest.mark.asyncio
async def test_simple_synthesizer_unknown_evidence_ids_fail_fast() -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        """
        {
          "claims": [
            {
              "text": "An unsupported claim references missing evidence.",
              "supporting_evidence_ids": ["evidence_missing"],
              "contradicting_evidence_ids": [],
              "epistemic_status": "low_confidence"
            }
          ],
          "information_gaps": [],
          "conflicts": []
        }
        """
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)

    with pytest.raises(DeliberationError):
        await synthesizer.deliberate(
            [_evidence("evidence_1", "One piece of evidence.")],
            context="plan_123",
        )


@pytest.mark.asyncio
async def test_simple_synthesizer_claims_reference_only_provided_evidence() -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        """
        {
          "claims": [
            {
              "text": "The evidence set supports the first claim.",
              "supporting_evidence_ids": ["evidence_1", "evidence_2"],
              "contradicting_evidence_ids": [],
              "epistemic_status": "moderate_confidence"
            }
          ],
          "information_gaps": [],
          "conflicts": []
        }
        """
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)

    decision = await synthesizer.deliberate(
        [
            _evidence("evidence_1", "First evidence."),
            _evidence("evidence_2", "Second evidence."),
        ],
        context="plan_123",
    )

    known_ids = {"evidence_1", "evidence_2"}
    assert set(decision.claims[0].supporting_evidence_ids).issubset(known_ids)
    assert set(decision.claims[0].contradicting_evidence_ids).issubset(known_ids)


@pytest.mark.asyncio
async def test_simple_synthesizer_uses_shared_ids_and_metadata_consistently() -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        """
        {
          "claims": [
            {
              "text": "Evidence one supports a stable trend.",
              "supporting_evidence_ids": ["evidence_1"],
              "contradicting_evidence_ids": [],
              "epistemic_status": "moderate_confidence"
            }
          ],
          "information_gaps": [],
          "conflicts": []
        }
        """
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)

    decision = await synthesizer.deliberate(
        [_evidence("evidence_1", "First evidence.")],
        context='{"plan_id":"plan_123","goal":"Test goal"}',
    )
    request = llm_client.requests[0]

    assert request.metadata["component"] == "deliberation"
    assert request.metadata["plan_id"] == "plan_123"
    assert request.metadata["trace_id"].startswith("trace_")
    assert request.messages[0] == LLMMessage(
        role=MessageRole.SYSTEM,
        content=(
            "You are ASAR's v0 synthesizer. Produce compact JSON only. "
            "Use the evidence set as the only source of truth."
        ),
    )
    assert decision.decision_id.startswith("decision_")
    assert all(claim.claim_id.startswith("claim_") for claim in decision.claims)


@pytest.mark.asyncio
async def test_simple_synthesizer_truncates_evidence_payload_for_prompt_compactness() -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        """
        {
          "claims": [
            {
              "text": "Evidence one supports a stable trend.",
              "supporting_evidence_ids": ["evidence_1"],
              "contradicting_evidence_ids": [],
              "epistemic_status": "moderate_confidence"
            }
          ],
          "information_gaps": [],
          "conflicts": []
        }
        """
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)

    long_content = "A" * 600
    await synthesizer.deliberate(
        [
            _evidence("evidence_1", long_content),
        ],
        context="plan_123",
    )

    request = llm_client.requests[0]
    assert "A" * 320 not in request.messages[1].content


@pytest.mark.asyncio
async def test_simple_synthesizer_builds_schema_valid_conflicts() -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        """
        {
          "claims": [
            {
              "text": "Evidence one suggests rapid adoption.",
              "supporting_evidence_ids": ["evidence_1"],
              "contradicting_evidence_ids": [],
              "epistemic_status": "moderate_confidence"
            },
            {
              "text": "Evidence two suggests adoption remained uneven.",
              "supporting_evidence_ids": ["evidence_2"],
              "contradicting_evidence_ids": [],
              "epistemic_status": "contested"
            }
          ],
          "information_gaps": [],
          "conflicts": [
            {
              "claim_indexes": [1, 2],
              "description": "The evidence points to different regional outcomes.",
              "resolution": "Keep both claims and flag the disagreement."
            }
          ]
        }
        """
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)

    decision = await synthesizer.deliberate(
        [
            _evidence("evidence_1", "First evidence."),
            _evidence("evidence_2", "Second evidence."),
        ],
        context="plan_123",
    )

    assert len(decision.conflicts) == 1
    assert decision.conflicts[0].conflict_id.startswith("conflict_")
    assert len(decision.conflicts[0].claim_ids) == 2


@pytest.mark.asyncio
async def test_simple_synthesizer_uses_utc_timestamps_and_schema_valid_packet() -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient(
        """
        {
          "claims": [
            {
              "text": "Evidence one supports the only claim.",
              "supporting_evidence_ids": ["evidence_1"],
              "contradicting_evidence_ids": [],
              "epistemic_status": "high_confidence"
            }
          ],
          "information_gaps": [],
          "conflicts": []
        }
        """
    )
    synthesizer = SimpleSynthesizer(llm_client, settings)

    decision = await synthesizer.deliberate(
        [_evidence("evidence_1", "First evidence.")],
        context="plan_123",
    )

    assert decision.created_at.utcoffset() is not None
    assert decision.claims[0].supporting_evidence_ids == ["evidence_1"]


@pytest.mark.asyncio
async def test_simple_synthesizer_empty_evidence_is_explicit_failure() -> None:
    settings = load_settings(CONFIG_DIR)
    llm_client = StubLLMClient('{"claims":[],"information_gaps":[],"conflicts":[]}')
    synthesizer = SimpleSynthesizer(llm_client, settings)

    result = await synthesizer.deliberate_result([], context="plan_123")

    assert result.is_error
    assert result.error is not None
    assert result.error.code == "deliberation_empty_evidence"


@pytest.mark.asyncio
async def test_simple_synthesizer_wraps_llm_failures() -> None:
    settings = load_settings(CONFIG_DIR)

    class BrokenLLMClient:
        async def generate(self, request: LLMGenerationRequest) -> LLMGenerationResponse:
            raise LLMClientError("provider timeout", retryable=True)

    synthesizer = SimpleSynthesizer(BrokenLLMClient(), settings)

    result = await synthesizer.deliberate_result(
        [_evidence("evidence_1", "First evidence.")],
        context="plan_123",
    )

    assert result.is_error
    assert result.error is not None
    assert result.error.code == "deliberation_llm_error"
    assert result.error.retryable is True

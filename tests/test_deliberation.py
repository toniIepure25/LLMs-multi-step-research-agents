"""
Unit tests for the v0 `SimpleSynthesizer`.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from asar.common import load_settings, setup_logging
from asar.core.errors import DeliberationError, LLMClientError
from asar.core.llm import LLMGenerationRequest, LLMGenerationResponse, LLMMessage, MessageRole, TokenUsage
from asar.deliberation import SimpleSynthesizer
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
        content="You are ASAR's v0 synthesizer. Produce compact JSON only. Use the evidence set as the only source of truth.",
    )
    assert decision.decision_id.startswith("decision_")
    assert all(claim.claim_id.startswith("claim_") for claim in decision.claims)


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

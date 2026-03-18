"""
Minimal v0 synthesizer backed by a typed LLM abstraction.
"""

from __future__ import annotations

import json

from pydantic import BaseModel, Field, ValidationError

from asar.common import ASARSettings, IDPrefix, generate_id, generate_trace_id, get_logger, setup_logging
from asar.core.errors import DeliberationError, LLMClientError
from asar.core.llm import LLMClientProtocol, LLMGenerationRequest, LLMGenerationResponse, LLMMessage, MessageRole
from asar.core.result import OperationResult
from schemas.decision_packet import Claim, Conflict, DecisionPacket, EpistemicStatus
from schemas.evidence_item import EvidenceItem


class _ContextPayload(BaseModel):
    """Minimal deliberation context extracted from the protocol string."""

    plan_id: str = Field(..., min_length=1)
    goal: str | None = None


class _ClaimDraft(BaseModel):
    """Structured claim draft expected from the LLM."""

    text: str = Field(..., min_length=10)
    supporting_evidence_ids: list[str] = Field(..., min_length=1)
    contradicting_evidence_ids: list[str] = Field(default_factory=list)
    epistemic_status: EpistemicStatus = Field(default=EpistemicStatus.UNKNOWN)
    reasoning_trace: str | None = None


class _ConflictDraft(BaseModel):
    """Minimal conflict draft expected from the LLM."""

    claim_indexes: list[int] = Field(..., min_length=2)
    description: str = Field(..., min_length=5)
    resolution: str | None = None


class _SynthesizerResponse(BaseModel):
    """Structured synthesizer response expected from the LLM."""

    synthesis: str | None = None
    claims: list[_ClaimDraft] = Field(..., min_length=1, max_length=4)
    information_gaps: list[str] = Field(default_factory=list)
    conflicts: list[_ConflictDraft] = Field(default_factory=list)


class SimpleSynthesizer:
    """Generate one v0 `DecisionPacket` from a small evidence set."""

    def __init__(self, llm_client: LLMClientProtocol, settings: ASARSettings) -> None:
        self._llm_client = llm_client
        self._settings = settings
        setup_logging(settings.pipeline.logging)
        self._base_logger_name = "asar.deliberation.simple_synthesizer"

    async def deliberate(
        self,
        evidence: list[EvidenceItem],
        context: str | None = None,
    ) -> DecisionPacket:
        """Generate a valid v0 decision packet or raise a typed deliberation error."""

        result = await self.deliberate_result(evidence, context=context)
        if result.is_error and result.error is not None:
            raise DeliberationError(
                result.error.message,
                details=result.error.details,
                retryable=result.error.retryable,
            )
        return result.unwrap()

    async def deliberate_result(
        self,
        evidence: list[EvidenceItem],
        context: str | None = None,
    ) -> OperationResult[DecisionPacket]:
        """Generate a decision packet while keeping failure paths inspectable."""

        if not evidence:
            return OperationResult.fail(
                "deliberation_empty_evidence",
                "Deliberation requires at least one EvidenceItem",
            )

        try:
            context_payload = self._parse_context(context)
            evidence_payload = self._serialize_evidence(evidence)
        except DeliberationError as exc:
            return OperationResult.fail(
                "deliberation_invalid_input",
                exc.message,
                details=exc.details,
            )

        trace_id = generate_trace_id()
        logger = get_logger(self._base_logger_name, trace_id=trace_id)
        model_settings = self._settings.models.route_for("deliberation")
        request = self._build_request(
            evidence_payload=evidence_payload,
            context_payload=context_payload,
            model=model_settings.model,
            temperature=model_settings.temperature,
            max_tokens=model_settings.max_tokens,
            trace_id=trace_id,
        )

        logger.info("Generating v0 decision packet")
        try:
            response = await self._llm_client.generate(request)
        except Exception as exc:
            return OperationResult.fail(
                "deliberation_llm_error",
                "Deliberation LLM call failed",
                retryable=isinstance(exc, LLMClientError),
                details={
                    "plan_id": context_payload.plan_id,
                    "trace_id": trace_id,
                    "error": str(exc),
                },
            )

        try:
            parsed = self._parse_response(response)
            decision = self._build_decision_packet(
                parsed=parsed,
                context_payload=context_payload,
                known_evidence_ids={item.evidence_id for item in evidence},
            )
        except DeliberationError as exc:
            logger.error("Synthesizer response validation failed")
            return OperationResult.fail(
                "deliberation_response_invalid",
                exc.message,
                details={**exc.details, "trace_id": trace_id},
            )

        logger.info("Decision packet generated")
        return OperationResult.ok(decision)

    def _parse_context(self, context: str | None) -> _ContextPayload:
        if context is None or not context.strip():
            raise DeliberationError(
                "Deliberation context must include a plan_id",
                details={"context": context},
            )

        stripped = context.strip()
        if stripped.startswith("{"):
            try:
                decoded = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise DeliberationError(
                    "Deliberation context JSON was invalid",
                    details={"context": context},
                ) from exc
            try:
                return _ContextPayload.model_validate(decoded)
            except ValidationError as exc:
                raise DeliberationError(
                    "Deliberation context did not include a valid plan_id",
                    details={"errors": exc.errors()},
                ) from exc

        return _ContextPayload(plan_id=stripped)

    def _serialize_evidence(self, evidence: list[EvidenceItem]) -> list[dict[str, str]]:
        seen_ids: set[str] = set()
        payload: list[dict[str, str]] = []

        for item in evidence:
            if item.evidence_id in seen_ids:
                raise DeliberationError(
                    "Evidence IDs must be unique for deliberation",
                    details={"evidence_id": item.evidence_id},
                )
            seen_ids.add(item.evidence_id)
            payload.append(
                {
                    "evidence_id": item.evidence_id,
                    "content": item.content,
                    "title": item.source.title or "",
                    "url": item.source.url or "",
                }
            )

        return payload

    def _build_request(
        self,
        *,
        evidence_payload: list[dict[str, str]],
        context_payload: _ContextPayload,
        model: str,
        temperature: float,
        max_tokens: int,
        trace_id: str,
    ) -> LLMGenerationRequest:
        prompt = (
            "Synthesize grounded claims from the evidence below.\n"
            "Return JSON only with this shape:\n"
            '{"synthesis":"...","claims":[{"text":"...","supporting_evidence_ids":["evidence_..."],'
            '"contradicting_evidence_ids":[],"epistemic_status":"moderate_confidence","reasoning_trace":"..."}],'
            '"information_gaps":["..."],"conflicts":[{"claim_indexes":[1,2],"description":"...","resolution":"..."}]}\n'
            "Requirements:\n"
            "- use only the provided evidence IDs\n"
            "- produce 1 to 4 grounded claims\n"
            "- keep synthesis single-pass and concise\n"
            "- do not verify truth or invent citations\n"
            f"Plan ID: {context_payload.plan_id}\n"
            f"Goal: {context_payload.goal or 'unknown'}\n"
            f"Evidence: {json.dumps(evidence_payload, sort_keys=True)}"
        )

        return LLMGenerationRequest(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                LLMMessage(
                    role=MessageRole.SYSTEM,
                    content=(
                        "You are ASAR's v0 synthesizer. Produce compact JSON only. "
                        "Use the evidence set as the only source of truth."
                    ),
                ),
                LLMMessage(role=MessageRole.USER, content=prompt),
            ],
            metadata={
                "component": "deliberation",
                "trace_id": trace_id,
                "plan_id": context_payload.plan_id,
            },
        )

    def _parse_response(self, response: LLMGenerationResponse) -> _SynthesizerResponse:
        raw_payload = _strip_code_fences(response.output_text)
        try:
            decoded = json.loads(raw_payload)
        except json.JSONDecodeError as exc:
            raise DeliberationError(
                "Synthesizer response was not valid JSON",
                details={"response": response.output_text},
            ) from exc

        try:
            return _SynthesizerResponse.model_validate(decoded)
        except ValidationError as exc:
            raise DeliberationError(
                "Synthesizer response did not match the expected schema",
                details={"response": decoded, "errors": exc.errors()},
            ) from exc

    def _build_decision_packet(
        self,
        *,
        parsed: _SynthesizerResponse,
        context_payload: _ContextPayload,
        known_evidence_ids: set[str],
    ) -> DecisionPacket:
        claims: list[Claim] = []

        for draft in parsed.claims:
            referenced_ids = set(draft.supporting_evidence_ids) | set(draft.contradicting_evidence_ids)
            unknown_ids = sorted(referenced_ids - known_evidence_ids)
            if unknown_ids:
                raise DeliberationError(
                    "Synthesizer referenced unknown evidence IDs",
                    details={"unknown_evidence_ids": unknown_ids},
                )

            claims.append(
                Claim(
                    claim_id=generate_id(IDPrefix.CLAIM),
                    text=draft.text.strip(),
                    epistemic_status=draft.epistemic_status,
                    supporting_evidence_ids=draft.supporting_evidence_ids,
                    contradicting_evidence_ids=draft.contradicting_evidence_ids,
                    reasoning_trace=draft.reasoning_trace,
                )
            )

        conflicts: list[Conflict] = []
        for draft in parsed.conflicts:
            claim_ids = []
            for claim_index in draft.claim_indexes:
                if claim_index < 1 or claim_index > len(claims):
                    raise DeliberationError(
                        "Synthesizer conflict indexes must refer to generated claims",
                        details={"claim_indexes": draft.claim_indexes},
                    )
                claim_ids.append(claims[claim_index - 1].claim_id)

            conflicts.append(
                Conflict(
                    conflict_id=generate_id(IDPrefix.CONFLICT),
                    claim_ids=claim_ids,
                    description=draft.description,
                    resolution=draft.resolution,
                )
            )

        try:
            return DecisionPacket(
                decision_id=generate_id(IDPrefix.DECISION),
                plan_id=context_payload.plan_id,
                claims=claims,
                conflicts=conflicts,
                synthesis=parsed.synthesis,
                information_gaps=parsed.information_gaps,
            )
        except ValidationError as exc:
            raise DeliberationError(
                "Synthesizer produced an invalid DecisionPacket",
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

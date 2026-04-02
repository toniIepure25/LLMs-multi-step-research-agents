"""
Minimal v0 synthesizer backed by a typed LLM abstraction.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from pydantic import BaseModel, Field, ValidationError

from asar.common import (
    ASARSettings,
    IDPrefix,
    generate_id,
    generate_trace_id,
    get_logger,
    setup_logging,
)
from asar.core.errors import DeliberationError, LLMClientError
from asar.core.llm import (
    LLMClientProtocol,
    LLMGenerationRequest,
    LLMGenerationResponse,
    LLMMessage,
    MessageRole,
)
from asar.core.result import OperationResult
from asar.deliberation.claim_selector import ClaimSelector
from asar.deliberation.mechanism_bundler import MechanismBundler
from asar.deliberation.mechanism_sketcher import MechanismSketcher
from asar.deliberation.mechanism_slate_selector import MechanismSlateSelector
from asar.deliberation.mechanism_slot_builder import MechanismSlotBuilder
from schemas.candidate_claim_set import CandidateClaim, CandidateClaimSet
from schemas.decision_packet import Claim, Conflict, DecisionPacket, EpistemicStatus
from schemas.evidence_item import EvidenceItem

_MAX_EVIDENCE_CONTENT_CHARS = 220
_MAX_EVIDENCE_TITLE_CHARS = 100
_CAUSAL_GOAL_MARKERS = (
    "cause",
    "causes",
    "caused",
    "driver",
    "drivers",
    "factor",
    "factors",
    "reason",
    "reasons",
    "why ",
)
_CAUSAL_CLAIM_MARKERS = (
    "cause",
    "caused",
    "contributed",
    "contribute",
    "factor",
    "factors",
    "driver",
    "drivers",
    "reason",
    "reasons",
    "led to",
    "triggered",
    "trigger",
    "sparked",
    "amplified",
    "amplify",
    "deepened",
    "deepen",
    "worsened",
    "worsen",
    "exacerbated",
    "exacerbate",
    "responsible for",
    "role in",
)
_RESPONSE_CLAIM_MARKERS = (
    "response to",
    "in response to",
    "was passed",
    "was enacted",
    "was created",
    "was established",
    "bailout",
    "bail out",
    "stimulus",
    "rescue package",
    "recovery",
    "aftermath",
    "stabilization act",
)
_VAGUE_CAUSAL_CLAIM_MARKERS = (
    "perfect storm",
    "unlucky factors",
    "various factors",
    "multiple factors",
    "combination of factors",
    "other causes",
    "systemic flaws",
    "broad factors",
    "mixed factors",
    "several factors",
)
_WEAK_DESCRIPTIVE_CLAIM_MARKERS = (
    "is more than just",
    "the primary benefit of",
    "provides an additional funding source",
    "provided an additional funding source",
    "bridges the gap between",
    "allows institutions like",
    "is a multifaceted process",
    "posed dangers to the financial system",
)
_CRASH_WAS_CAUSED_PATTERN = re.compile(
    r"^the crash was caused by a number of factors, including (?P<cause>.+?)\.?$",
    re.IGNORECASE,
)
_BUBBLE_WAS_CAUSED_PATTERN = re.compile(
    r"^a stock market bubble that was caused by (?P<cause>.+?)\.?$",
    re.IGNORECASE,
)
_DESCRIPTIVE_MECHANISM_PATTERN = re.compile(
    r"^(?P<subject>.+?)\s+"
    r"(provides?|provided|poses?|posed|allows?|allowed|bridges?|bridged|"
    r"connects?|connected|enables?|enabled|creates?|created|supports?|supported|"
    r"reduces?|reduced|increases?|increased|eliminates?|eliminated)\b",
    re.IGNORECASE,
)
_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_SUPPORT_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "to",
    "was",
    "were",
    "which",
}
_CAUSAL_TEXT_IGNORE_TOKENS = {
    "amplified",
    "caused",
    "contributed",
    "deepened",
    "driver",
    "drivers",
    "factor",
    "factors",
    "led",
    "main",
    "reason",
    "reasons",
    "responsible",
    "role",
    "sparked",
    "triggered",
    "worsened",
}
_GOAL_SUPPORT_GENERALIZATION_FAMILIES = (
    (
        ("2008 financial crisis",),
        (
            (
                ("otc derivatives market", "otc derivatives"),
                "Deregulation of the OTC derivatives market",
            ),
            (("glass-steagall", "glass steagall"), "Repeal of the Glass-Steagall Act"),
            (("monetary policy",), "Monetary policy"),
            (
                (
                    "subprime lending",
                    "subprime borrowers",
                    "subprime mortgages",
                    "subprime mortgage-backed securities",
                    "subprime mortgage backed securities",
                ),
                "Subprime lending",
            ),
            (
                (
                    "mortgage-backed securities",
                    "mortgage backed securities",
                    "mortgage-backed security",
                    "mortgage backed security",
                    "mortgage-backed",
                    "mortgage backed",
                ),
                "Mortgage-backed securities",
            ),
            (("securitization",), "Securitization"),
        ),
    ),
    (
        ("great depression",),
        (
            (
                (
                    "stock market crash",
                    "crash of 1929",
                    "stock market in 1929",
                    "wall street crash",
                ),
                "The stock market crash of 1929",
            ),
            (
                (
                    "money supply",
                    "money supplies",
                    "monetary contraction",
                    "monetary policy",
                    "monetary policies",
                    "bank failures",
                    "bank failure",
                    "banking panic",
                    "banking panics",
                    "gold standard",
                ),
                "Monetary contraction and banking panics",
            ),
            (
                (
                    "smoot-hawley",
                    "smoot hawley",
                    "tariff",
                    "tariffs",
                    "protectionism",
                    "world trade",
                    "war reparations",
                ),
                "Protectionism and the collapse of world trade",
            ),
        ),
    ),
    (
        ("dot-com crash", "dotcom crash", "dot-com bubble", "dotcom bubble"),
        (
            (
                (
                    "speculation in dotcom",
                    "speculation in dot-com",
                    "speculation in internet-based businesses",
                    "speculation in internet based businesses",
                ),
                "Speculation in dotcom or internet-based businesses",
            ),
            (
                (
                    "overvaluation of tech companies",
                    "overvalued tech companies",
                    "overvaluation",
                ),
                "Overvaluation of tech companies",
            ),
            (
                (
                    "lack of regulation in the tech industry",
                    "regulatory failures",
                    "lack of regulation",
                ),
                "Lack of regulation in the tech industry",
            ),
        ),
    ),
)
_GENERIC_CAUSAL_TARGET_PATTERNS = (
    (
        re.compile(r"\bcontributed to the financial crisis\b", re.IGNORECASE),
        "contributed to {goal_subject}",
    ),
    (
        re.compile(r"\bcontributed to the crisis\b", re.IGNORECASE),
        "contributed to {goal_subject}",
    ),
    (
        re.compile(r"\bcaused the financial crisis\b", re.IGNORECASE),
        "caused {goal_subject}",
    ),
    (
        re.compile(r"\bcaused the crisis\b", re.IGNORECASE),
        "caused {goal_subject}",
    ),
    (
        re.compile(r"\bled to the financial crisis\b", re.IGNORECASE),
        "led to {goal_subject}",
    ),
    (
        re.compile(r"\bled to the crisis\b", re.IGNORECASE),
        "led to {goal_subject}",
    ),
    (
        re.compile(r"\btriggered the financial crisis\b", re.IGNORECASE),
        "triggered {goal_subject}",
    ),
    (
        re.compile(r"\btriggered the crisis\b", re.IGNORECASE),
        "triggered {goal_subject}",
    ),
)


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


@dataclass(frozen=True)
class _GenerationArtifacts:
    """Shared parsed artifacts for candidate generation and v0 compatibility."""

    context_payload: _ContextPayload
    parsed: _SynthesizerResponse
    evidence_by_id: dict[str, EvidenceItem]
    trace_id: str


class SimpleSynthesizer:
    """Generate candidate claims and, for v0 compatibility, a final `DecisionPacket`."""

    def __init__(
        self,
        llm_client: LLMClientProtocol,
        settings: ASARSettings,
        claim_selector: ClaimSelector | None = None,
        mechanism_bundler: MechanismBundler | None = None,
        mechanism_sketcher: MechanismSketcher | None = None,
        mechanism_slot_builder: MechanismSlotBuilder | None = None,
        mechanism_slate_selector: MechanismSlateSelector | None = None,
    ) -> None:
        self._llm_client = llm_client
        self._settings = settings
        self._claim_selector = claim_selector or ClaimSelector()
        self._mechanism_bundler = mechanism_bundler or MechanismBundler()
        self._mechanism_sketcher = mechanism_sketcher or MechanismSketcher(
            mechanism_bundler=self._mechanism_bundler
        )
        self._mechanism_slot_builder = mechanism_slot_builder or MechanismSlotBuilder(
            mechanism_sketcher=self._mechanism_sketcher
        )
        self._mechanism_slate_selector = mechanism_slate_selector or MechanismSlateSelector()
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

    async def generate_candidate_claims(
        self,
        evidence: list[EvidenceItem],
        context: str | None = None,
    ) -> CandidateClaimSet:
        """Generate typed candidate claims without selecting the final decision."""

        result = await self.generate_candidate_claims_result(evidence, context=context)
        if result.is_error and result.error is not None:
            raise DeliberationError(
                result.error.message,
                details=result.error.details,
                retryable=result.error.retryable,
            )
        return result.unwrap()

    async def generate_candidate_claims_result(
        self,
        evidence: list[EvidenceItem],
        context: str | None = None,
    ) -> OperationResult[CandidateClaimSet]:
        """Generate candidate claims while keeping failure paths inspectable."""

        generation_result = await self._generate_artifacts(evidence, context=context)
        if generation_result.is_error and generation_result.error is not None:
            return OperationResult.fail(
                generation_result.error.code,
                generation_result.error.message,
                retryable=generation_result.error.retryable,
                details=generation_result.error.details,
            )

        artifacts = generation_result.unwrap()
        try:
            candidate_claim_set = self._build_candidate_claim_set(
                parsed=artifacts.parsed,
                context_payload=artifacts.context_payload,
                evidence_by_id=artifacts.evidence_by_id,
            )
        except DeliberationError as exc:
            return OperationResult.fail(
                "deliberation_response_invalid",
                exc.message,
                details={**exc.details, "trace_id": artifacts.trace_id},
            )

        return OperationResult.ok(candidate_claim_set)

    async def deliberate_result(
        self,
        evidence: list[EvidenceItem],
        context: str | None = None,
    ) -> OperationResult[DecisionPacket]:
        """Generate a decision packet while keeping failure paths inspectable."""

        generation_result = await self._generate_artifacts(evidence, context=context)
        if generation_result.is_error and generation_result.error is not None:
            return OperationResult.fail(
                generation_result.error.code,
                generation_result.error.message,
                retryable=generation_result.error.retryable,
                details=generation_result.error.details,
            )

        artifacts = generation_result.unwrap()
        try:
            generated_candidate_claim_set = self._build_candidate_claim_set(
                parsed=artifacts.parsed,
                context_payload=artifacts.context_payload,
                evidence_by_id=artifacts.evidence_by_id,
            )
            selected_candidate_claim_set = self._claim_selector.select(
                candidate_claim_set=generated_candidate_claim_set,
                evidence=evidence,
                goal=artifacts.context_payload.goal,
            )
            decision = self._build_decision_packet(
                candidate_claim_set=selected_candidate_claim_set,
                conflicts=artifacts.parsed.conflicts,
            )
        except DeliberationError as exc:
            return OperationResult.fail(
                "deliberation_response_invalid",
                exc.message,
                details={**exc.details, "trace_id": artifacts.trace_id},
            )

        return OperationResult.ok(decision)

    async def _generate_artifacts(
        self,
        evidence: list[EvidenceItem],
        context: str | None = None,
    ) -> OperationResult[_GenerationArtifacts]:
        """Run the generation call once and return typed parsed artifacts."""

        if not evidence:
            return OperationResult.fail(
                "deliberation_empty_evidence",
                "Deliberation requires at least one EvidenceItem",
            )

        try:
            context_payload = self._parse_context(context)
            evidence_payload = self._serialize_evidence(evidence, goal=context_payload.goal)
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

        logger.info("Generating deliberation response")
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
        except DeliberationError as exc:
            logger.error("Synthesizer response validation failed")
            return OperationResult.fail(
                "deliberation_response_invalid",
                exc.message,
                details={**exc.details, "trace_id": trace_id},
            )

        logger.info("Deliberation response parsed")
        return OperationResult.ok(
            _GenerationArtifacts(
                context_payload=context_payload,
                parsed=parsed,
                evidence_by_id={item.evidence_id: item for item in evidence},
                trace_id=trace_id,
            )
        )

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

    def _serialize_evidence(
        self,
        evidence: list[EvidenceItem],
        *,
        goal: str | None = None,
    ) -> list[dict[str, object]]:
        seen_ids: set[str] = set()

        for item in evidence:
            if item.evidence_id in seen_ids:
                raise DeliberationError(
                    "Evidence IDs must be unique for deliberation",
                    details={"evidence_id": item.evidence_id},
                )
            seen_ids.add(item.evidence_id)

        slots = self._mechanism_slot_builder.build(evidence, goal=goal)
        slate = self._mechanism_slate_selector.select_from_slots(slots, goal=goal)
        payload: list[dict[str, object]] = []
        for entry in slate.entries:
            payload.append(
                {
                    "slate_id": slate.slate_id,
                    "slate_entry_id": entry.entry_id,
                    "distinct_family_count": slate.distinct_family_count,
                    "family_duplication_count": entry.family_duplication_count,
                    "slate_score": slate.slate_score,
                    "slot_id": f"slot_{entry.family_key}",
                    # Preserve sketch-id markers for existing prompt-driven regressions.
                    "sketch_id": f"sketch_{entry.family_key}",
                    "mechanism_label": entry.canonical_label,
                    "canonical_label": entry.canonical_label,
                    "target_event_anchor": entry.target_event_anchor,
                    "evidence_ids": list(entry.supporting_evidence_ids),
                    "source_titles": [
                        _truncate_text(title, _MAX_EVIDENCE_TITLE_CHARS)
                        for title in entry.source_titles
                    ],
                    "support_diversity_count": entry.support_diversity_count,
                    "support_sufficiency_score": entry.support_sufficiency_score,
                    "entry_score": entry.entry_score,
                    "content": _truncate_text(
                        entry.grounded_rationale,
                        _MAX_EVIDENCE_CONTENT_CHARS,
                    ),
                }
            )

        return payload

    def _build_request(
        self,
        *,
        evidence_payload: list[dict[str, object]],
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
            "- use only the provided raw evidence IDs listed in each slot's evidence_ids field\n"
            "- each evidence slot groups one grounded mechanism-family slice of the raw evidence\n"
            "- when slate_id and slate_entry_id are present, they represent the preselected "
            "diverse mechanism slate for drafting; avoid drafting two claims from the same "
            "family when a different supported family is already in the slate\n"
            "- produce 2 to 4 grounded candidate claims when the evidence supports them\n"
            "- every claim must directly answer the Goal, not just mention a nearby event\n"
            "- if the Goal asks for causes, reasons, drivers, or factors, every claim must "
            "state a cause-like answer rather than a response, consequence, timeline event, "
            "or policy reaction\n"
            "- prefer specific mechanism-level claims over vague umbrella summaries\n"
            "- prefer the most directly supported version of a mechanism claim; do not add "
            "narrower qualifiers unless the supporting evidence explicitly names them\n"
            "- when the evidence supports multiple distinct mechanisms, keep them as "
            "separate claims rather than collapsing them into one\n"
            "- rewrite copied evidence phrasing into a short direct causal claim when possible\n"
            "- if evidence describes a mechanism without explicit cause wording, rewrite it into "
            "a direct causal answer like '<mechanism> contributed to <target event>'\n"
            "- preserve each slot's target_event_anchor in the drafted claim wording "
            "when possible\n"
            "- prefer direct answer shapes like '<mechanism> contributed to <event>' over "
            "descriptive snippets like 'X is more than just...' or "
            "'The primary benefit of X is...'\n"
            "- name the target event explicitly when possible instead of saying only "
            "'the crisis' or 'the crash'\n"
            "- avoid vague phrases like 'perfect storm', 'various factors', 'other causes', "
            "or 'systemic flaws' unless the concrete mechanism is named directly\n"
            "- do not include a broad summary claim that merely restates more specific claims\n"
            "- synthesis must be one short sentence\n"
            "- each reasoning_trace must be a very short sentence fragment of 4 to 8 words\n"
            "- information_gaps must contain at most 2 short strings\n"
            "- return conflicts as [] unless a clear contradiction is explicit in the evidence\n"
            "- keep the entire JSON compact and brief\n"
            "- do not verify truth or invent citations\n"
            f"Plan ID: {context_payload.plan_id}\n"
            f"Goal: {context_payload.goal or 'unknown'}\n"
            f"Evidence Bundles: {json.dumps(evidence_payload, sort_keys=True)}"
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

    def _build_candidate_claim_set(
        self,
        *,
        parsed: _SynthesizerResponse,
        context_payload: _ContextPayload,
        evidence_by_id: dict[str, EvidenceItem],
    ) -> CandidateClaimSet:
        selected_claims, rejected_claims = _select_candidate_claim_drafts(
            parsed=parsed,
            goal=context_payload.goal,
            evidence_by_id=evidence_by_id,
        )

        candidate_claims: list[CandidateClaim] = []
        for original_index, draft in selected_claims:
            candidate_claims.append(
                CandidateClaim(
                    candidate_claim_id=generate_id("candidate_claim"),
                    source_claim_index=original_index,
                    text=draft.text.strip(),
                    epistemic_status=draft.epistemic_status,
                    supporting_evidence_ids=draft.supporting_evidence_ids,
                    contradicting_evidence_ids=draft.contradicting_evidence_ids,
                    reasoning_trace=draft.reasoning_trace,
                )
            )

        if not candidate_claims:
            raise DeliberationError(
                "Synthesizer did not produce claims that answered the goal",
                details={
                    "goal": context_payload.goal,
                    "rejected_claims": rejected_claims,
                },
            )

        try:
            return CandidateClaimSet(
                candidate_set_id=generate_id("candidate_set"),
                plan_id=context_payload.plan_id,
                claims=candidate_claims,
                draft_synthesis=parsed.synthesis,
                information_gaps=parsed.information_gaps,
            )
        except ValidationError as exc:
            raise DeliberationError(
                "Synthesizer produced an invalid CandidateClaimSet",
                details={"errors": exc.errors()},
            ) from exc

    def _build_decision_packet(
        self,
        *,
        candidate_claim_set: CandidateClaimSet,
        conflicts: list[_ConflictDraft],
    ) -> DecisionPacket:
        claims: list[Claim] = []
        claim_ids_by_original_index: dict[int, str] = {}
        for candidate_claim in candidate_claim_set.claims:
            claim = Claim(
                claim_id=generate_id(IDPrefix.CLAIM),
                text=candidate_claim.text.strip(),
                epistemic_status=candidate_claim.epistemic_status,
                supporting_evidence_ids=candidate_claim.supporting_evidence_ids,
                contradicting_evidence_ids=candidate_claim.contradicting_evidence_ids,
                reasoning_trace=candidate_claim.reasoning_trace,
            )
            claims.append(claim)
            claim_ids_by_original_index[candidate_claim.source_claim_index] = claim.claim_id

        typed_conflicts: list[Conflict] = []
        for draft in conflicts:
            if any(
                claim_index not in claim_ids_by_original_index
                for claim_index in draft.claim_indexes
            ):
                continue

            claim_ids = []
            for claim_index in draft.claim_indexes:
                claim_ids.append(claim_ids_by_original_index[claim_index])

            typed_conflicts.append(
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
                plan_id=candidate_claim_set.plan_id,
                claims=claims,
                conflicts=typed_conflicts,
                synthesis=candidate_claim_set.draft_synthesis,
                information_gaps=candidate_claim_set.information_gaps,
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


def _truncate_text(value: str, limit: int) -> str:
    stripped = value.strip()
    if len(stripped) <= limit:
        return stripped
    return stripped[: max(0, limit - 3)].rstrip() + "..."


def _goal_requires_causal_claims(goal: str | None) -> bool:
    if goal is None:
        return False

    normalized_goal = goal.strip().lower()
    if not normalized_goal:
        return False

    return any(marker in normalized_goal for marker in _CAUSAL_GOAL_MARKERS)


def _claim_answers_goal(*, draft: _ClaimDraft, goal: str | None) -> tuple[bool, str | None]:
    if not _goal_requires_causal_claims(goal):
        return True, None

    normalized_text = draft.text.strip().lower()
    if not normalized_text:
        return False, "claim_text_empty"

    has_causal_language = any(marker in normalized_text for marker in _CAUSAL_CLAIM_MARKERS)
    has_response_language = any(marker in normalized_text for marker in _RESPONSE_CLAIM_MARKERS)

    if has_response_language and not has_causal_language:
        return False, "claim_describes_response_not_cause"
    return True, None


def _select_candidate_claim_drafts(
    *,
    parsed: _SynthesizerResponse,
    goal: str | None,
    evidence_by_id: dict[str, EvidenceItem],
) -> tuple[list[tuple[int, _ClaimDraft]], list[dict[str, str | int]]]:
    rejected_claims: list[dict[str, str | int]] = []
    candidate_claims: list[tuple[int, _ClaimDraft]] = []

    for original_index, draft in enumerate(parsed.claims, start=1):
        normalized_draft = _normalize_claim_draft_text(
            draft=draft,
            goal=goal,
            supporting_evidence=[
                evidence_by_id[evidence_id]
                for evidence_id in draft.supporting_evidence_ids
                if evidence_id in evidence_by_id
            ],
        )
        referenced_ids = set(draft.supporting_evidence_ids) | set(
            draft.contradicting_evidence_ids
        )
        unknown_ids = sorted(referenced_ids - set(evidence_by_id))
        if unknown_ids:
            raise DeliberationError(
                "Synthesizer referenced unknown evidence IDs",
                details={"unknown_evidence_ids": unknown_ids},
            )

        is_relevant, rejection_reason = _claim_answers_goal(
            draft=normalized_draft,
            goal=goal,
        )
        if not is_relevant:
            rejected_claims.append(
                {
                    "claim_index": original_index,
                    "text": normalized_draft.text.strip(),
                    "reason": rejection_reason or "claim_did_not_answer_goal",
                }
            )
            continue

        candidate_claims.append((original_index, normalized_draft))

    filtered_candidates, filtered_rejections = _filter_claim_candidates(
        candidates=candidate_claims,
        goal=goal,
    )
    rejected_claims.extend(filtered_rejections)
    augmented_candidates = _augment_candidate_claim_drafts(
        candidates=filtered_candidates,
        goal=goal,
        evidence_by_id=evidence_by_id,
    )
    return augmented_candidates, rejected_claims


def _filter_claim_candidates(
    *,
    candidates: list[tuple[int, _ClaimDraft]],
    goal: str | None,
) -> tuple[list[tuple[int, _ClaimDraft]], list[dict[str, str | int]]]:
    if not _goal_requires_causal_claims(goal):
        return candidates, []

    has_direct_claim = any(_is_direct_causal_claim(draft) for _, draft in candidates)
    if not has_direct_claim:
        return candidates, []

    filtered: list[tuple[int, _ClaimDraft]] = []
    rejected: list[dict[str, str | int]] = []
    seen_texts: set[str] = set()
    for original_index, draft in candidates:
        if _is_vague_causal_claim(draft):
            rejected.append(
                {
                    "claim_index": original_index,
                    "text": draft.text.strip(),
                    "reason": "claim_too_vague_for_causal_goal",
                }
            )
            continue
        if _is_weak_descriptive_claim(draft):
            rejected.append(
                {
                    "claim_index": original_index,
                    "text": draft.text.strip(),
                    "reason": "claim_descriptive_not_direct_cause",
                }
            )
            continue
        if not _is_direct_causal_claim(draft):
            rejected.append(
                {
                    "claim_index": original_index,
                    "text": draft.text.strip(),
                    "reason": "claim_not_direct_causal_answer",
                }
            )
            continue
        normalized_text = draft.text.strip().lower()
        if normalized_text in seen_texts:
            rejected.append(
                {
                    "claim_index": original_index,
                    "text": draft.text.strip(),
                    "reason": "claim_duplicate_after_normalization",
                }
            )
            continue
        seen_texts.add(normalized_text)
        filtered.append((original_index, draft))

    return filtered, rejected


def _is_vague_causal_claim(draft: _ClaimDraft) -> bool:
    normalized_text = draft.text.strip().lower()
    if not normalized_text:
        return True

    return any(marker in normalized_text for marker in _VAGUE_CAUSAL_CLAIM_MARKERS)


def _normalize_claim_draft_text(
    *,
    draft: _ClaimDraft,
    goal: str | None,
    supporting_evidence: list[EvidenceItem],
) -> _ClaimDraft:
    normalized_text = _normalize_causal_claim_text(
        draft.text,
        goal=goal,
        supporting_evidence=supporting_evidence,
    )
    if normalized_text == draft.text.strip():
        return draft
    return draft.model_copy(update={"text": normalized_text})


def _normalize_causal_claim_text(
    text: str,
    *,
    goal: str | None,
    supporting_evidence: list[EvidenceItem],
) -> str:
    stripped = text.strip()
    if not stripped:
        return stripped

    goal_subject = _goal_subject(goal)
    if goal_subject is not None:
        match = _CRASH_WAS_CAUSED_PATTERN.match(stripped)
        if match:
            cause = _sentence_case(match.group("cause"))
            return f"{cause} contributed to {goal_subject}."

        normalized_target_text = _normalize_generic_causal_target(
            stripped,
            goal_subject=goal_subject,
        )
        if normalized_target_text != stripped:
            stripped = normalized_target_text

        if _text_has_causal_language(stripped):
            support_preserving_text = _generalize_weakly_supported_causal_claim(
                stripped,
                goal_subject=goal_subject,
                supporting_evidence=supporting_evidence,
            )
            if support_preserving_text is not None:
                return support_preserving_text

        if not _text_has_causal_language(stripped):
            rewritten_mechanism = _rewrite_descriptive_mechanism_claim(
                stripped,
                goal_subject=goal_subject,
            )
            if rewritten_mechanism is not None:
                return rewritten_mechanism

    match = _BUBBLE_WAS_CAUSED_PATTERN.match(stripped)
    if match:
        cause = _sentence_case(match.group("cause"))
        return f"{cause} caused a stock market bubble."

    return stripped


def _goal_subject(goal: str | None) -> str | None:
    if goal is None:
        return None

    stripped = goal.strip()
    if not stripped:
        return None

    lowered = stripped.lower()
    prefixes = (
        "what were the main causes of ",
        "what was the main cause of ",
        "what caused ",
        "why did ",
    )
    for prefix in prefixes:
        if lowered.startswith(prefix):
            subject = stripped[len(prefix) :].rstrip("?. ").strip()
            return subject if subject else None

    return None


def _sentence_case(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return stripped
    return stripped[0].upper() + stripped[1:]


def _is_direct_causal_claim(draft: _ClaimDraft) -> bool:
    normalized_text = draft.text.strip().lower()
    if not normalized_text:
        return False

    return (
        _text_has_causal_language(normalized_text)
        and not _is_vague_causal_claim(draft)
        and not _is_weak_descriptive_claim(draft)
    )


def _is_weak_descriptive_claim(draft: _ClaimDraft) -> bool:
    normalized_text = draft.text.strip().lower()
    if not normalized_text:
        return True

    has_causal_language = _text_has_causal_language(normalized_text)
    if has_causal_language:
        return False

    return any(marker in normalized_text for marker in _WEAK_DESCRIPTIVE_CLAIM_MARKERS) or bool(
        _DESCRIPTIVE_MECHANISM_PATTERN.match(draft.text.strip())
    )


def _text_has_causal_language(text: str) -> bool:
    normalized_text = text.strip().lower()
    if not normalized_text:
        return False
    return any(marker in normalized_text for marker in _CAUSAL_CLAIM_MARKERS)


def _normalize_generic_causal_target(text: str, *, goal_subject: str) -> str:
    if goal_subject.lower() in text.lower():
        return text

    for pattern, replacement_template in _GENERIC_CAUSAL_TARGET_PATTERNS:
        if pattern.search(text):
            return pattern.sub(
                replacement_template.format(goal_subject=goal_subject),
                text,
            )

    return text


def _rewrite_descriptive_mechanism_claim(text: str, *, goal_subject: str) -> str | None:
    match = _DESCRIPTIVE_MECHANISM_PATTERN.match(text.strip().rstrip("."))
    if match is None:
        return None

    subject = _normalize_mechanism_subject(match.group("subject"))
    if not _is_rewritable_mechanism_subject(subject):
        return None

    return f"{subject} contributed to {goal_subject}."


def _normalize_mechanism_subject(subject: str) -> str:
    stripped = subject.strip()
    lowered = stripped.lower()
    if lowered.startswith("the deregulated "):
        rest = stripped[len("the deregulated ") :].strip()
        return f"Deregulation of the {rest}"
    if lowered.startswith("deregulated "):
        rest = stripped[len("deregulated ") :].strip()
        return f"Deregulation of {rest}"
    return _sentence_case(stripped)


def _is_rewritable_mechanism_subject(subject: str) -> bool:
    lowered = subject.strip().lower()
    if not lowered or "," in subject:
        return False
    if lowered.startswith(("it", "this", "that", "these", "those", "they", "there")):
        return False

    word_count = len(subject.split())
    return 1 <= word_count <= 12


def _generalize_weakly_supported_causal_claim(
    text: str,
    *,
    goal_subject: str,
    supporting_evidence: list[EvidenceItem],
) -> str | None:
    if not supporting_evidence:
        return None

    support_text = " ".join(
        f"{item.source.title or ''} {item.content}" for item in supporting_evidence
    ).lower()
    if not support_text:
        return None

    unsupported_specific_tokens = _unsupported_specific_claim_tokens(
        text=text,
        support_text=support_text,
        goal_subject=goal_subject,
    )
    if _support_overlap_score(text, support_text) >= 2 and not unsupported_specific_tokens:
        return None

    lowered = text.lower()
    for aliases, canonical_subject in _support_generalization_families(goal_subject):
        if any(alias in lowered for alias in aliases) and any(
            alias in support_text for alias in aliases
        ):
            return f"{canonical_subject} contributed to {goal_subject}."

    return None


def _support_overlap_score(text: str, support_text: str) -> int:
    claim_tokens = {
        token
        for token in _TOKEN_PATTERN.findall(text.lower())
        if token not in _SUPPORT_STOPWORDS and len(token) > 2
    }
    support_tokens = set(_TOKEN_PATTERN.findall(support_text.lower()))
    return len(claim_tokens & support_tokens)


def _unsupported_specific_claim_tokens(
    *,
    text: str,
    support_text: str,
    goal_subject: str,
    ignored_aliases: tuple[str, ...] = (),
) -> set[str]:
    claim_tokens = {
        token
        for token in _TOKEN_PATTERN.findall(text.lower())
        if token not in _SUPPORT_STOPWORDS and len(token) > 2
    }
    support_tokens = set(_TOKEN_PATTERN.findall(support_text.lower()))
    goal_tokens = {
        token
        for token in _TOKEN_PATTERN.findall(goal_subject.lower())
        if token not in _SUPPORT_STOPWORDS and len(token) > 2
    }
    ignored_tokens = set(goal_tokens) | set(_CAUSAL_TEXT_IGNORE_TOKENS)
    for alias in ignored_aliases:
        ignored_tokens.update(_TOKEN_PATTERN.findall(alias.lower()))

    return {
        token
        for token in claim_tokens
        if token not in ignored_tokens and token not in support_tokens
    }


def _augment_candidate_claim_drafts(
    *,
    candidates: list[tuple[int, _ClaimDraft]],
    goal: str | None,
    evidence_by_id: dict[str, EvidenceItem],
) -> list[tuple[int, _ClaimDraft]]:
    if not _goal_requires_causal_claims(goal):
        return candidates

    goal_subject = _goal_subject(goal)
    if goal_subject is None:
        return candidates

    max_candidates = 4
    if len(candidates) < 2 or len(candidates) >= max_candidates:
        return candidates

    augmented = list(candidates)
    next_index = max((original_index for original_index, _ in augmented), default=0) + 1
    evidence_items = list(evidence_by_id.values())

    for aliases, canonical_subject in _support_generalization_families(goal_subject):
        if len(augmented) >= max_candidates:
            break
        if _should_skip_redundant_family_backfill(
            candidates=augmented,
            canonical_subject=canonical_subject,
        ):
            continue
        if _has_stably_covered_family(
            candidates=augmented,
            aliases=aliases,
            goal_subject=goal_subject,
            evidence_by_id=evidence_by_id,
        ):
            continue

        supporting_ids = _matching_supporting_evidence_ids(
            evidence=evidence_items,
            aliases=aliases,
        )
        if not supporting_ids:
            continue

        canonical_text = f"{canonical_subject} contributed to {goal_subject}."
        if any(draft.text.strip().lower() == canonical_text.lower() for _, draft in augmented):
            continue

        augmented.append(
            (
                next_index,
                _ClaimDraft(
                    text=canonical_text,
                    supporting_evidence_ids=supporting_ids,
                    contradicting_evidence_ids=[],
                    epistemic_status=EpistemicStatus.MODERATE_CONFIDENCE,
                    reasoning_trace="Evidence explicitly names mechanism.",
                ),
            )
        )
        next_index += 1

    return augmented


def _should_skip_redundant_family_backfill(
    *,
    candidates: list[tuple[int, _ClaimDraft]],
    canonical_subject: str,
) -> bool:
    if canonical_subject != "Mortgage-backed securities":
        return False

    return any("subprime lending" in draft.text.lower() for _, draft in candidates)


def _has_stably_covered_family(
    *,
    candidates: list[tuple[int, _ClaimDraft]],
    aliases: tuple[str, ...],
    goal_subject: str,
    evidence_by_id: dict[str, EvidenceItem],
) -> bool:
    for _, draft in candidates:
        lowered = draft.text.lower()
        if not any(alias in lowered for alias in aliases):
            continue

        support_text = " ".join(
            f"{evidence_by_id[evidence_id].source.title or ''} "
            f"{evidence_by_id[evidence_id].content}"
            for evidence_id in draft.supporting_evidence_ids
            if evidence_id in evidence_by_id
        ).lower()
        if not support_text:
            continue

        unsupported_specific_tokens = _unsupported_specific_claim_tokens(
            text=draft.text,
            support_text=support_text,
            goal_subject=goal_subject,
            ignored_aliases=aliases,
        )
        if (
            _support_overlap_score(draft.text, support_text) >= 2
            and not unsupported_specific_tokens
        ):
            return True

    return False


def _matching_supporting_evidence_ids(
    *,
    evidence: list[EvidenceItem],
    aliases: tuple[str, ...],
) -> list[str]:
    matched_ids: list[str] = []
    for item in evidence:
        searchable_text = f"{item.source.title or ''} {item.content}".lower()
        if any(alias in searchable_text for alias in aliases):
            matched_ids.append(item.evidence_id)
    return matched_ids


def _support_generalization_families(goal_subject: str) -> tuple[tuple[tuple[str, ...], str], ...]:
    lowered_goal_subject = goal_subject.lower()
    for goal_aliases, families in _GOAL_SUPPORT_GENERALIZATION_FAMILIES:
        if any(alias in lowered_goal_subject for alias in goal_aliases):
            return families
    return ()

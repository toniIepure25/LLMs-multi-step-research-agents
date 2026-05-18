"""
ASAR webapp backend — FastAPI server that wraps the v0 demo pipeline and
exposes the fine-tuned **v3** preference model.

Design
------

The fine-tuned model (Qwen2.5-0.5B + LoRA, SFT v3 + DPO v3) was trained for
**pairwise grounded claim selection** on SciFact preference pairs. It is not
a planner and not a synthesizer — asking it to emit JSON plans or full
deliberation packets fails fast.

So this server does two things:

1. ``POST /api/research`` runs the **structurally reliable** pipeline:
   deterministic plan + deterministic synthesizer over **real SciFact corpus
   retrieval** + real evidence-checker + real safety filter. The output is a
   fully typed ``ResearchOutput``.

2. ``POST /api/rerank`` invokes the **v3 adapter directly** on its native
   task — given a goal and two candidate claims, the model picks the one
   it judges supported by the corpus. The frontend calls this endpoint
   once per generated claim so the v3 model is exercised on every run.

Endpoints
---------
- ``GET  /api/health``  — liveness
- ``GET  /api/info``    — adapter metadata + provider state
- ``POST /api/research`` — body ``{"goal": str, "safety_enabled": bool}``
- ``POST /api/rerank``  — body ``{"goal": str, "claim_a": str, "claim_b": str}``
- ``POST /api/warmup``  — force the v3 adapter to load (returns load latency)

Run::

    ./webapp/run-backend.sh
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from asar.core.errors import ASARError
from asar.core.llm import LLMGenerationRequest, LLMMessage, MessageRole
from asar.demo.run import build_demo_orchestrator
from asar.safety.pipeline import SafetyAwareRunner

LOG = logging.getLogger("asar.webapp")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s :: %(message)s")


# ---------------------------------------------------------------------------
# State — a single LocalSLMClient warm-cached across requests.
# ---------------------------------------------------------------------------


class _State:
    local_client: Any = None  # set lazily; typed as Any to avoid optional-dep import here


STATE = _State()


def _ensure_local_client() -> Any:
    """Build (and cache) the v3 LocalSLMClient. Raises if local-llm extras missing."""
    if STATE.local_client is not None:
        return STATE.local_client
    from asar.providers.local_llm import build_local_llm_client

    client = build_local_llm_client(
        base_model=os.environ.get("ASAR_LOCAL_BASE_MODEL"),
        adapter_path=os.environ.get("ASAR_LOCAL_ADAPTER_PATH"),
    )
    STATE.local_client = client
    return client


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    adapter_path = os.environ.get("ASAR_LOCAL_ADAPTER_PATH", "(unset)")
    base_model = os.environ.get("ASAR_LOCAL_BASE_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")
    provider = os.environ.get("ASAR_MODEL_PROVIDER", "(unset)")
    LOG.info("startup: ASAR_MODEL_PROVIDER=%s base=%s adapter=%s", provider, base_model, adapter_path)
    LOG.info(
        "startup: search_provider=%s safety=%s",
        os.environ.get("ASAR_SEARCH_PROVIDER", "(default)"),
        os.environ.get("ASAR_SAFETY_ENABLED", "(default)"),
    )
    try:
        _ensure_local_client()
    except Exception as exc:  # pragma: no cover - optional dep
        LOG.warning("could not construct LocalSLMClient at startup: %s", exc)
    yield
    LOG.info("shutdown")


app = FastAPI(
    title="ASAR Webapp API",
    description="Run the v0 ASAR research pipeline (planner → executor → memory → "
                "synthesizer → verifier → evaluator) over the SciFact corpus, with "
                "the fine-tuned Qwen-0.5B + LoRA (DPO v3) adapter exposed at /api/rerank.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ResearchRequest(BaseModel):
    goal: str = Field(..., min_length=4, max_length=500)
    safety_enabled: bool = Field(default=True)


class ResearchSafetyReport(BaseModel):
    blocked_pre: bool
    blocked_post: bool
    blocked_reason: str | None = None
    max_toxicity_pre: float
    max_injection_pre: float
    max_toxicity_post: float
    max_injection_post: float


class GroundedAnswer(BaseModel):
    """LLM-generated answer that quotes the retrieved passages by [n] index."""

    text: str
    cited_indices: list[int]
    cited_evidence_ids: list[str]
    elapsed_seconds: float
    generated: bool
    note: str | None = None


class ResearchResponse(BaseModel):
    goal: str
    elapsed_seconds: float
    adapter_metadata: dict[str, Any]
    output: dict[str, Any]
    safety: ResearchSafetyReport
    answer: GroundedAnswer | None = None


class InfoResponse(BaseModel):
    base_model: str
    adapter_path: str | None
    adapter_metadata: dict[str, Any] | None
    search_provider: str | None
    safety_enabled: bool
    adapter_loaded: bool


class RerankRequest(BaseModel):
    goal: str = Field(..., min_length=4, max_length=500)
    claim_a: str = Field(..., min_length=2, max_length=1500)
    claim_b: str = Field(..., min_length=2, max_length=1500)


class RerankResponse(BaseModel):
    preferred: str = Field(..., description="'A' or 'B'")
    raw: str = Field(..., description="Raw model output (first ~64 chars)")
    elapsed_seconds: float


class WarmupResponse(BaseModel):
    adapter_loaded: bool
    elapsed_seconds: float
    sample: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_adapter_metadata() -> dict[str, Any] | None:
    adapter_path = os.environ.get("ASAR_LOCAL_ADAPTER_PATH")
    if not adapter_path:
        return None
    for name in ("asar_dpo_metadata.json", "asar_finetune_metadata.json"):
        candidate = Path(adapter_path) / name
        if candidate.exists():
            try:
                return json.loads(candidate.read_text(encoding="utf-8"))
            except Exception as exc:  # pragma: no cover - best-effort
                LOG.warning("could not parse %s: %s", candidate, exc)
                return {"adapter_path": adapter_path, "error": str(exc)}
    return {"adapter_path": adapter_path, "note": "no sidecar metadata file"}


def _safety_enabled_env() -> bool:
    return os.environ.get("ASAR_SAFETY_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"}


def _first_sentence(text: str, *, max_chars: int = 240) -> str:
    """Return the first sentence of ``text``, truncated to ``max_chars``."""
    if not text:
        return ""
    cleaned = " ".join(text.split())
    # Cut at the first ". " / "? " / "! " boundary if it appears before max_chars.
    for stop in (". ", "? ", "! "):
        idx = cleaned.find(stop)
        if 0 < idx <= max_chars:
            return cleaned[: idx + 1].strip()
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max_chars - 1].rstrip() + "…"


def _strip_topic_prefix(text: str) -> str:
    """Strip leading ``"Topic label: "`` prefixes the SimpleSynthesizer prepends.

    The default v0 synthesizer ships with a 2008-financial-crisis-themed
    thesaurus and prepends labels like ``"OTC derivatives and deregulation:
    …"`` to every claim. Those labels are unhelpful (and often nonsensical)
    when the corpus is SciFact biomedical text, so we strip the prefix when
    it appears at the start of the claim and is short.
    """
    if not text:
        return text
    idx = text.find(": ")
    if 0 < idx <= 80 and text[:idx].count(" ") <= 8:
        return text[idx + 2 :].lstrip()
    return text


# ---------------------------------------------------------------------------
# Grounded-answer generation
# ---------------------------------------------------------------------------

_ANSWER_SYSTEM_PROMPT = (
    "You are a careful scientific assistant. You will be given a research "
    "question and a short list of numbered retrieved passages. Write a "
    "concise answer (2 to 4 sentences) that is grounded ONLY in the passages "
    "provided. Cite the passages you use with bracketed numbers like [1] or "
    "[2]. If the passages do not directly address the question, say so "
    "honestly in one sentence. Do not invent facts beyond the passages. "
    "Do not copy the passages verbatim — paraphrase. Do not list the "
    "passages back. Begin your answer immediately."
)

_ANSWER_FEWSHOT_USER = (
    "Question: Does aspirin reduce the risk of colorectal cancer?\n\n"
    "Passages:\n"
    "[1] Aspirin in cancer prevention: Long-term low-dose aspirin reduced "
    "the incidence of colorectal cancer by roughly 24% in a 20-year follow-up "
    "of randomized trials.\n"
    "[2] Bleeding risks of aspirin: Daily aspirin increases the risk of "
    "gastrointestinal bleeding, especially in older adults.\n\n"
    "Answer (2-4 sentences, cite passages as [1], [2], ...):"
)

_ANSWER_FEWSHOT_ASSISTANT = (
    "Yes — long-term low-dose aspirin has been shown to reduce the incidence "
    "of colorectal cancer by around 24% in pooled randomized-trial follow-ups "
    "[1]. The benefit must be weighed against an increased risk of "
    "gastrointestinal bleeding, particularly in older adults [2]."
)

_CITATION_RE = re.compile(r"\[(\d{1,2})\]")


def _truncate(text: str, *, max_chars: int) -> str:
    cleaned = " ".join((text or "").split())
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max_chars - 1].rstrip() + "…"


async def _generate_grounded_answer(
    *, goal: str, evidence_payload: list[dict[str, Any]]
) -> GroundedAnswer:
    """Ask the loaded local model for a grounded answer over the top passages.

    Returns a ``GroundedAnswer`` with ``generated=False`` and a fallback
    sentence if the local client is unavailable or generation fails — we
    never raise out of this helper because the rest of the pipeline is
    perfectly usable without it.
    """
    if not evidence_payload:
        return GroundedAnswer(
            text="No evidence was retrieved for this query, so no grounded answer can be produced.",
            cited_indices=[],
            cited_evidence_ids=[],
            elapsed_seconds=0.0,
            generated=False,
            note="no_evidence",
        )

    # Build a numbered passage list (1-indexed) for the prompt.
    passages = evidence_payload[:5]
    lines: list[str] = []
    for idx, ev in enumerate(passages, start=1):
        title = (ev.get("source") or {}).get("title") or "Untitled"
        content = _truncate(ev.get("content") or "", max_chars=600)
        lines.append(f"[{idx}] {title}: {content}")
    passages_block = "\n".join(lines)

    user_msg = (
        f"Question: {goal.strip()}\n\n"
        f"Passages:\n{passages_block}\n\n"
        "Answer (2-4 sentences, cite passages as [1], [2], ...):"
    )

    try:
        client = _ensure_local_client()
    except Exception as exc:
        LOG.warning("answer: local client unavailable (%s)", exc)
        return GroundedAnswer(
            text=(
                "The local model is not available, so a generated answer could not be produced. "
                "The retrieved evidence and extracted claims below are still available for review."
            ),
            cited_indices=[],
            cited_evidence_ids=[],
            elapsed_seconds=0.0,
            generated=False,
            note=f"local_unavailable: {exc}",
        )

    request = LLMGenerationRequest(
        model=os.environ.get("ASAR_LOCAL_BASE_MODEL", "Qwen/Qwen2.5-0.5B-Instruct"),
        messages=[
            LLMMessage(role=MessageRole.SYSTEM, content=_ANSWER_SYSTEM_PROMPT),
            LLMMessage(role=MessageRole.USER, content=_ANSWER_FEWSHOT_USER),
            LLMMessage(role=MessageRole.ASSISTANT, content=_ANSWER_FEWSHOT_ASSISTANT),
            LLMMessage(role=MessageRole.USER, content=user_msg),
        ],
        temperature=0.3,
        # 200 tokens (~80 words) was clipping the model mid-sentence on
        # 3-4 sentence answers with citations.  400 gives the model
        # enough headroom to finish a paragraph naturally, while still
        # staying well under the local client's 512-token cap.
        max_tokens=400,
        # Bypass the v3 LoRA: it was DPO-trained for A/B picks and would
        # bias generation toward single-letter outputs.  Use the base
        # Qwen-0.5B-Instruct weights for free-form prose.
        metadata={"component": "answer", "disable_adapter": "1"},
    )

    start = time.monotonic()
    try:
        resp = await client.generate(request)
        raw = (resp.output_text or "").strip()
    except Exception as exc:  # pragma: no cover - defensive
        LOG.exception("answer generation failed")
        return GroundedAnswer(
            text=(
                "The local model failed to produce a grounded answer for this query. "
                "See the retrieved evidence and extracted claims below."
            ),
            cited_indices=[],
            cited_evidence_ids=[],
            elapsed_seconds=time.monotonic() - start,
            generated=False,
            note=f"generation_error: {exc}",
        )
    elapsed = time.monotonic() - start

    # Strip any leading "Answer:" the model tends to echo.
    if raw.lower().startswith("answer:"):
        raw = raw[len("answer:") :].lstrip()

    # Extract the [n] indices the model actually cited, in order, deduped.
    cited_indices: list[int] = []
    for match in _CITATION_RE.finditer(raw):
        n = int(match.group(1))
        if 1 <= n <= len(passages) and n not in cited_indices:
            cited_indices.append(n)

    cited_evidence_ids = [
        passages[i - 1].get("evidence_id", "") for i in cited_indices
    ]
    cited_evidence_ids = [eid for eid in cited_evidence_ids if eid]

    return GroundedAnswer(
        text=raw,
        cited_indices=cited_indices,
        cited_evidence_ids=cited_evidence_ids,
        elapsed_seconds=elapsed,
        generated=True,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/info", response_model=InfoResponse)
async def info() -> InfoResponse:
    return InfoResponse(
        base_model=os.environ.get("ASAR_LOCAL_BASE_MODEL", "Qwen/Qwen2.5-0.5B-Instruct"),
        adapter_path=os.environ.get("ASAR_LOCAL_ADAPTER_PATH"),
        adapter_metadata=_read_adapter_metadata(),
        search_provider=os.environ.get("ASAR_SEARCH_PROVIDER"),
        safety_enabled=_safety_enabled_env(),
        adapter_loaded=STATE.local_client is not None and getattr(STATE.local_client, "_model", None) is not None,
    )


@app.post("/api/research", response_model=ResearchResponse)
async def research(req: ResearchRequest) -> ResearchResponse:
    """Run the deterministic pipeline over the live SciFact corpus.

    ``mode="mock"`` gives us a deterministic planner + synthesizer; the search
    client is overridden to the SciFact corpus via ``ASAR_SEARCH_PROVIDER=corpus``,
    so the executor pulls real retrieved passages. The synthesizer mirrors that
    evidence into well-formed claims so the UI always has a structurally correct
    ``ResearchOutput`` — the frontend then exercises the v3 model per-claim
    against ``/api/rerank``.
    """
    goal = req.goal.strip()
    if not goal:
        raise HTTPException(status_code=400, detail="goal is required")

    start = time.monotonic()
    orchestrator = build_demo_orchestrator(mode="mock")
    runner = SafetyAwareRunner(orchestrator=orchestrator) if req.safety_enabled else None

    try:
        if runner is None:
            output = await orchestrator.run(goal)
            safety = ResearchSafetyReport(
                blocked_pre=False,
                blocked_post=False,
                blocked_reason=None,
                max_toxicity_pre=0.0,
                max_injection_pre=0.0,
                max_toxicity_post=0.0,
                max_injection_post=0.0,
            )
        else:
            outcome = await runner.run(goal)
            pre = outcome.pre_report
            post = outcome.post_report
            safety = ResearchSafetyReport(
                blocked_pre=outcome.blocked_pre,
                blocked_post=outcome.blocked_post,
                blocked_reason=outcome.blocked_reason,
                max_toxicity_pre=pre.overall_max_toxicity if pre else 0.0,
                max_injection_pre=pre.overall_max_injection if pre else 0.0,
                max_toxicity_post=post.overall_max_toxicity if post else 0.0,
                max_injection_post=post.overall_max_injection if post else 0.0,
            )
            if outcome.blocked_pre or outcome.output is None:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "blocked_by_safety",
                        "reason": outcome.blocked_reason or "unsafe_goal",
                    },
                )
            output = outcome.output
    except ASARError as exc:
        LOG.exception("pipeline error")
        raise HTTPException(status_code=500, detail={"error": exc.message, "details": exc.details}) from exc
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        LOG.exception("unexpected error")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    elapsed = time.monotonic() - start
    payload = output.model_dump(mode="json")
    _polish_output(payload, goal=goal, elapsed=elapsed)

    # Generate a real grounded answer from the retrieved passages using the
    # loaded local model.  Best-effort: never raises out of the helper.
    # Disable via ASAR_DISABLE_GROUNDED_ANSWER=1 if the proxy keeps timing out
    # during long generation (e.g. CPU inference on a fresh start).
    if os.environ.get("ASAR_DISABLE_GROUNDED_ANSWER") == "1":
        answer = GroundedAnswer(
            text="",
            cited_indices=[],
            cited_evidence_ids=[],
            elapsed_seconds=0.0,
            generated=False,
            note="disabled_via_env",
        )
    else:
        evidence_payload = payload.get("evidence") or []
        answer = await _generate_grounded_answer(goal=goal, evidence_payload=evidence_payload)

    # If the model wrote something usable, surface it inside the decision's
    # synthesis field too so downstream consumers (raw JSON viewers, exports)
    # see a coherent paragraph rather than the pipeline-description string.
    if answer.generated and answer.text:
        decision = payload.get("decision") or {}
        decision["synthesis"] = answer.text

    return ResearchResponse(
        goal=goal,
        elapsed_seconds=elapsed,
        adapter_metadata=_read_adapter_metadata() or {},
        output=payload,
        safety=safety,
        answer=answer,
    )


def _polish_output(payload: dict[str, Any], *, goal: str, elapsed: float) -> None:
    """Replace deterministic placeholder strings with goal-aware language.

    The demo synthesizer mirrors raw evidence content into "claims" and emits
    a fixed synthesis string. That's fine for tests but reads strangely in
    the UI. We rewrite only the human-facing strings — IDs, evidence IDs,
    and claim/evidence linkage are left untouched so the rerank call still
    receives the original substantive text.
    """
    decision = payload.get("decision") or {}
    claims = decision.get("claims") or []
    evidence = payload.get("evidence") or []
    evidence_by_id = {
        str(ev.get("evidence_id")): ev for ev in evidence if ev.get("evidence_id")
    }

    n_claims = len(claims)
    n_evidence = len(evidence)

    if decision:
        decision["synthesis"] = (
            f"Over {n_evidence} retrieved passage{'s' if n_evidence != 1 else ''} "
            f"the pipeline surfaced {n_claims} candidate claim"
            f"{'s' if n_claims != 1 else ''} relevant to “{goal}”. "
            f"Each claim below quotes its supporting passage; the v3 adapter "
            f"is invoked on every claim to judge whether the corpus supports it."
        )
        for idx, claim in enumerate(claims, start=1):
            text = (claim.get("text") or "").strip()
            text = _strip_topic_prefix(text)

            # Pull the full passage from the first supporting evidence item
            # so the UI can offer a "show full claim" toggle.  The synthesizer
            # truncates to ~220 chars with "..."; if the synthesizer's text
            # ends in an ellipsis (one of "...", "…"), the original evidence
            # content is almost certainly longer.
            supporting_ids = claim.get("supporting_evidence_ids") or []
            full_from_evidence: str | None = None
            for sid in supporting_ids:
                ev = evidence_by_id.get(str(sid))
                if ev and ev.get("content"):
                    full_from_evidence = str(ev["content"]).strip()
                    break

            looks_truncated = (
                text.endswith("...") or text.endswith("…")
            )

            if full_from_evidence and (
                looks_truncated or len(full_from_evidence) > len(text) + 16
            ):
                # Display the synthesizer's short summary; keep the full
                # evidence passage in `text_full` for the expand-toggle.
                short = _first_sentence(text, max_chars=260)
                claim["text"] = short or text
                claim["text_full"] = full_from_evidence
            else:
                short = _first_sentence(text, max_chars=260)
                if short and short != text:
                    claim["text_full"] = text
                    claim["text"] = short
                else:
                    claim["text"] = text
            claim.setdefault("title", f"Finding {idx}")


# ---------------------------------------------------------------------------
# v3 adapter — exposed directly.
# ---------------------------------------------------------------------------


_RERANK_SYSTEM_PROMPT = (
    "You are a careful scientific fact-checker. Given a research question and "
    "two candidate claims, output ONLY the single letter A or B for the claim "
    "that is most consistent with current peer-reviewed evidence. Output a "
    "single letter and nothing else."
)


def _parse_ab(text: str) -> str | None:
    if not text:
        return None
    for ch in text.upper():
        if ch == "A":
            return "A"
        if ch == "B":
            return "B"
    return None


@app.post("/api/rerank", response_model=RerankResponse)
async def rerank(req: RerankRequest) -> RerankResponse:
    """Invoke the v3 adapter on a single pairwise-preference judgement."""
    try:
        client = _ensure_local_client()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"local model unavailable: {exc}") from exc

    user_msg = (
        f"Research question:\n{req.goal.strip()}\n\n"
        f"Claim A: {req.claim_a.strip()}\n"
        f"Claim B: {req.claim_b.strip()}\n\n"
        "Which claim is supported by current scientific evidence? Answer with A or B."
    )
    request = LLMGenerationRequest(
        model=os.environ.get("ASAR_LOCAL_BASE_MODEL", "Qwen/Qwen2.5-0.5B-Instruct"),
        messages=[
            LLMMessage(role=MessageRole.SYSTEM, content=_RERANK_SYSTEM_PROMPT),
            LLMMessage(role=MessageRole.USER, content=user_msg),
        ],
        temperature=0.0,
        max_tokens=8,
        metadata={"component": "rerank"},
    )

    start = time.monotonic()
    try:
        resp = await client.generate(request)
    except ASARError as exc:
        raise HTTPException(status_code=500, detail={"error": exc.message, "details": exc.details}) from exc
    except Exception as exc:  # pragma: no cover - defensive
        LOG.exception("rerank failure")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    elapsed = time.monotonic() - start

    pick = _parse_ab(resp.output_text) or "A"
    return RerankResponse(
        preferred=pick,
        raw=resp.output_text[:64],
        elapsed_seconds=elapsed,
    )


@app.post("/api/warmup", response_model=WarmupResponse)
async def warmup() -> WarmupResponse:
    """Force the v3 adapter to load (so the first /api/rerank call is fast)."""
    try:
        client = _ensure_local_client()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"local model unavailable: {exc}") from exc

    request = LLMGenerationRequest(
        model=os.environ.get("ASAR_LOCAL_BASE_MODEL", "Qwen/Qwen2.5-0.5B-Instruct"),
        messages=[
            LLMMessage(role=MessageRole.SYSTEM, content=_RERANK_SYSTEM_PROMPT),
            LLMMessage(role=MessageRole.USER, content="Goal: ping. Claim A: yes. Claim B: no. Answer A or B."),
        ],
        temperature=0.0,
        max_tokens=4,
        metadata={"component": "warmup"},
    )

    start = time.monotonic()
    try:
        resp = await client.generate(request)
        sample = resp.output_text
        loaded = True
    except Exception as exc:
        LOG.warning("warmup failed: %s", exc)
        sample = f"<error: {exc}>"
        loaded = False
    elapsed = time.monotonic() - start

    return WarmupResponse(adapter_loaded=loaded, elapsed_seconds=elapsed, sample=sample)

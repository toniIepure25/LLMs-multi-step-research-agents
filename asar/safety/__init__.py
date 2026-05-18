"""
Safety layer — input and output guardrails for the ASAR pipeline.

Two checks live here:

1. **Toxicity / hate / harassment** — uses Detoxify when installed, otherwise
   falls back to a deterministic keyword/regex filter. Both produce a
   `SafetyVerdict` over the same scoring surface.

2. **Prompt-injection-style instruction smuggling** — a lightweight pattern
   match for the most common manipulation phrases (e.g. "ignore previous
   instructions"). Runs on the goal text *and* on retrieved evidence
   snippets so a poisoned web/corpus result cannot hijack the synthesizer.

Both checks are deterministic when the LLM is offline (mock path) and
gracefully upgrade to Detoxify-based scoring when the optional dep is present.

Public surface:
- `SafetyVerdict`, `SafetyReport` — typed results
- `SafetyFilterProtocol` — minimal protocol
- `KeywordSafetyFilter` — always-available baseline
- `DetoxifySafetyFilter` — optional, model-backed
- `build_safety_filter` — config-driven factory
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Protocol


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SafetyVerdict:
    """Score + label for a single piece of text."""

    text_kind: str  # "goal" | "evidence" | "claim"
    text_id: str | None
    is_safe: bool
    toxicity_score: float  # [0.0, 1.0]
    injection_score: float  # [0.0, 1.0]
    reasons: tuple[str, ...] = ()
    backend: str = "keyword"

    def to_dict(self) -> dict[str, object]:
        return {
            "text_kind": self.text_kind,
            "text_id": self.text_id,
            "is_safe": self.is_safe,
            "toxicity_score": self.toxicity_score,
            "injection_score": self.injection_score,
            "reasons": list(self.reasons),
            "backend": self.backend,
        }


@dataclass(frozen=True)
class SafetyReport:
    """Aggregate safety check over goal + evidence + claims."""

    verdicts: tuple[SafetyVerdict, ...]
    blocked: bool
    overall_max_toxicity: float
    overall_max_injection: float
    backend: str

    @property
    def summary(self) -> dict[str, object]:
        return {
            "blocked": self.blocked,
            "max_toxicity": self.overall_max_toxicity,
            "max_injection": self.overall_max_injection,
            "backend": self.backend,
            "verdict_count": len(self.verdicts),
            "unsafe_count": sum(1 for v in self.verdicts if not v.is_safe),
        }

    def to_dict(self) -> dict[str, object]:
        return {
            **self.summary,
            "verdicts": [v.to_dict() for v in self.verdicts],
        }


@dataclass(frozen=True)
class SafetyConfig:
    """Tunable thresholds for the safety filter."""

    toxicity_threshold: float = 0.5
    injection_threshold: float = 0.5
    block_on_unsafe_goal: bool = True
    block_on_unsafe_evidence: bool = False  # warn-only by default — we still want to report
    block_on_unsafe_claim: bool = True


class SafetyFilterProtocol(Protocol):
    """Minimal protocol any safety filter must satisfy."""

    @property
    def backend(self) -> str: ...

    def score_toxicity(self, text: str) -> float: ...


# ---------------------------------------------------------------------------
# Keyword / regex baseline
# ---------------------------------------------------------------------------


_TOXIC_PATTERNS = [
    r"\bkill\s+(yourself|themselves|everyone)\b",
    r"\b(idiot|moron|retard|stupid)\b",
    r"\bhate\s+(you|them|him|her)\b",
    r"\bgo\s+die\b",
    r"\b(fuck|shit|bitch)\b",
    r"\bracial\s+slur\b",
    r"\b(?:bomb|kill)\s+(?:everyone|all)\b",
]

_HARM_INTENT_PATTERNS = [
    # ── Weapon / drug manufacturing ────────────────────────────────────────
    # Matches the verb+dangerous-object pair regardless of leading "how to /
    # how can I / I want to / show me / tell me" framing.  Examples caught:
    #   "how can we make a bomb"          (the original miss)
    #   "build a pipe bomb at home"
    #   "synthesize sarin"
    #   "cook some meth"
    r"\b(?:make|build|create|construct|synthesize|assemble|manufacture|"
    r"cook|brew|3d[-\s]?print)\s+(?:a|an|the|some|my|our|your)?\s*"
    r"(?:pipe[-\s]?bomb|bomb|ied|grenade|molotov|napalm|landmine|"
    r"chemical\s+weapon|nerve\s+agent|sarin|ricin|vx\s+gas|"
    r"gun|firearm|assault\s+rifle|silencer|suppressor|explosive|"
    r"meth(?:amphetamine)?|cocaine|heroin|fentanyl|crack\s+cocaine|lsd)s?\b",
    # ── Targeting a person directly ────────────────────────────────────────
    r"\bhow\s+(?:can\s+|do\s+|could\s+|should\s+|to\s+)?(?:i|we|you|one)?"
    r"\s*(?:kill|murder|poison|stab|shoot|strangle|behead|assassinate)\s+"
    r"(?:a|the|some|my|his|her|their|someone|anyone|people|everyone|"
    r"him|her|them|my\s+\w+)\b",
    # ── Acquisitive / property crime ───────────────────────────────────────
    r"\b(?:rob|robbing|burglarize|burgle|hold\s+up)\s+"
    r"(?:a|the|some|that|this)\s+"
    r"(?:bank|store|shop|gas\s+station|atm|jewelry\s+store|casino|"
    r"house|home|business)\b",
    r"\bcommit\s+(?:a\s+|an\s+)?"
    r"(?:robbery|burglary|heist|murder|arson|kidnapping|terrorism|"
    r"terror\s+attack|hate\s+crime|massacre|shooting|stabbing|"
    r"assault|fraud)\b",
    # ── Self-harm ──────────────────────────────────────────────────────────
    r"\bsuicide\s+method\b",
    r"\bhow\s+(?:to|can\s+i|do\s+i)\s+(?:kill\s+myself|commit\s+suicide|"
    r"end\s+(?:my|it\s+all))\b",
]

_INJECTION_PATTERNS = [
    r"ignore\s+(?:all\s+)?previous\s+(?:instructions|prompts|directions)",
    r"disregard\s+(?:all\s+)?(?:previous|prior)\s+instructions",
    r"forget\s+(?:everything|what\s+(?:i|you)\s+said)",
    r"system\s+prompt\s*:",
    r"new\s+instructions\s*:",
    r"you\s+are\s+now\s+(?:a|an)\s+",
    r"act\s+as\s+if\s+you\s+(?:have\s+)?no\s+restrictions",
    r"jailbreak",
    r"<\s*/?\s*(?:system|assistant)\s*>",
]


def _re_compile_all(patterns: list[str]) -> list[re.Pattern[str]]:
    return [re.compile(p, re.IGNORECASE) for p in patterns]


_TOXIC_RE = _re_compile_all(_TOXIC_PATTERNS)
_HARM_INTENT_RE = _re_compile_all(_HARM_INTENT_PATTERNS)
_INJECTION_RE = _re_compile_all(_INJECTION_PATTERNS)


class KeywordSafetyFilter:
    """Always-available deterministic baseline.

    Toxicity score is the fraction of toxic-pattern hits over the number of
    sentences (clipped to 1.0). Harm-intent hits saturate the score to 1.0.
    Injection score is the fraction of injection-pattern hits (capped at 1.0).
    """

    name = "keyword"

    @property
    def backend(self) -> str:
        return "keyword"

    def score_toxicity(self, text: str) -> float:
        if not text:
            return 0.0
        sentences = max(1, len(re.findall(r"[.!?]+", text)))
        toxic_hits = sum(1 for pattern in _TOXIC_RE if pattern.search(text))
        harm_hits = sum(1 for pattern in _HARM_INTENT_RE if pattern.search(text))
        if harm_hits > 0:
            return 1.0
        return min(1.0, toxic_hits / sentences + 0.4 * min(1, toxic_hits))

    def score_injection(self, text: str) -> float:
        if not text:
            return 0.0
        hits = sum(1 for pattern in _INJECTION_RE if pattern.search(text))
        if hits == 0:
            return 0.0
        return min(1.0, 0.4 + 0.2 * hits)


# ---------------------------------------------------------------------------
# Detoxify-backed filter (optional)
# ---------------------------------------------------------------------------


class DetoxifySafetyFilter:
    """Backed by the small Detoxify multilingual model.

    The model is loaded lazily on the first scoring call. Toxicity score is
    the max of {toxicity, severe_toxicity, identity_attack, insult, threat}.
    Injection scoring delegates to the keyword baseline because Detoxify does
    not address prompt injection at all.
    """

    name = "detoxify"

    def __init__(self, model_name: str = "original") -> None:
        self._model_name = model_name
        self._model = None
        self._fallback = KeywordSafetyFilter()

    @property
    def backend(self) -> str:
        return f"detoxify:{self._model_name}"

    def _load(self) -> None:
        if self._model is not None:
            return
        try:
            from detoxify import Detoxify  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dep
            raise RuntimeError(
                "detoxify is not installed. Run `uv sync --extra safety`."
            ) from exc
        self._model = Detoxify(self._model_name)

    def score_toxicity(self, text: str) -> float:
        if not text:
            return 0.0
        self._load()
        assert self._model is not None
        scores = self._model.predict(text)
        keys = ("toxicity", "severe_toxicity", "identity_attack", "insult", "threat")
        return float(max(scores.get(k, 0.0) for k in keys))

    def score_injection(self, text: str) -> float:
        return self._fallback.score_injection(text)


# ---------------------------------------------------------------------------
# Pipeline-facing checker
# ---------------------------------------------------------------------------


class SafetyChecker:
    """Composes a toxicity scorer with the injection scorer to produce reports."""

    def __init__(
        self,
        *,
        filter: SafetyFilterProtocol | KeywordSafetyFilter | DetoxifySafetyFilter,
        config: SafetyConfig | None = None,
    ) -> None:
        self._filter = filter
        self._config = config or SafetyConfig()
        self._keyword = KeywordSafetyFilter()

    def check_text(self, text: str, *, kind: str, text_id: str | None = None) -> SafetyVerdict:
        toxicity = float(self._filter.score_toxicity(text))
        injection = float(
            getattr(self._filter, "score_injection", self._keyword.score_injection)(text)
        )
        reasons: list[str] = []
        if toxicity >= self._config.toxicity_threshold:
            reasons.append(f"toxicity_above_{self._config.toxicity_threshold:.2f}")
        if injection >= self._config.injection_threshold:
            reasons.append(f"injection_above_{self._config.injection_threshold:.2f}")
        is_safe = not reasons
        return SafetyVerdict(
            text_kind=kind,
            text_id=text_id,
            is_safe=is_safe,
            toxicity_score=round(toxicity, 4),
            injection_score=round(injection, 4),
            reasons=tuple(reasons),
            backend=getattr(self._filter, "backend", "keyword"),
        )

    def report(
        self,
        *,
        goal: str,
        evidence: list[tuple[str, str]] | None = None,
        claims: list[tuple[str, str]] | None = None,
    ) -> SafetyReport:
        """Score the goal, all evidence snippets, and all claim texts.

        ``evidence`` is a list of ``(evidence_id, content)`` pairs.
        ``claims`` is a list of ``(claim_id, statement)`` pairs.
        """
        verdicts: list[SafetyVerdict] = [self.check_text(goal, kind="goal", text_id="goal")]
        for ev_id, text in evidence or []:
            verdicts.append(self.check_text(text, kind="evidence", text_id=ev_id))
        for claim_id, text in claims or []:
            verdicts.append(self.check_text(text, kind="claim", text_id=claim_id))

        max_tox = max((v.toxicity_score for v in verdicts), default=0.0)
        max_inj = max((v.injection_score for v in verdicts), default=0.0)

        blocked = self._should_block(verdicts)
        return SafetyReport(
            verdicts=tuple(verdicts),
            blocked=blocked,
            overall_max_toxicity=max_tox,
            overall_max_injection=max_inj,
            backend=getattr(self._filter, "backend", "keyword"),
        )

    def _should_block(self, verdicts: list[SafetyVerdict]) -> bool:
        for verdict in verdicts:
            if verdict.is_safe:
                continue
            if verdict.text_kind == "goal" and self._config.block_on_unsafe_goal:
                return True
            if verdict.text_kind == "evidence" and self._config.block_on_unsafe_evidence:
                return True
            if verdict.text_kind == "claim" and self._config.block_on_unsafe_claim:
                return True
        return False


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def build_safety_filter(
    backend: str | None = None,
    config: SafetyConfig | None = None,
) -> SafetyChecker:
    """Build a safety checker from a backend name.

    Resolution order:
    1. Explicit ``backend`` arg.
    2. ``ASAR_SAFETY_BACKEND`` env var.
    3. Default: ``keyword``.
    """
    resolved = (backend or os.environ.get("ASAR_SAFETY_BACKEND") or "keyword").strip().lower()
    if resolved in {"keyword", "regex", "baseline"}:
        return SafetyChecker(filter=KeywordSafetyFilter(), config=config)
    if resolved == "detoxify":
        return SafetyChecker(filter=DetoxifySafetyFilter(), config=config)
    raise ValueError(f"Unknown safety backend: {resolved!r}")

# v1 Minimal Architecture

> Parent: [PROJECT_DOSSIER.md § Roadmap](../../PROJECT_DOSSIER.md#15-roadmap)
> Frozen historical baseline: [experiments/notes/v0_tier1_eval_set_004.md](../../experiments/notes/v0_tier1_eval_set_004.md)
> Active experimental v1-minimal baseline: [experiments/notes/v1_tier1_eval_set_004.md](../../experiments/notes/v1_tier1_eval_set_004.md)
> See also: [v0-canonical-architecture.md](v0-canonical-architecture.md) · [tasks/v1_minimal_plan.md](../../tasks/v1_minimal_plan.md) · [v1_1-grounded-selection-architecture.md](v1_1-grounded-selection-architecture.md) · [v1_2-mechanism-bundling-architecture.md](v1_2-mechanism-bundling-architecture.md) · [v1_3-mechanism-sketching-architecture.md](v1_3-mechanism-sketching-architecture.md) · [v1_4-slot-grounded-drafting-architecture.md](v1_4-slot-grounded-drafting-architecture.md) · [../../tasks/handoff/2026-03-21_v1_1_exploratory_freeze.md](../../tasks/handoff/2026-03-21_v1_1_exploratory_freeze.md) · [../../tasks/handoff/2026-03-25_v1_2_exploratory_freeze.md](../../tasks/handoff/2026-03-25_v1_2_exploratory_freeze.md) · [../../tasks/handoff/2026-03-26_v1_3_exploratory_freeze.md](../../tasks/handoff/2026-03-26_v1_3_exploratory_freeze.md) · [../../tasks/handoff/2026-03-31_v1_4_exploratory_freeze.md](../../tasks/handoff/2026-03-31_v1_4_exploratory_freeze.md)

This document defines the smallest sensible step beyond frozen v0. It describes
the minimum architectural delta that was implemented to address the main
structural limitation discovered in the v0 live baseline and probe cycle.

## Status

- v1-minimal has now been implemented and evaluated through focused probes plus full live Tier 1 reruns
- the current active experimental baseline is [v1_tier1_eval_set_004.md](../../experiments/notes/v1_tier1_eval_set_004.md)
- narrow v1-minimal tuning should stop for now
- future work should build intentionally from this baseline rather than reopening ad hoc tuning loops by default
- the exploratory v1.1 grounded-selection branch was not promoted after focused live probing and should not replace this baseline
- the exploratory v1.2 mechanism-bundling branch was also not promoted after focused mocked and live probing and should not replace this baseline
- the exploratory v1.3 mechanism-sketching branch was also not promoted after mocked checkpoints and a focused live 2008 probe and should not replace this baseline
- the exploratory v1.4 slot-grounded drafting branch was also not promoted after mocked checkpoints and a focused live 2008 probe and should not replace this baseline
- the next step should be a new consciously scoped design step informed by, but not automatically continuing, v1.1, v1.2, v1.3, or v1.4

## 1. Why v0 is frozen

v0 is frozen because:

- the pipeline now works end-to-end in a repeatable live configuration
- `v0_tier1_eval_set_004` is a credible reference live baseline
- repeated micro-tuning of v0 reached diminishing returns
- later v0 probes showed that single-pass synthesis is trying to do too much at once

Concretely, v0 already supports:

- structured planning
- step-wise execution
- typed evidence accumulation
- weak deterministic verification
- experiment logging and live baseline comparison

The remaining bottleneck is not "add one more prompt tweak." The remaining
bottleneck is architectural.

## 2. Observed limitation of single-pass synthesis

The current `SimpleSynthesizer` must do all of the following in one step:

1. generate candidate claims from evidence
2. decide which claims are worth keeping
3. resolve near-duplicates
4. choose the right level of specificity
5. phrase the selected claims cleanly

This creates unstable tradeoffs:

- cleaner phrasing can reduce support quality
- stronger support can survive as awkward phrasing
- distinct claims can be merged or dropped too early
- selection and phrasing interfere with each other

The live 2008 probes showed the problem clearly:

- `v0_2008_probe_006` improved phrasing
- `v0_2008_probe_007` improved phrasing further but lost support quality and claim count
- `v0_2008_probe_008` removed over-specific wording but still failed to recover groundedness and distinct mechanism coverage

The core issue is that claim generation and claim selection are currently the
same step.

## 3. Minimal v1 change

v1 introduces one new architectural capability only:

- a support-aware claim selection stage after candidate claim generation

Everything else remains as close to v0 as possible.

This means:

- planning stays the same
- execution stays the same
- memory stays the same
- verification stays the same
- evaluation stays the same
- orchestration changes only enough to call generation first, then selection

## 4. Exact new component for v1

The new component is:

- `ClaimSelector`

The existing `SimpleSynthesizer` is no longer responsible for both generation
and selection. In v1 minimal, it becomes the candidate claim generator role.

Proposed deliberation split:

- `SimpleSynthesizer` or successor generation mode:
  - input: `list[EvidenceItem]` + goal context
  - output: a small candidate claim set
- `ClaimSelector`:
  - input: candidate claims + evidence + goal context
  - output: final selected claims for the `DecisionPacket`

The architectural novelty is the selector, not a full redesign of the
deliberation layer.

## 5. Proposed data flow

v0:

```text
EvidenceItem[] -> SimpleSynthesizer -> DecisionPacket -> EvidenceChecker
```

v1 minimal:

```text
EvidenceItem[]
  -> candidate claim generation
  -> ClaimSelector
  -> DecisionPacket
  -> EvidenceChecker
```

More explicitly:

```text
Research Goal
  -> planning
  -> execution
  -> memory
  -> candidate claim generation
  -> ClaimSelector
  -> verification
  -> evaluation
  -> ResearchOutput
```

Selector priorities:

- stronger evidence support
- higher question relevance
- non-duplication
- sufficient specificity without unsupported overreach

## 6. Expected benefits

Expected benefits of the minimal split:

- cleaner causal phrasing without sacrificing support quality
- fewer cases where a brittle specific claim replaces a stronger supported one
- better preservation of distinct mechanisms like securitization, OTC
  derivatives, and Glass-Steagall when the evidence supports them separately
- lower sensitivity to single-pass prompt variance
- clearer debug surface: generation failures and selection failures can be
  diagnosed separately

## 7. Risks

The minimal v1 step still has risks:

- one more component means one more typed boundary to maintain
- poorly designed selection logic could just move instability downstream
- selector heuristics could over-prune or over-favor lexical overlap
- candidate generation could become too verbose without tight caps

Risk mitigation:

- keep candidate set small
- keep selection deterministic first
- compare directly against `v0_tier1_eval_set_004`
- validate on the same live questions before expanding scope

## 8. Evaluation plan for v1

v1 should be evaluated against the current reference live baseline:

- baseline: [experiments/notes/v0_tier1_eval_set_004.md](../../experiments/notes/v0_tier1_eval_set_004.md)

Primary success checks:

- 2008-style causal claims stay directly causal
- groundedness does not regress
- distinct supported mechanisms are preserved
- evidence utilization does not collapse
- dot-com retrieval cleanliness from v0 remains intact

Suggested evaluation order:

1. mocked unit tests for selector behavior
2. mocked end-to-end integration on the canonical 2008 question
3. focused live 2008 probe
4. full 3-question Tier 1 rerun only if the focused probe is stable

Current outcome:

- frozen historical v0 baseline remains [v0_tier1_eval_set_004.md](../../experiments/notes/v0_tier1_eval_set_004.md)
- active experimental v1-minimal baseline is now [v1_tier1_eval_set_004.md](../../experiments/notes/v1_tier1_eval_set_004.md)
- v1-minimal improved overall enough to justify stopping further narrow tuning in this phase

## 9. What is explicitly still postponed

The following are still out of scope for this first v1 step:

- grounding and `CitationRecord` handling
- re-planning
- parallel execution
- multi-perspective debate
- advanced memory compression
- broad verification redesign
- benchmark expansion
- giant roadmap restructuring

## 10. Minimality Rule

This document is intentionally narrow.

If a proposed v1 implementation requires:

- multiple new architectural capabilities
- new live providers
- a redesigned verification system
- new orchestration complexity beyond generation -> selection

then it is no longer the minimal v1 described here and should be deferred.

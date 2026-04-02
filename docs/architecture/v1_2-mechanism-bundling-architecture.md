# v1.2 Mechanism Bundling Architecture

> Parent: [PROJECT_DOSSIER.md § Roadmap](../../PROJECT_DOSSIER.md#15-roadmap)
> Frozen historical baseline: [experiments/notes/v0_tier1_eval_set_004.md](../../experiments/notes/v0_tier1_eval_set_004.md)
> Active experimental v1-minimal baseline: [experiments/notes/v1_tier1_eval_set_004.md](../../experiments/notes/v1_tier1_eval_set_004.md)
> Exploratory evidence: [v1_1-grounded-selection-architecture.md](v1_1-grounded-selection-architecture.md) · [../../tasks/handoff/2026-03-21_v1_1_exploratory_freeze.md](../../tasks/handoff/2026-03-21_v1_1_exploratory_freeze.md)
> Build plan: [../../tasks/v1_2_mechanism_bundling_plan.md](../../tasks/v1_2_mechanism_bundling_plan.md)
> Freeze note: [../../tasks/handoff/2026-03-25_v1_2_exploratory_freeze.md](../../tasks/handoff/2026-03-25_v1_2_exploratory_freeze.md)

This document records the consciously scoped `v1.2` exploration that was tried
beyond the active v1-minimal baseline. It kept the current pipeline shape
intact and introduced one new capability only: deterministic evidence bundling
into compact mechanism-oriented slices before final claim generation and
selection.

## Status

- explored in code through a local deterministic `MechanismBundler` inside `deliberation`
- validated through mocked bundling checkpoints and end-to-end thin-2008 coverage
- tested in focused live probes:
  - [v1_2_2008_probe_002.md](../../experiments/notes/v1_2_2008_probe_002.md)
  - [v1_2_great_depression_probe_001.md](../../experiments/notes/v1_2_great_depression_probe_001.md)
  - [v1_2_dotcom_probe_001.md](../../experiments/notes/v1_2_dotcom_probe_001.md)
- not promoted: the focused live probes produced useful evidence, but did not show clear overall superiority to the active v1-minimal baseline
- subsequent v1.3 mechanism-sketching exploration also remained exploratory and did not change the active baseline decision
- subsequent v1.4 slot-grounded drafting exploration also remained exploratory and did not change the active baseline decision
- current status: exploratory branch only, frozen for now, not the active baseline and not the default path forward without a new design decision

## 1. Why v1-minimal remains the correct active baseline

v1-minimal is the correct active baseline because it is the strongest live
configuration that has actually cleared a full Tier 1 comparison bar.

What it already proved:

- direct-causal answers are more stable than frozen v0 on the highest-value live questions
- candidate generation plus deterministic selection is a better architectural split than single-pass synthesis
- the current live path can preserve groundedness and question fidelity without adding orchestration complexity

The active baseline is therefore still:

- [v1_tier1_eval_set_004.md](../../experiments/notes/v1_tier1_eval_set_004.md)

## 2. What v1.1 taught us

v1.1 tested a plausible next idea: add support attribution before final
selection.

What worked:

- mocked regressions improved weak-support-vs-strong-support behavior
- mocked regressions improved diversity-aware composition behavior
- the idea remains promising as design evidence

What failed in live use:

- focused 2008 live behavior regressed against the active v1-minimal baseline
- support attribution was too brittle around lexical and family variation
- downstream scoring could not reliably rescue unstable or weakly framed candidate sets

The key lesson is not that grounding-aware selection is useless. The key lesson
is that adding more downstream scoring pressure is not the most promising next
step while candidate framing and evidence compression remain unstable under the
current live budget.

## 3. The next bottleneck after v1-minimal and exploratory v1.1

The most likely next bottleneck is budget-sensitive evidence-to-claim shaping.

Observed pattern across v1-minimal and exploratory v1.1:

- live candidate sets are sensitive to wording and token budget pressure
- mechanism diversity can collapse before selection has enough good options
- support scoring becomes brittle when freeform claim wording drifts away from the evidence wording that generated it
- several questions improve when evidence is implicitly grouped by mechanism family, but the current path does not make that grouping explicit

In short: the next bottleneck is not only claim scoring. It is the lack of a
small explicit intermediate representation between raw evidence accumulation and
freeform claim wording.

## 4. Single new capability for v1.2

The next step should introduce one new capability only:

- `MechanismBundler`

`MechanismBundler` would deterministically group and compress `EvidenceItem`s
into a small set of mechanism-oriented evidence bundles before final claim
surface realization.

Responsibilities:

- cluster relevant evidence into a few compact mechanism-family bundles
- keep bundle support explicit and inspectable
- preserve distinct mechanism families when support comes from different sources
- reduce prompt-budget pressure by passing bundled evidence rather than the whole flat evidence list into the final claim-generation step

This is more promising than continuing v1.1 tuning directly because it attacks
an upstream instability that support scoring alone could not fix.

## 5. Proposed data flow

Current v1-minimal:

```text
EvidenceItem[]
  -> candidate claim generation
  -> ClaimSelector
  -> DecisionPacket
  -> EvidenceChecker
```

Proposed v1.2:

```text
EvidenceItem[]
  -> MechanismBundler
  -> bundled candidate claim generation
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
  -> mechanism bundling
  -> bundled claim generation
  -> deterministic claim selection
  -> verification
  -> evaluation
  -> ResearchOutput
```

Minimality rule:

- keep the bundler local to `deliberation` first
- do not activate the full `grounding` layer
- do not introduce `CitationRecord` rollout yet
- do not redesign orchestration

## 6. Expected benefits

Expected gains from this step:

- more stable mechanism coverage under the live token budget
- less candidate undercoverage before selection
- better completeness without depending on brittle freeform lexical overlap alone
- more consistent evidence utilization because final claims are generated from compact supported bundles instead of a noisy flat pool
- simpler debugging surface:
  - bundle construction failure
  - bundled generation failure
  - selection failure
  become easier to separate

## 7. Risks

Risks of this step:

- bundling heuristics may over-merge distinct mechanism families
- poorly chosen bundle caps could hide useful minority evidence
- if bundle labels become too canonical too early, phrasing quality may regress into rigid or generic wording
- if implemented too broadly, this could accidentally become an early grounding-layer rewrite

Risk controls:

- keep bundling deterministic first
- keep the number of bundles small and inspectable
- compare directly against [v1_tier1_eval_set_004.md](../../experiments/notes/v1_tier1_eval_set_004.md)
- test focused coverage questions before any full-set rerun

## 8. What is explicitly postponed

Still postponed after v1.2:

- full `grounding` layer activation
- `CitationRecord`-heavy citation normalization
- re-planning
- parallel execution
- debate / multi-perspective deliberation
- advanced memory compression
- broad verification redesign
- benchmark-suite expansion as a prerequisite for the first pass

## 9. Why it was not promoted

What worked:

- mocked checkpoints showed that mechanism bundles can stabilize thin candidate-generation inputs
- the focused live 2008 probe was viable, grounded, and complete enough to evaluate in real conditions
- the focused live Great Depression probe showed a meaningful diversity gain by bringing back a monetary / banking family
- the focused live dot-com probe stayed complete and grounded, and wrong-domain crash / vehicle noise stayed gone

What failed the promotion bar:

- there was no clear overall superiority to [v1_tier1_eval_set_004.md](../../experiments/notes/v1_tier1_eval_set_004.md)
- the focused live 2008 result was viable but mixed, not clearly better in mechanism quality than the active baseline
- the focused live Great Depression result was promising on diversity, but still not cleanly stronger overall
- the focused live dot-com result did not improve the strongest prior mechanism organization and lost the regulation family

Conclusion:

- v1.2 remains promising as design evidence
- but it is exploratory only and should not replace [v1_tier1_eval_set_004.md](../../experiments/notes/v1_tier1_eval_set_004.md) as the active runtime baseline

## 10. Acceptance shape for the proposal

This proposal is successful if implementation can remain:

- one new capability only
- mostly inside `deliberation`
- compatible with current v1-minimal orchestration
- testable with mocked evidence/candidate sets before live reruns

If the implementation requires:

- multiple new runtime stages
- protocol churn across the pipeline
- a full grounding subsystem
- broad orchestration changes

then it is no longer the intended v1.2 step and should be deferred.

# v1.4 Slot-Grounded Drafting Architecture

> Parent: [PROJECT_DOSSIER.md § Roadmap](../../PROJECT_DOSSIER.md#15-roadmap)
> Frozen historical baseline: [experiments/notes/v0_tier1_eval_set_004.md](../../experiments/notes/v0_tier1_eval_set_004.md)
> Active experimental v1-minimal baseline: [experiments/notes/v1_tier1_eval_set_004.md](../../experiments/notes/v1_tier1_eval_set_004.md)
> Exploratory evidence: [v1_1-grounded-selection-architecture.md](v1_1-grounded-selection-architecture.md) · [v1_2-mechanism-bundling-architecture.md](v1_2-mechanism-bundling-architecture.md) · [v1_3-mechanism-sketching-architecture.md](v1_3-mechanism-sketching-architecture.md)
> Freeze notes: [../../tasks/handoff/2026-03-21_v1_1_exploratory_freeze.md](../../tasks/handoff/2026-03-21_v1_1_exploratory_freeze.md) · [../../tasks/handoff/2026-03-25_v1_2_exploratory_freeze.md](../../tasks/handoff/2026-03-25_v1_2_exploratory_freeze.md) · [../../tasks/handoff/2026-03-26_v1_3_exploratory_freeze.md](../../tasks/handoff/2026-03-26_v1_3_exploratory_freeze.md) · [../../tasks/handoff/2026-03-31_v1_4_exploratory_freeze.md](../../tasks/handoff/2026-03-31_v1_4_exploratory_freeze.md)
> Build plan: [../../tasks/v1_4_slot_grounded_drafting_plan.md](../../tasks/v1_4_slot_grounded_drafting_plan.md)

This document records the consciously scoped `v1.4` exploration that was tried
beyond the active v1-minimal baseline. It introduced one new capability only:
slot-grounded mechanism drafting before final claim selection.

## Status

- explored in code through a local deterministic `MechanismSlotBuilder` plus slot-grounded prompt serialization inside `SimpleSynthesizer`
- validated through mocked thin-2008 slot-preservation checkpoints and one end-to-end mocked slot-grounded deliberation checkpoint
- tested in a focused live 2008 probe: [v1_4_2008_probe_001.md](../../experiments/notes/v1_4_2008_probe_001.md)
- not promoted: the live 2008 result was viable and utilization-friendly, but it did not beat the active v1-minimal baseline on groundedness, verification quality, or distinct third-family coverage
- operational issue observed: the focused live 2008 probe completed under the wrong artifact directory (`v0_live_baseline_001d` instead of the requested `v1_4_2008_probe_001`)
- current status: exploratory branch only, frozen for now, not the active baseline and not the default path forward without a new design decision

## 1. Why v1-minimal remains the correct active baseline

v1-minimal remains the correct active baseline because it is still the
strongest live configuration that has cleared a full Tier 1 comparison bar.

What it already proved:

- candidate generation plus deterministic selection is better than v0 single-pass synthesis
- direct-causal answer quality improved on the highest-value live questions
- the current runtime shape can preserve groundedness and question fidelity without added orchestration complexity

The active runtime comparison point remains:

- [v1_tier1_eval_set_004.md](../../experiments/notes/v1_tier1_eval_set_004.md)

## 2. What v1.1 taught us

v1.1 explored support-aware selection through explicit support attribution.

What worked:

- mocked regressions improved weak-support filtering
- mocked regressions improved diversity-aware selection
- the idea remains useful as evidence that support provenance matters

What failed:

- live 2008 behavior regressed against the active baseline before partial recovery
- downstream support scoring was too brittle around lexical and mechanism-family variation
- selection pressure alone could not reliably rescue unstable candidate sets

Lesson:

- support-aware selection matters, but it acts too late if the candidate surface
  is already unstable

## 3. What v1.2 taught us

v1.2 explored deterministic mechanism bundling before final claim generation.

What worked:

- mocked checkpoints showed that pre-claim structure can stabilize thin evidence
- Great Depression live behavior showed a meaningful diversity gain
- live probing confirmed that earlier structure can be viable under real budget constraints

What failed:

- deterministic bundles alone were not clearly superior overall to v1-minimal
- 2008 remained mixed on mechanism quality
- dot-com mechanism organization did not clearly improve

Lesson:

- structure earlier than final selection helps
- but bundling alone is too coarse and rigid to control final mechanism wording

## 4. What v1.3 taught us

v1.3 explored sketch-first prompting before final claim wording.

What worked:

- mocked checkpoints showed that sketch-first structure can preserve thin-evidence mechanism separation
- the focused live 2008 probe stayed viable, grounded, and utilization-friendly

What failed:

- the live 2008 result did not beat the active v1-minimal baseline on mechanism quality
- explicit OTC-derivatives wording disappeared
- mechanism choice and final phrasing still drifted even when earlier structure existed
- the live probe also revealed an operational artifact-routing bug, which reinforces the need to keep the next step compact and easy to evaluate

Lesson:

- sketch-first prompting is closer to the right shape than downstream scoring or bundling alone
- but the final drafting step is still too free to rediscover or blur mechanism families

## 5. The next bottleneck after v1-minimal, v1.1, v1.2, and v1.3

The next bottleneck is uncontrolled mechanism realization between upstream
structure and final claim wording.

Observed pattern across the active baseline and the exploratory branches:

- raw evidence is too noisy and budget-sensitive to feed directly into final claim wording
- downstream selection is too late to repair bad or drifting candidate surfaces
- upstream bundling helps, but still leaves the LLM to rediscover family boundaries
- sketch-first prompting preserves structure better, but still allows final wording to drift into broader or weaker mechanisms

In short: the system still lacks a compact, explicit object that says:

- this is the mechanism family we intend to preserve
- these are the evidence IDs grounding it
- this is the target event anchor
- this is the drafting scope for the next claim

before the LLM turns it into surface text.

## 6. Single new capability for v1.4

The next step should introduce one new capability only:

- slot-grounded mechanism drafting

This means adding a small internal `MechanismSlot` representation plus a narrow
slot-building step before final claim wording.

Each slot should carry a compact grounded structure, for example:

- `slot_id`
- canonical mechanism family label
- supporting evidence IDs
- compact grounded rationale
- target-event anchor
- optional deterministic diversity or confidence metadata

Why this was more promising than continuing v1.1, v1.2, or v1.3 directly:

- it acts earlier than selector scoring, where v1.1 was too brittle
- it is more explicit than deterministic bundles, where v1.2 was too coarse
- it is stricter than sketch-first prompting, where v1.3 still let the final wording stage rediscover or blur mechanism families
- it narrows the downstream LLM role:
  - not "find the mechanisms again"
  - but "turn these already-grounded slots into short direct-causal claims"

Minimality rule:

- keep slots internal to `deliberation` first
- do not introduce a public schema unless implementation pressure proves it is necessary
- do not activate the full `grounding` layer
- do not redesign orchestration

## 7. Proposed data flow

Current v1-minimal:

```text
EvidenceItem[]
  -> candidate claim generation
  -> ClaimSelector
  -> DecisionPacket
  -> EvidenceChecker
```

Proposed v1.4:

```text
EvidenceItem[]
  -> MechanismSlotBuilder
  -> slot-grounded claim drafting
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
  -> mechanism slot construction
  -> bounded slot-grounded claim drafting
  -> deterministic claim selection
  -> verification
  -> evaluation
  -> ResearchOutput
```

Expected drafting rule in the first pass:

- one slot should draft at most one short direct-causal claim
- drafted claims should preserve the slot's target-event anchor and supporting evidence IDs
- `ClaimSelector` should remain mostly stable in the first pass

## 8. Expected benefits

Expected gains from this step:

- more stable mechanism preservation before final wording
- less family drift between intermediate structure and final claims
- cleaner direct-causal phrasing because the drafting step has a narrower job
- better evidence organization without depending on full grounding rollout
- better mocked-test surface:
  - slot construction failure
  - slot-to-claim drafting failure
  - final selection failure
  become easier to diagnose separately

## 9. Risks

Risks of this step:

- the slot layer could become a hidden schema expansion if it grows too much
- overly canonical slot labels could erase useful nuance or over-merge nearby mechanisms
- slot-grounded drafting could become too rigid and hurt phrasing quality
- target-event anchors may still drift if the drafting prompt contract is loose
- provider timeout sensitivity and occasional artifact-routing bugs remain operational realities, so the design must keep prompts bounded and evaluation simple

Risk controls:

- keep the slot shape small and internal
- cap slot count tightly
- require explicit supporting evidence IDs and target anchors in every slot
- compare directly against [v1_tier1_eval_set_004.md](../../experiments/notes/v1_tier1_eval_set_004.md)
- use mocked regressions before any live probes

## 10. What is explicitly postponed

Still postponed after v1.4:

- full `grounding` layer activation
- `CitationRecord`-heavy citation normalization
- knowledge graphs
- re-planning
- parallel execution
- debate / multi-perspective deliberation
- advanced memory compression
- broad verification redesign
- broad operational hardening beyond narrow bug fixes required to run focused probes

## 11. Why it was not promoted

What worked:

- mocked checkpoints showed that slot-grounded structure can preserve thin-evidence mechanism separation before final wording
- the focused live 2008 probe completed successfully and remained viable in real conditions
- the live 2008 result kept `3` claims, preserved OTC derivatives, and materially improved evidence utilization

What failed the promotion bar:

- there was no clear overall superiority to [v1_tier1_eval_set_004.md](../../experiments/notes/v1_tier1_eval_set_004.md)
- groundedness regressed from the active v1-minimal 2008 baseline to `0.6667`
- one claim verified as `insufficient`
- the final set duplicated the housing-finance family instead of clearly improving distinct third-family coverage

Operational issue:

- the live 2008 probe wrote artifacts under `v0_live_baseline_001d` instead of the requested `v1_4_2008_probe_001`
- this should be treated as a recurring artifact-routing / output-dir bug in the live demo path and not as intentional baseline naming

Conclusion:

- v1.4 remains promising as design evidence
- but it is exploratory only and should not replace [v1_tier1_eval_set_004.md](../../experiments/notes/v1_tier1_eval_set_004.md) as the active runtime baseline

## 12. Acceptance shape for the proposal

This proposal is successful if implementation can remain:

- one new capability only
- mostly inside `deliberation`
- compatible with current v1-minimal orchestration
- testable with mocked regressions before live reruns

Promotion bar:

- focused live probes must show no clear regression versus [v1_tier1_eval_set_004.md](../../experiments/notes/v1_tier1_eval_set_004.md)
- at least one focused question should show a clear structural gain in mechanism fidelity, completeness, or wording stability
- the result must be promising enough to justify a first full Tier 1 comparison

If the implementation requires:

- multiple new runtime stages
- protocol churn across the pipeline
- a public schema rollout
- a full grounding subsystem
- broad orchestration changes

then it is no longer the intended v1.4 step and should be deferred.

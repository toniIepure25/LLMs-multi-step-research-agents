# v1.3 Mechanism Sketching Architecture

> Parent: [PROJECT_DOSSIER.md § Roadmap](../../PROJECT_DOSSIER.md#15-roadmap)
> Frozen historical baseline: [experiments/notes/v0_tier1_eval_set_004.md](../../experiments/notes/v0_tier1_eval_set_004.md)
> Active experimental v1-minimal baseline: [experiments/notes/v1_tier1_eval_set_004.md](../../experiments/notes/v1_tier1_eval_set_004.md)
> Exploratory evidence: [v1_1-grounded-selection-architecture.md](v1_1-grounded-selection-architecture.md) · [v1_2-mechanism-bundling-architecture.md](v1_2-mechanism-bundling-architecture.md)
> Freeze notes: [../../tasks/handoff/2026-03-21_v1_1_exploratory_freeze.md](../../tasks/handoff/2026-03-21_v1_1_exploratory_freeze.md) · [../../tasks/handoff/2026-03-25_v1_2_exploratory_freeze.md](../../tasks/handoff/2026-03-25_v1_2_exploratory_freeze.md) · [../../tasks/handoff/2026-03-26_v1_3_exploratory_freeze.md](../../tasks/handoff/2026-03-26_v1_3_exploratory_freeze.md)
> Build plan: [../../tasks/v1_3_mechanism_sketching_plan.md](../../tasks/v1_3_mechanism_sketching_plan.md)

This document records the consciously scoped `v1.3` exploration that was tried
beyond the active v1-minimal baseline. It introduced one new capability only:
evidence-grounded mechanism sketching before final claim wording and selection.

## Status

- explored in code through a local deterministic `MechanismSketcher` plus sketch-first prompt serialization inside `SimpleSynthesizer`
- validated through mocked thin-2008 sketch-preservation checkpoints and one end-to-end mocked sketch-first deliberation checkpoint
- tested in a focused live 2008 probe: [v1_3_2008_probe_001.md](../../experiments/notes/v1_3_2008_probe_001.md)
- not promoted: the live 2008 result was viable, grounded, and utilization-friendly, but it did not beat the active v1-minimal baseline on mechanism quality
- operational issue observed: the focused live 2008 probe completed under the wrong artifact directory (`v0_live_baseline_001` instead of the requested `v1_3_2008_probe_001`)
- subsequent v1.4 slot-grounded drafting exploration also remained exploratory and did not change the active baseline decision
- current status: exploratory branch only, frozen for now, not the active baseline and not the default path forward without a new design decision

## 1. Why v1-minimal remains the correct active baseline

v1-minimal remains the correct active baseline because it is still the strongest
live configuration that has cleared a full Tier 1 comparison bar.

What it already proved:

- candidate generation plus deterministic selection is better than v0 single-pass synthesis
- direct-causal answer quality improved on the highest-value live questions
- the current runtime shape can preserve groundedness and question fidelity without added orchestration complexity

The active runtime comparison point is still:

- [v1_tier1_eval_set_004.md](../../experiments/notes/v1_tier1_eval_set_004.md)

## 2. What v1.1 taught us

v1.1 explored support-aware selection through explicit support attribution.

What worked:

- mocked regressions showed better weak-support filtering
- mocked regressions showed better diversity-aware selection
- the idea remains useful as evidence that support provenance matters

What failed:

- live 2008 behavior regressed against the active baseline before partial recovery
- downstream support scoring was too brittle around lexical and mechanism-family variation
- selection pressure alone could not reliably rescue unstable candidate sets

Lesson:

- support-aware scoring is useful, but it is too late in the pipeline to be the
  next primary lever when the candidate surface itself is unstable

## 3. What v1.2 taught us

v1.2 explored deterministic mechanism bundling before final claim generation.

What worked:

- mocked checkpoints showed that pre-claim structure can stabilize thin evidence
- Great Depression live behavior showed a meaningful diversity gain
- 2008 and dot-com live probing confirmed that upstream structure can be viable under live constraints

What failed:

- deterministic bundles alone were not clearly superior overall to v1-minimal
- 2008 remained mixed on mechanism quality
- dot-com completeness by count held, but mechanism organization did not clearly improve
- hardcoded bundle heuristics were still too rigid to be the whole answer

Lesson:

- earlier structure helps more than downstream scoring alone
- but deterministic bundling by itself is not flexible enough to reliably produce the best final mechanism set

## 4. The next bottleneck after v1-minimal, v1.1, and v1.2

The next bottleneck is the missing small structured intermediate representation
between evidence collection and freeform final claim wording.

Observed pattern across the current baseline and both exploratory branches:

- raw evidence is too noisy and budget-sensitive to feed directly into the final claim surface step
- downstream scoring is too brittle if the freeform candidates are already unstable
- deterministic bundling helps, but is still too rigid when mechanism boundaries are fuzzy or evidence wording varies
- the system still lacks a compact, inspectable object representing:
  - the candidate mechanism family
  - the evidence IDs that support it
  - the intended causal angle
  before final claim wording

In short: the next bottleneck is not just support scoring or bundling. It is the
absence of an explicit evidence-grounded mechanism sketch layer inside
deliberation.

## 5. Single new capability for v1.3

The next step should introduce one new capability only:

- `MechanismSketcher`

`MechanismSketcher` would produce a small set of evidence-grounded mechanism
sketches before final claim realization.

Each sketch should be a compact internal object, for example:

- mechanism family label
- direct causal angle
- supporting evidence IDs
- optional support-strength note
- optional "do not merge with" hint for nearby families

Minimality rule:

- keep sketches internal to `deliberation` first
- do not introduce a public schema unless implementation pressure proves it is necessary
- do not turn this into a full `CitationRecord` or grounding rollout
- allow reuse of existing deterministic bundling as a helper, but make sketching the new capability

Why this is more promising than continuing v1.1 or v1.2 directly:

- it acts earlier than selector scoring, where v1.1 was too brittle
- it is more flexible than deterministic bundles alone, where v1.2 was too rigid
- it gives final claim realization a compact structured object instead of a raw flat evidence pool or purely heuristic bundle labels

## 6. Proposed data flow

Current v1-minimal:

```text
EvidenceItem[]
  -> candidate claim generation
  -> ClaimSelector
  -> DecisionPacket
  -> EvidenceChecker
```

Proposed v1.3:

```text
EvidenceItem[]
  -> MechanismSketcher
  -> final claim realization from sketches
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
  -> evidence-grounded mechanism sketching
  -> final claim realization from sketches
  -> deterministic claim selection
  -> verification
  -> evaluation
  -> ResearchOutput
```

Possible internal-first implementation:

- `MechanismSketcher` may call or reuse `MechanismBundler` internally
- `SimpleSynthesizer` may ask the LLM for a small set of structured sketches before final claim wording
- `ClaimSelector` remains mostly stable in the first pass

## 7. Expected benefits

Expected gains from this step:

- more stable mechanism-family coverage before final claim wording
- cleaner separation between "what mechanism are we keeping" and "how do we phrase it"
- less lexical brittleness than v1.1 support attribution alone
- less heuristic rigidity than v1.2 deterministic bundling alone
- better mocked-test surface:
  - sketch extraction failure
  - claim realization failure
  - final selection failure
  become easier to diagnose separately

## 8. Risks

Risks of this step:

- the sketch layer could become a hidden schema expansion if it grows too much
- LLM-produced sketches could drift into vague restatements instead of stable mechanism objects
- sketch-to-claim realization might duplicate errors rather than reduce them if the sketch contract is loose
- if implemented too broadly, this could accidentally become a premature grounding subsystem

Risk controls:

- keep the sketch shape small and internal
- cap the number of sketches tightly
- require explicit supporting evidence IDs in every sketch
- compare directly against [v1_tier1_eval_set_004.md](../../experiments/notes/v1_tier1_eval_set_004.md)
- use mocked regressions before any live probes

## 9. What is explicitly postponed

Still postponed after v1.3:

- full `grounding` layer activation
- `CitationRecord`-heavy citation normalization
- knowledge graphs
- re-planning
- parallel execution
- debate / multi-perspective deliberation
- advanced memory compression
- broad verification redesign
- benchmark-suite expansion as a prerequisite for the first pass

## 10. Why it was not promoted

What worked:

- mocked checkpoints showed that sketch-first structure can preserve thin-evidence mechanism separation before final wording
- the focused live 2008 probe completed successfully and remained viable in real conditions
- the live 2008 result kept `3` claims, `groundedness=1.0`, `supported=3`, and materially stronger evidence utilization than the active v1-minimal 2008 baseline

What failed the promotion bar:

- there was no clear overall superiority to [v1_tier1_eval_set_004.md](../../experiments/notes/v1_tier1_eval_set_004.md)
- the focused live 2008 result lost the explicit OTC-derivatives family
- the lead deregulation claim broadened relative to the stronger v1-minimal 2008 mechanism mix
- the result was healthier by core metrics than by mechanism quality, which was not enough to justify promotion

Operational issue:

- the live 2008 probe wrote artifacts under `v0_live_baseline_001` instead of the requested `v1_3_2008_probe_001`
- this should be treated as an artifact-routing / output-dir bug and not as intentional naming or baseline behavior

Conclusion:

- v1.3 remains promising as design evidence
- but it is exploratory only and should not replace [v1_tier1_eval_set_004.md](../../experiments/notes/v1_tier1_eval_set_004.md) as the active runtime baseline

## 11. Acceptance shape for the proposal

This proposal would be successful if implementation can remain:

- one new capability only
- mostly inside `deliberation`
- compatible with current v1-minimal orchestration
- testable with mocked evidence-first regressions before live reruns

Promotion bar:

- focused live probes must show no clear regression versus [v1_tier1_eval_set_004.md](../../experiments/notes/v1_tier1_eval_set_004.md)
- at least one focused question should show a clear structural gain in mechanism quality, completeness, or support organization
- the result must be promising enough to justify a first full Tier 1 comparison

If the implementation requires:

- multiple new runtime stages
- protocol churn across the pipeline
- a public schema rollout
- a full grounding subsystem
- broad orchestration changes

then it is no longer the intended v1.3 step and should be deferred.

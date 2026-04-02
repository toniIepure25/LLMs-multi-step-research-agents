# v1.5 Mechanism Slate Selection Architecture

> Parent: [PROJECT_DOSSIER.md § Roadmap](../../PROJECT_DOSSIER.md#15-roadmap)
> Frozen historical baseline: [experiments/notes/v0_tier1_eval_set_004.md](../../experiments/notes/v0_tier1_eval_set_004.md)
> Active experimental v1-minimal baseline: [experiments/notes/v1_tier1_eval_set_004.md](../../experiments/notes/v1_tier1_eval_set_004.md)
> Exploratory evidence: [v1_1-grounded-selection-architecture.md](v1_1-grounded-selection-architecture.md) · [v1_2-mechanism-bundling-architecture.md](v1_2-mechanism-bundling-architecture.md) · [v1_3-mechanism-sketching-architecture.md](v1_3-mechanism-sketching-architecture.md) · [v1_4-slot-grounded-drafting-architecture.md](v1_4-slot-grounded-drafting-architecture.md)
> Freeze notes: [../../tasks/handoff/2026-03-21_v1_1_exploratory_freeze.md](../../tasks/handoff/2026-03-21_v1_1_exploratory_freeze.md) · [../../tasks/handoff/2026-03-25_v1_2_exploratory_freeze.md](../../tasks/handoff/2026-03-25_v1_2_exploratory_freeze.md) · [../../tasks/handoff/2026-03-26_v1_3_exploratory_freeze.md](../../tasks/handoff/2026-03-26_v1_3_exploratory_freeze.md) · [../../tasks/handoff/2026-03-31_v1_4_exploratory_freeze.md](../../tasks/handoff/2026-03-31_v1_4_exploratory_freeze.md)
> Build plan: [../../tasks/v1_5_mechanism_slate_selection_plan.md](../../tasks/v1_5_mechanism_slate_selection_plan.md)

This document proposes the next consciously scoped architecture step beyond the
active v1-minimal baseline. It introduces one new capability only:
diversity-constrained mechanism slate selection before final claim wording and
selection.

## Status

- proposed only
- not implemented
- intended as the next architecture-design step after the exploratory v1.1, v1.2, v1.3, and v1.4 freezes

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
- per-claim support pressure alone could not reliably rescue unstable candidate sets

Lesson:

- support-aware selection matters, but it acts too late if the candidate surface
  is already unstable and if final set composition is already poor

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
- but bundling alone is too coarse and rigid to guarantee the best final mechanism set

## 4. What v1.3 taught us

v1.3 explored sketch-first prompting before final claim wording.

What worked:

- mocked checkpoints showed that sketch-first structure can preserve thin-evidence mechanism separation
- the focused live 2008 probe stayed viable, grounded, and utilization-friendly

What failed:

- the live 2008 result did not beat the active v1-minimal baseline on mechanism quality
- explicit OTC-derivatives wording disappeared
- final mechanism choice and phrasing still drifted even when earlier structure existed

Lesson:

- earlier structure helps, but free drafting still allows set-level drift if the
  system is not deciding explicitly which small set of mechanisms it intends to preserve

## 5. What v1.4 taught us

v1.4 explored slot-grounded drafting before final claim selection.

What worked:

- mocked checkpoints showed that grounded slots can preserve thin-evidence mechanism structure
- the focused live 2008 probe was viable, preserved OTC derivatives, and improved evidence utilization materially

What failed:

- groundedness regressed against the active baseline
- one final claim verified as insufficient
- the final set duplicated the housing-finance family instead of preserving a stronger third mechanism
- the live probe also reproduced the recurring artifact-routing / output-dir bug, reinforcing the need to keep the next step compact and easy to inspect

Lesson:

- slot-grounded drafting is closer to the right shape than earlier exploratory branches
- but the remaining bottleneck is now set composition, not just per-claim grounding or wording

## 6. The next bottleneck after v1-minimal and the exploratory branches

The next bottleneck is uncontrolled set composition before final claim wording.

Observed pattern across the active baseline and exploratory branches:

- individual claim candidates can be viable while the final set is still suboptimal
- downstream support scoring helps but is too brittle if the candidate pool already contains duplicated families
- upstream structure helps, but it still leaves the system without an explicit bounded decision about which three mechanism families should survive together
- the system can still spend two final slots on closely related mechanisms while losing a stronger third supported family

In short: the missing piece is not another per-claim signal. The missing piece
is an explicit small set-level composition object that selects a diverse,
supported, target-faithful mechanism slate before final wording.

## 7. Why diversity-constrained slate selection is the right next capability

The next step should introduce one new capability only:

- diversity-constrained mechanism slate selection

This means adding a compact internal `MechanismSlate` representation plus a
deterministic `MechanismSlateSelector` that chooses a bounded set of distinct
mechanism entries before final claim wording.

Each slate entry should carry a grounded structure such as:

- canonical mechanism family label
- target-event anchor
- supporting evidence IDs
- compact grounded rationale
- support sufficiency indicators
- family-duplication / diversity metadata

Why this is more promising than continuing v1.1, v1.2, v1.3, or v1.4 directly:

- it keeps the useful support-awareness lesson from v1.1 without relying on brittle late scoring alone
- it keeps the early-structure lesson from v1.2 without depending on bundling alone to determine the final set
- it keeps the structure-preservation lesson from v1.3 without letting free drafting rediscover the slate implicitly
- it keeps the grounded-slot lesson from v1.4 while explicitly solving the unresolved same-family duplication problem
- it narrows the downstream LLM role:
  - not "choose the best mechanisms again"
  - but "turn this already-selected diverse grounded slate into short direct-causal claims"

Minimality rule:

- keep slates internal to `deliberation` first
- do not introduce a public schema unless implementation pressure proves it is necessary
- do not activate the full `grounding` layer
- do not redesign orchestration

## 8. Proposed data flow

Current v1-minimal:

```text
EvidenceItem[]
  -> candidate claim generation
  -> ClaimSelector
  -> DecisionPacket
  -> EvidenceChecker
```

Proposed v1.5:

```text
EvidenceItem[]
  -> mechanism-family candidate extraction
  -> MechanismSlateSelector
  -> slate-grounded claim drafting
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
  -> candidate mechanism-family structures
  -> diversity-constrained mechanism slate selection
  -> bounded slate-grounded claim drafting
  -> deterministic claim selection
  -> verification
  -> evaluation
  -> ResearchOutput
```

Expected first-pass drafting rule:

- one slate entry should draft at most one short direct-causal claim
- the drafted claim should preserve the slate entry's target-event anchor and supporting evidence IDs
- `ClaimSelector` should remain mostly stable in the first pass

## 9. Expected benefits

Expected gains from this step:

- more reliable preservation of three distinct supported mechanisms when available
- less same-family duplication in the final claim set
- cleaner target-event fidelity because slate entries carry explicit target anchors
- better separation between:
  - which mechanisms should survive together
  - how each surviving mechanism should be phrased
- stronger mocked-test surface:
  - family extraction failure
  - slate-composition failure
  - slate-to-claim drafting failure
  - final selection failure
  become easier to diagnose separately

## 10. Risks

Risks of this step:

- family labels or duplication heuristics may become too rigid and suppress useful nuance
- slate-level optimization could over-prioritize diversity at the expense of support quality
- the slate layer could become a hidden schema expansion if it grows too much
- target-event or family boundaries may still drift if the drafting contract is too loose
- provider timeout sensitivity, limited token budget, and recurring artifact-routing bugs remain operational realities, so the design must keep prompts bounded and evaluation simple

Risk controls:

- keep the slate shape small and internal
- cap slate size tightly
- require explicit supporting evidence IDs and target anchors in every slate entry
- preserve support sufficiency as a hard constraint, not just diversity
- compare directly against [v1_tier1_eval_set_004.md](../../experiments/notes/v1_tier1_eval_set_004.md)
- use mocked regressions before any live probes

## 11. What is explicitly postponed

Still postponed after v1.5:

- full `grounding` layer activation
- `CitationRecord`-heavy citation normalization
- knowledge graphs
- re-planning
- parallel execution
- debate / multi-perspective deliberation
- advanced memory compression
- broad verification redesign
- broad operational hardening beyond narrow bug fixes required to run focused probes

## 12. Acceptance shape for the proposal

This proposal is successful if implementation can remain:

- one new capability only
- mostly inside `deliberation`
- compatible with current v1-minimal orchestration
- testable with mocked regressions before live reruns

Promotion bar:

- focused live probes must show no clear regression versus [v1_tier1_eval_set_004.md](../../experiments/notes/v1_tier1_eval_set_004.md)
- at least one focused question should show a clear structural gain in set composition:
  - less same-family duplication
  - better preservation of a supported third mechanism
  - better target-event fidelity
- the result must be promising enough to justify a first full Tier 1 comparison

If the implementation requires:

- multiple new runtime stages
- protocol churn across the pipeline
- a full grounding subsystem
- broad orchestration changes

then it is no longer the intended v1.5 step and should be deferred.

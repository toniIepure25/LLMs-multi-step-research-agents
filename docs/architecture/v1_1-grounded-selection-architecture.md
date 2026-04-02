# v1.1 Grounded Selection Architecture

> Parent: [PROJECT_DOSSIER.md § Roadmap](../../PROJECT_DOSSIER.md#15-roadmap)
> Frozen historical baseline: [experiments/notes/v0_tier1_eval_set_004.md](../../experiments/notes/v0_tier1_eval_set_004.md)
> Active experimental v1-minimal baseline: [experiments/notes/v1_tier1_eval_set_004.md](../../experiments/notes/v1_tier1_eval_set_004.md)
> Previous step: [v1-minimal-architecture.md](v1-minimal-architecture.md)
> Build plan: [tasks/v1_1_grounded_selection_plan.md](../../tasks/v1_1_grounded_selection_plan.md)

This document records the smallest sensible architectural step that was explored beyond
v1-minimal. It kept the current pipeline shape intact and added one new
capability only: grounding-aware claim scoring through explicit support
attribution before final claim selection.

## Status

- explored in code through a local deterministic `SupportAttributor` plus selector integration
- validated through mocked checkpoints for weak-support filtering and diversity-aware composition
- tested in focused live 2008 probes: [v1_1_2008_probe_001.md](../../experiments/notes/v1_1_2008_probe_001.md), [v1_1_2008_probe_002.md](../../experiments/notes/v1_1_2008_probe_002.md)
- not promoted: live 2008 behavior improved over the first probe but still did not beat the active v1-minimal baseline on groundedness, verification quality, or stable support for the securitization family
- subsequent v1.2 mechanism-bundling exploration also remained exploratory and did not change the active baseline decision
- subsequent v1.3 mechanism-sketching exploration also remained exploratory and did not change the active baseline decision
- subsequent v1.4 slot-grounded drafting exploration also remained exploratory and did not change the active baseline decision
- current status: exploratory branch only, frozen for now, not the active baseline and not the default path forward without a new design decision

## 1. Why v1-minimal is a good stopping point

v1-minimal solved the most important v0 bottleneck without broadening the
pipeline too much.

It added:

- explicit candidate claim generation
- deterministic final claim selection
- better direct-causal answer quality on the highest-value live questions
- a stronger live baseline in [v1_tier1_eval_set_004.md](../../experiments/notes/v1_tier1_eval_set_004.md)

That is enough to stop narrow tuning and treat v1-minimal as a stable baseline
for the next phase.

## 2. The next bottleneck after v1-minimal

The remaining instability is no longer mainly:

- target-event drift
- duplicate suppression
- same-family umbrella collapse

The next bottleneck is weaker support attribution inside deliberation.

Observed pattern across the v1-minimal probe and Tier 1 cycle:

- some claims are selected because they look lexically plausible, not because the
  support evidence is explicitly and cleanly attributed
- support quality and phrasing can still trade off against each other
- evidence utilization can collapse even when groundedness remains acceptable
- mechanism diversity can degrade when several claims implicitly lean on the same
  broad source

In short: v1-minimal improved selection, but it still scores claims with only a
lightweight notion of what evidence most directly grounds each claim.

## 3. Why v1.1 should focus on grounding-aware claim scoring

Grounding-aware claim scoring is the smallest next move because it improves the
quality of the existing selection decision without adding a broad new runtime
stage.

It is the right next step because it can improve:

- support sufficiency
- support-source diversity
- evidence utilization
- claim specificity when support is actually present

while preserving the v1-minimal shape:

- candidate generation stays
- deterministic selection stays
- verification stays separate
- orchestration does not need a redesign

This is intentionally not the full postponed `grounding` phase. It is a narrow
deliberation-side capability that makes claim selection more explicitly aware of
support provenance.

## 4. Minimal new component(s)

The smallest new component is:

- `SupportAttributor`

Responsibilities:

- score how well each candidate claim is grounded by each `EvidenceItem`
- identify the best supporting evidence IDs for each candidate
- estimate support sufficiency for the claim wording
- expose simple deterministic attribution signals to the selector

Expected input:

- `CandidateClaimSet`
- `list[EvidenceItem]`
- optional goal / question text

Expected output:

- an attributed candidate view for selection, for example:
  - candidate claim text
  - top support evidence IDs
  - support strength score
  - event-link score
  - support concentration signal
  - unsupported-specificity signal

Minimality rule:

- start with an internal helper structure first
- do not introduce a broad new schema unless implementation pressure proves it is necessary
- do not turn this into a full `CitationRecord` system yet

## 5. Proposed data flow

v1-minimal:

```text
EvidenceItem[]
  -> candidate claim generation
  -> ClaimSelector
  -> DecisionPacket
  -> EvidenceChecker
```

v1.1 grounded selection:

```text
EvidenceItem[]
  -> candidate claim generation
  -> SupportAttributor
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
  -> support attribution
  -> deterministic claim selection
  -> verification
  -> evaluation
  -> ResearchOutput
```

Selector behavior in v1.1 should rely more on attributed support and less on
raw lexical plausibility alone.

## 6. Expected benefits

Expected gains from this narrow step:

- cleaner distinction between supported and merely plausible candidate claims
- better preservation of distinct mechanism families when support comes from
  different evidence
- fewer cases where 3 claims are technically grounded but effectively depend on
  one broad source
- improved evidence utilization without changing verification
- better debugging surface:
  - candidate generation failure
  - support attribution failure
  - final selection failure
  become easier to separate

## 7. Risks

Risks of this step:

- attribution heuristics may over-favor explicit phrasing and miss indirect but
  real support
- a new helper boundary could add complexity if it grows too large
- overly aggressive concentration penalties could reduce claim count
- if implemented too broadly, this could accidentally turn into a premature
  grounding-layer rewrite

Risk controls:

- keep attribution deterministic first
- keep the helper local to deliberation in v1.1
- preserve v1-minimal external contracts where possible
- compare directly against [v1_tier1_eval_set_004.md](../../experiments/notes/v1_tier1_eval_set_004.md)

## 8. What is explicitly postponed

Still postponed after v1.1:

- full `grounding` layer activation
- `CitationRecord`-heavy citation normalization
- re-planning
- parallel execution
- debate / multi-perspective deliberation
- advanced memory compression
- broad verification redesign
- benchmark-suite expansion as a prerequisite for this step

## 9. Why it was not promoted

What worked:

- mocked tests showed better weak-support-vs-strong-support behavior
- mocked tests showed better diversity-aware composition behavior
- the second focused live 2008 probe improved over the first v1.1 live probe

What failed the promotion bar:

- the first focused live 2008 probe regressed sharply against the active v1-minimal baseline
- the second focused live 2008 probe recovered partway, but still did not match v1-minimal on groundedness or verification quality
- support attribution remained too brittle around the securitization / subprime family to justify promotion

Conclusion:

- v1.1 remains promising as design evidence
- but it is exploratory only and should not replace [v1_tier1_eval_set_004.md](../../experiments/notes/v1_tier1_eval_set_004.md) as the active runtime baseline

## 10. Acceptance shape for the proposal

This proposal is successful if implementation can remain:

- one new capability only
- mostly inside `deliberation`
- compatible with current v1-minimal orchestration
- testable with mocked candidate/evidence sets before live reruns

If the implementation requires:

- multiple new runtime stages
- protocol churn across the whole pipeline
- a full grounding subsystem
- broad orchestration changes

then it is no longer the intended v1.1 step and should be deferred.

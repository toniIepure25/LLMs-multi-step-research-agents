# v1.2 Mechanism Bundling Plan

> Architecture proposal: [docs/architecture/v1_2-mechanism-bundling-architecture.md](../docs/architecture/v1_2-mechanism-bundling-architecture.md)
> Current active baseline: [experiments/notes/v1_tier1_eval_set_004.md](../experiments/notes/v1_tier1_eval_set_004.md)
> Exploratory reference: [tasks/handoff/2026-03-21_v1_1_exploratory_freeze.md](handoff/2026-03-21_v1_1_exploratory_freeze.md)

This plan describes the intended build order for the next step beyond
v1-minimal. It is deliberately small and should be treated as the default
starting point for the next implementation phase.

## Goal

Add deterministic mechanism-oriented evidence bundling before final claim
generation and selection so the live path is less sensitive to:

- token-budget pressure
- candidate-generation variability
- support-attribution brittleness on freeform claim wording
- diversity/completeness collapse under thin evidence slices

without redesigning the broader pipeline.

## Implementation Order

1. Add an internal bundle helper in `deliberation`
   - keep it local first
   - avoid schema changes unless they become necessary

2. Implement deterministic `MechanismBundler`
   - input: `list[EvidenceItem]`, optional goal / question text
   - output: a small ordered bundle set
   - each bundle should include:
     - mechanism-family label
     - member evidence IDs
     - compact merged support text or bundle summary
     - light support diversity signals

3. Teach `SimpleSynthesizer` to generate from bundles instead of the raw flat pool
   - keep the external `deliberate(...)` contract stable
   - preserve direct-causal phrasing expectations
   - keep bundle count small enough for the current live budget

4. Keep `ClaimSelector` mostly stable in the first pass
   - allow it to consume bundled candidates and existing signals
   - avoid a broad selector rewrite unless mocked tests prove it is necessary

5. Add mocked integration coverage before any live rerun
   - 2008 mechanism-retention regression
   - Great Depression diversity/completeness regression
   - dot-com cleanliness preservation

6. Run focused live probes only after mocked coverage passes
   - first 2008
   - then Great Depression
   - then dot-com only if bundling materially changes dot-com candidate composition

7. Run a full Tier 1 comparison only if focused probes are stable

## Dependencies

- current v1-minimal candidate-generation and selection path
- current `DecisionPacket` and verification contracts
- no new provider or orchestration dependency
- v1.1 lessons are reference input only, not a dependency that must be revived

## Acceptance Criteria

Implementation is acceptable if it meets all of the following:

- external v1-minimal pipeline contracts remain stable unless a tiny typed addition is clearly justified
- 2008-style runs are less likely to lose the third mechanism under live-budget pressure
- Great Depression-style runs are less likely to produce 3 claims that all collapse onto one broad evidence source
- dot-com cleanliness is not degraded
- groundedness remains competitive with [v1_tier1_eval_set_004.md](../experiments/notes/v1_tier1_eval_set_004.md)
- evidence utilization becomes at least as stable as the active v1-minimal baseline on focused probes

## First Mocked Tests To Write

1. Bundle construction preserves distinct supported families
   - evidence for two related but distinct mechanisms should not be merged into one bundle too early

2. 2008 bundle retention under thin live-style evidence
   - securitization / subprime-family evidence plus OTC evidence should still yield three viable mechanism bundles or candidates

3. Great Depression bundle diversity
   - stock crash, world-trade collapse, and monetary/banking evidence should survive as distinct bundles when supported

4. Dot-com cleanliness preservation
   - the bundler should not reintroduce wrong-domain crash/vehicle evidence into the final candidate path

5. End-to-end schema compatibility
   - final `DecisionPacket` stays valid and current verification still works

## First Focused Live Probes

1. 2008 financial crisis
   - check whether three mechanisms remain stable under the live budget
   - watch groundedness, verification quality, and securitization-family stability

2. Great Depression
   - check whether three claims remain distinct and supported
   - watch evidence-source concentration and family diversity

3. Dot-com crash
   - only if the bundling change materially affects dot-com generation paths
   - confirm cleanliness and claim completeness remain intact

## Evaluation Plan Against the Active Baseline

Compare the implemented v1.2 step against
[v1_tier1_eval_set_004.md](../experiments/notes/v1_tier1_eval_set_004.md), not
against exploratory v1.1 first.

Primary comparison questions:

- does 2008 retain 3 supported direct-causal claims more stably than v1-minimal under the current live budget?
- does Great Depression retain 3 claims with better mechanism diversity and less source collapse?
- does dot-com remain clean and complete?
- does the new step improve completeness stability without reintroducing broad support-quality regressions?

## Explicit Non-Goals

- full grounding layer
- `CitationRecord` rollout
- debate or multi-perspective reasoning
- re-planning
- parallel orchestration
- verification redesign
- broad benchmark expansion before the first implementation pass

## Recommended First Coding Task

Implement a local `MechanismBundler` helper in `deliberation` plus one mocked 2008 regression showing that thin live-style evidence is bundled into stable mechanism-family slices before final claim generation.

# v1.1 Grounded Selection Plan

> Architecture proposal: [docs/architecture/v1_1-grounded-selection-architecture.md](../docs/architecture/v1_1-grounded-selection-architecture.md)
> Current active baseline: [experiments/notes/v1_tier1_eval_set_004.md](../experiments/notes/v1_tier1_eval_set_004.md)
> Previous phase handoff: [tasks/handoff/2026-03-20_v1_minimal_baseline_freeze.md](handoff/2026-03-20_v1_minimal_baseline_freeze.md)

This plan describes the intended build order for the first step beyond
v1-minimal. It is deliberately small and should be treated as the default
starting point for the next implementation phase.

## Goal

Add grounding-aware support attribution before final claim selection so the
selector can make better choices about:

- support sufficiency
- evidence-source concentration
- mechanism-family diversity
- specificity versus support tradeoffs

without redesigning the broader pipeline.

## Implementation Order

1. Add an internal attributed-candidate helper in `deliberation`
   - keep this local first
   - avoid schema changes unless they become necessary

2. Implement deterministic `SupportAttributor`
   - input: `CandidateClaimSet`, `list[EvidenceItem]`, optional goal
   - output: per-candidate support attribution signals
   - include top support evidence IDs, support strength, event-link strength,
     unsupported-specificity signal, and support-concentration signal

3. Integrate attribution into `ClaimSelector`
   - prefer attributed support over raw lexical plausibility alone
   - use attributed support to improve same-family and diversity decisions
   - preserve current target-fidelity and support-sufficiency protections

4. Keep `SimpleSynthesizer.deliberate(...)` externally stable
   - generation -> attribution -> selection -> `DecisionPacket`
   - no orchestration redesign

5. Add mocked integration coverage before any live rerun
   - 2008 support attribution regression
   - Great Depression diversity regression
   - dot-com completeness preservation

6. Run focused live probes only after mocked coverage passes
   - first 2008
   - then Great Depression
   - then dot-com only if attribution logic touches dot-com behavior materially

7. Run a full Tier 1 comparison only if focused probes are stable

## Dependencies

- current v1-minimal candidate generation contract
- current `ClaimSelector` deterministic scoring path
- current `DecisionPacket` and verification contracts
- no new provider or orchestration dependency

## Acceptance Criteria

Implementation is acceptable if it meets all of the following:

- external v1-minimal pipeline contracts remain stable unless a tiny typed
  addition is clearly justified
- selector decisions become explainable in terms of attributed support
- 2008-style claims are less likely to survive on weak or diffuse support
- Great Depression-style final sets are less likely to collapse onto one broad
  support source when distinct supported families exist
- dot-com cleanliness is not degraded
- groundedness remains competitive with [v1_tier1_eval_set_004.md](../experiments/notes/v1_tier1_eval_set_004.md)

## First Tests To Write

1. Attributed support beats lexical plausibility
   - a cleaner but weakly attributed claim should lose to a slightly broader but
     clearly supported claim

2. Diverse support beats same-source stacking
   - three claims can be produced from one broad source, but only two should
     survive if a third distinct-family candidate has stronger fresh support

3. Exact target-event fidelity still holds
   - alternate-target claims should still lose when exact-target candidates are
     comparably supported

4. Same-family suppression still holds
   - broad umbrella claims should still lose to sharper attributed same-family
     claims

5. End-to-end schema compatibility
   - final `DecisionPacket` stays valid and current verification still works

## Evaluation Plan Against the Active Baseline

Compare the implemented v1.1 step against
[v1_tier1_eval_set_004.md](../experiments/notes/v1_tier1_eval_set_004.md), not
against older intermediate probes first.

Primary comparison questions:

- does 2008 retain 3 supported claims with cleaner support attribution
  explanations?
- does Great Depression retain 3 claims with less evidence-source collapse?
- does dot-com remain clean and complete?
- does evidence utilization improve or at least stop collapsing on broad-source
  cases?

## Explicit Non-Goals

- full grounding layer
- citation graph or knowledge graph work
- debate or multi-perspective reasoning
- re-planning
- parallel orchestration
- verification redesign
- broad benchmark expansion before the first implementation pass

## Recommended First Coding Task

Implement a local `SupportAttributor` helper plus one mocked regression test for
2008 candidate support attribution, with no orchestration changes.
